from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum, uuid

class Base(DeclarativeBase): pass
class Role(str, enum.Enum):
    ADMIN="ADMIN"; SENIOR_CLINICIAN="SENIOR_CLINICIAN"; CLINICIAN="CLINICIAN"; VIEWER="VIEWER"
def now_utc(): return datetime.now(timezone.utc)
class Ward(Base):
    __tablename__="ward"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    name: Mapped[str]=mapped_column(String(80), unique=True)
class AppUser(Base):
    __tablename__="app_user"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    username: Mapped[str]=mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str]=mapped_column(String(255))
    role: Mapped[Role]=mapped_column(Enum(Role, name="user_role"))
    active: Mapped[bool]=mapped_column(Boolean, default=True)
    failed_logins: Mapped[int]=mapped_column(Integer, default=0)
    locked_until: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
class UserWard(Base):
    __tablename__="user_ward"
    user_id: Mapped[str]=mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"), primary_key=True)
    ward_id: Mapped[str]=mapped_column(ForeignKey("ward.id", ondelete="CASCADE"), primary_key=True)
class Session(Base):
    __tablename__="session"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    token_hash: Mapped[str]=mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[str]=mapped_column(ForeignKey("app_user.id", ondelete="CASCADE"))
    csrf_hash: Mapped[str]=mapped_column(String(64))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc)
    last_seen_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc)
    expires_at: Mapped[datetime]=mapped_column(DateTime(timezone=True))
class ApiKey(Base):
    __tablename__="api_key"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    key_hash: Mapped[str]=mapped_column(String(64), unique=True)
    scope: Mapped[str]=mapped_column(String(40), default="ingest:write")
class SystemConfig(Base):
    __tablename__="system_config"
    key: Mapped[str]=mapped_column(String(100), primary_key=True)
    value: Mapped[str]=mapped_column(String(500))
class AuditLog(Base):
    __tablename__="audit_log"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    actor_id: Mapped[str|None]=mapped_column(String(36), nullable=True)
    action: Mapped[str]=mapped_column(String(100))
    object_type: Mapped[str]=mapped_column(String(60))
    object_id: Mapped[str|None]=mapped_column(String(36), nullable=True)
    request_id: Mapped[str]=mapped_column(String(36))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=now_utc, index=True)
