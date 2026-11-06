import hashlib, secrets, uuid
from collections import defaultdict, deque
from time import monotonic
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session as DBSession
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError
from app.core.config import settings
from app.core.db import get_db
from app.models.base import AppUser, AuditLog, Role, Session
router=APIRouter(prefix="/api/v1/auth", tags=["authentication"])
hasher=PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
_attempts=defaultdict(deque)
def digest(v:str)->str: return hashlib.sha256(v.encode()).hexdigest()
def utcnow(): return datetime.now(timezone.utc)
class LoginIn(BaseModel): model_config=ConfigDict(extra="forbid"); username:str=Field(min_length=1,max_length=120); password:str=Field(min_length=1,max_length=256)
class PasswordIn(BaseModel): model_config=ConfigDict(extra="forbid"); current_password:str; new_password:str=Field(min_length=12,max_length=256)
def current_session(request:Request, db:DBSession=Depends(get_db)):
    raw=request.cookies.get("g_one_session")
    if not raw: raise HTTPException(401,"Authentication required")
    session=db.query(Session).filter_by(token_hash=digest(raw)).first(); now=utcnow()
    if not session or session.expires_at <= now or session.last_seen_at <= now-timedelta(minutes=settings.session_idle_minutes):
        if session: db.delete(session); db.commit()
        raise HTTPException(401,"Session expired")
    user=db.get(AppUser,session.user_id)
    if not user or not user.active: raise HTTPException(401,"Authentication required")
    if request.method not in ("GET","HEAD","OPTIONS"):
        csrf=request.headers.get("X-CSRF-Token","")
        if not secrets.compare_digest(digest(csrf),session.csrf_hash): raise HTTPException(403,"CSRF validation failed")
    session.last_seen_at=now; db.commit(); request.state.user=user; request.state.session=session
    return user
def require_roles(*allowed:Role):
    def check(user:AppUser=Depends(current_session)):
        if user.role not in allowed: raise HTTPException(403,"Access denied")
        return user
    return check
@router.get("/csrf")
def csrf(response:Response):
    token=secrets.token_urlsafe(32)
    response.set_cookie("g_one_pre_csrf",token,httponly=False,secure=(settings.environment != "development" or settings.cookie_secure),samesite="lax",max_age=600,path="/")
    return {"csrf_token":token}
@router.post("/login")
def login(data:LoginIn, request:Request, response:Response, db:DBSession=Depends(get_db)):
    pre_cookie=request.cookies.get("g_one_pre_csrf",""); pre_header=request.headers.get("X-CSRF-Token","")
    if not pre_cookie or not secrets.compare_digest(pre_cookie,pre_header): raise HTTPException(403,"CSRF validation failed")
    now_m=monotonic(); address=request.client.host if request.client else "unknown"; attempts=_attempts[address]
    while attempts and now_m-attempts[0]>60: attempts.popleft()
    if len(attempts)>=20: raise HTTPException(429,"Too many attempts. Try again later")
    attempts.append(now_m)
    user=db.query(AppUser).filter_by(username=data.username).first(); now=utcnow(); valid=False
    if user and user.active and user.locked_until and user.locked_until > now: raise HTTPException(423,"Account temporarily locked. Try again later")
    if user and user.active and (not user.locked_until or user.locked_until <= now):
        try: valid=hasher.verify(user.password_hash,data.password)
        except (VerifyMismatchError,InvalidHashError): valid=False
    if not valid:
        if user and user.active:
            user.failed_logins += 1
            if user.failed_logins >= settings.login_max_failures:
                user.locked_until=now+timedelta(minutes=settings.login_lock_minutes); user.failed_logins=0
            db.commit()
        raise HTTPException(401,"Unable to sign in with those credentials")
    user.failed_logins=0; user.locked_until=None; raw=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
    s=Session(token_hash=digest(raw),csrf_hash=digest(csrf),user_id=user.id,created_at=now,last_seen_at=now,expires_at=now+timedelta(hours=settings.session_absolute_hours))
    db.add(s); db.flush(); db.add(AuditLog(actor_id=user.id,action="auth.login",object_type="session",object_id=s.id,request_id=getattr(request.state,"request_id","unknown"))); db.commit()
    response.set_cookie("g_one_session",raw,httponly=True,secure=(settings.environment != "development" or settings.cookie_secure),samesite="lax",max_age=settings.session_absolute_hours*3600,path="/")
    response.set_cookie("g_one_csrf",csrf,httponly=False,secure=(settings.environment != "development" or settings.cookie_secure),samesite="lax",max_age=settings.session_absolute_hours*3600,path="/")
    response.delete_cookie("g_one_pre_csrf",path="/")
    return {"id":user.id,"username":user.username,"role":user.role.value,"csrf_token":csrf}
@router.get("/me")
def me(request:Request,user:AppUser=Depends(current_session)):
    return {"id":user.id,"username":user.username,"role":user.role.value,"csrf_token":request.cookies.get("g_one_csrf","")}
@router.post("/logout")
def logout(request:Request,response:Response,user:AppUser=Depends(current_session),db:DBSession=Depends(get_db)):
    s=request.state.session; db.add(AuditLog(actor_id=user.id,action="auth.logout",object_type="session",object_id=s.id,request_id=request.state.request_id)); db.delete(s); db.commit()
    response.delete_cookie("g_one_session",path="/"); response.delete_cookie("g_one_csrf",path="/"); return {"ok":True}
@router.post("/password")
def change_password(data:PasswordIn,user:AppUser=Depends(current_session),db:DBSession=Depends(get_db)):
    try: ok=hasher.verify(user.password_hash,data.current_password)
    except (VerifyMismatchError,InvalidHashError): ok=False
    if not ok: raise HTTPException(400,"Current password is incorrect")
    user.password_hash=hasher.hash(data.new_password); db.commit(); return {"ok":True}
