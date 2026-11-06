from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession
from argon2 import PasswordHasher
from app.api.auth import require_roles
from app.core.db import get_db, engine
from app.models.base import Admission, Alert, AppUser, AuditLog, DataSourceStatus, Observation, Role, Session, SystemConfig, UserWard, Ward
from app.services.alerts import ensure_escalations

router = APIRouter(prefix="/api/v1/admin", tags=["administration"])
admin_only = require_roles(Role.ADMIN)
hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)

class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=3, max_length=120, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=12, max_length=256)
    role: Role
    ward_ids: list[str] = Field(default_factory=list, max_length=50)
    @model_validator(mode="after")
    def ward_rules(self):
        if self.role is not Role.ADMIN and not self.ward_ids:
            raise ValueError("Clinical and viewer users require at least one ward")
        if len(set(self.ward_ids)) != len(self.ward_ids):
            raise ValueError("Ward assignments must be unique")
        return self

class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: bool
    ward_ids: list[str] = Field(default_factory=list, max_length=50)

class AdvanceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    minutes: int = Field(ge=1, le=1440)

class ResetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seed: int = Field(default=42, ge=0, le=2_147_483_647)


def _user_payload(db: DBSession, user: AppUser):
    ward_ids = db.scalars(select(UserWard.ward_id).where(UserWard.user_id == user.id)).all()
    return {"id": user.id, "username": user.username, "role": user.role.value, "active": user.active, "ward_ids": ward_ids}


def _assign_wards(db: DBSession, user: AppUser, ward_ids: list[str]):
    if user.role is Role.ADMIN and ward_ids:
        raise HTTPException(422, "Administrators cannot be assigned clinical wards")
    if user.role is not Role.ADMIN and not ward_ids:
        raise HTTPException(422, "Clinical and viewer users require at least one ward")
    wards = set(db.scalars(select(Ward.id).where(Ward.id.in_(ward_ids))).all()) if ward_ids else set()
    if wards != set(ward_ids):
        raise HTTPException(422, "One or more wards do not exist")
    db.query(UserWard).filter_by(user_id=user.id).delete(synchronize_session=False)
    db.add_all([UserWard(user_id=user.id, ward_id=ward_id) for ward_id in ward_ids])


def _audit(request: Request, db: DBSession, user: AppUser, action: str, object_type: str, object_id: str | None):
    db.add(AuditLog(actor_id=user.id, action=action, object_type=object_type, object_id=object_id, request_id=request.state.request_id, created_at=datetime.now(timezone.utc)))


@router.get("/users")
def list_users(request: Request, user: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    rows = db.scalars(select(AppUser).order_by(AppUser.username)).all()
    return {"items": [_user_payload(db, row) for row in rows]}


@router.post("/users", status_code=201)
def create_user(body: UserCreate, request: Request, actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    if db.scalar(select(AppUser.id).where(AppUser.username == body.username)):
        raise HTTPException(409, "Username is already in use")
    user = AppUser(username=body.username, password_hash=hasher.hash(body.password), role=body.role, active=True)
    db.add(user)
    db.flush()
    _assign_wards(db, user, body.ward_ids)
    _audit(request, db, actor, "admin.user_created", "user", user.id)
    db.commit()
    return _user_payload(db, user)


@router.put("/users/{user_id}")
def update_user(user_id: str, body: UserUpdate, request: Request, actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    user = db.get(AppUser, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    _assign_wards(db, user, body.ward_ids)
    user.active = body.active
    if not user.active:
        db.query(Session).filter_by(user_id=user.id).delete(synchronize_session=False)
    _audit(request, db, actor, "admin.user_updated", "user", user.id)
    db.commit()
    return _user_payload(db, user)


@router.get("/status")
def system_status(request: Request, actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    with engine.connect() as connection:
        connection.execute(select(1))
    _audit(request, db, actor, "admin.status_read", "system", None)
    db.commit()
    try:
        from app.services.model_registry import InvalidModelArtifact, load_verified_active
        active_model = load_verified_active()
        model_status = f"{active_model['manifest']['model_id']} · {active_model['manifest']['version']}" if active_model else "No trained ML model is deployed"
    except InvalidModelArtifact:
        model_status = "Active model artifact failed integrity checks"
    return {
        "database": "connected",
        "users": db.scalar(select(func.count()).select_from(AppUser)),
        "active_admissions": db.scalar(select(func.count()).select_from(Admission).where(Admission.status == "ACTIVE")),
        "open_alerts": db.scalar(select(func.count()).select_from(Alert).where(Alert.status.in_(("OPEN", "ACKNOWLEDGED")))),
        "observations": db.scalar(select(func.count()).select_from(Observation)),
        "data_sources": [{"source": row.source, "connected": row.connected, "status": row.status_code, "updated_at": row.updated_at} for row in db.scalars(select(DataSourceStatus).order_by(DataSourceStatus.source)).all()],
        "model": model_status,
    }


@router.get("/audit")
def audit_events(request: Request, limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0), action: str | None = Query(None, min_length=1, max_length=100), actor_id: str | None = Query(None, max_length=36), actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    total_query = select(func.count()).select_from(query.subquery())
    total = db.scalar(total_query) or 0
    rows = db.scalars(query.order_by(AuditLog.created_at.desc(), AuditLog.id).limit(limit).offset(offset)).all()
    names = {item.id: item.username for item in db.scalars(select(AppUser).where(AppUser.id.in_({row.actor_id for row in rows if row.actor_id}))).all()} if rows else {}
    _audit(request, db, actor, "admin.audit_read", "audit_log", None)
    db.commit()
    return {"items": [{"id": row.id, "actor_id": row.actor_id, "actor_username": names.get(row.actor_id), "action": row.action, "object_type": row.object_type, "object_id": row.object_id, "request_id": row.request_id, "created_at": row.created_at} for row in rows], "limit": limit, "offset": offset, "total": total}


@router.get("/wards")
def list_wards(actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    return {"items": [{"id": row.id, "name": row.name} for row in db.scalars(select(Ward).order_by(Ward.name)).all()]}


@router.post("/simulator/reset")
def reset_simulator(body: ResetInput, request: Request, actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    from simulator.engine import run_seed
    result = run_seed(db, body.seed)
    if hasattr(request.app.state.clock, "refresh_assessments"):
        request.app.state.clock.refresh_assessments = False
    _audit(request, db, actor, "admin.simulator_reset", "simulator", str(body.seed))
    db.commit()
    return {"seed": result["seed"], "patients": result["patients"], "wards": result["wards"], "scenarios": result["scenarios"], "output_sha256": result["output_sha256"]}
@router.get("/clock")
def clock_status(request: Request, actor: AppUser = Depends(require_roles(Role.ADMIN, Role.SENIOR_CLINICIAN, Role.CLINICIAN, Role.VIEWER))):
    clock = request.app.state.clock
    return {"simulated": hasattr(clock, "advance"), "current_time": clock.now()}


@router.post("/simulator/advance")
def advance_simulator(body: AdvanceInput, request: Request, actor: AppUser = Depends(admin_only), db: DBSession = Depends(get_db)):
    clock = request.app.state.clock
    if not hasattr(clock, "advance"):
        raise HTTPException(409, "Reset the simulator before advancing its clock")
    current = clock.advance(minutes=body.minutes)
    clock.refresh_assessments = True
    ensure_escalations(db, current)
    _audit(request, db, actor, "admin.simulator_advanced", "simulator", str(body.minutes))
    db.commit()
    return {"current_time": current}
