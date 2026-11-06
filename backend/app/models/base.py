from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, JSON, Numeric, String, UniqueConstraint, text
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

class Patient(Base):
    __tablename__="patient"
    __table_args__=(
        CheckConstraint("age_years BETWEEN 0 AND 120", name="ck_patient_age_range"),
        CheckConstraint("patient_identifier ~ '^SIM-[0-9]{6}$'", name="ck_patient_synthetic_identifier"),
    )
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    patient_identifier: Mapped[str]=mapped_column(String(16), unique=True, nullable=False, index=True)
    age_years: Mapped[int]=mapped_column(Integer, nullable=False)
    sex: Mapped[str]=mapped_column(String(20), nullable=False)
    is_simulated: Mapped[bool]=mapped_column(Boolean, nullable=False, default=False)

class Admission(Base):
    __tablename__="admission"
    __table_args__=(
        CheckConstraint("spo2_scale IN (1, 2)", name="ck_admission_spo2_scale"),
        CheckConstraint("status IN ('ACTIVE', 'DISCHARGED')", name="ck_admission_status"),
        CheckConstraint("discharged_at IS NULL OR discharged_at >= admitted_at", name="ck_admission_dates"),
        CheckConstraint("simulation_scenario IS NULL OR simulation_scenario IN ('stable', 'gradual_deterioration', 'sudden_concerning_change', 'missing_observations', 'sensor_disconnection', 'data_quality_problems')", name="ck_admission_simulation_scenario"),
        Index("ix_admission_ward_status", "ward_id", "status"),
    )
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    patient_id: Mapped[str]=mapped_column(ForeignKey("patient.id", ondelete="RESTRICT"), nullable=False, index=True)
    ward_id: Mapped[str]=mapped_column(ForeignKey("ward.id", ondelete="RESTRICT"), nullable=False)
    bed_label: Mapped[str]=mapped_column(String(40), nullable=False)
    admitted_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)
    discharged_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    spo2_scale: Mapped[int]=mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str]=mapped_column(String(20), nullable=False, default="ACTIVE")
    is_simulated: Mapped[bool]=mapped_column(Boolean, nullable=False, default=False)
    simulation_scenario: Mapped[str|None]=mapped_column(String(40), nullable=True)

class Observation(Base):
    __tablename__="observation"
    __table_args__=(
        UniqueConstraint("admission_id", "measured_at", "source", "source_record_id", name="uq_observation_idempotency"),
        CheckConstraint("respiration_rate IS NULL OR respiration_rate BETWEEN 1 AND 100", name="ck_observation_rr"),
        CheckConstraint("spo2 IS NULL OR spo2 BETWEEN 50 AND 100", name="ck_observation_spo2"),
        CheckConstraint("systolic_bp IS NULL OR systolic_bp BETWEEN 30 AND 300", name="ck_observation_sbp"),
        CheckConstraint("pulse IS NULL OR pulse BETWEEN 20 AND 300", name="ck_observation_pulse"),
        CheckConstraint("temperature IS NULL OR temperature BETWEEN 25 AND 45", name="ck_observation_temperature"),
        CheckConstraint("consciousness IS NULL OR consciousness IN ('ALERT', 'NEW_CONFUSION', 'VOICE', 'PAIN', 'UNRESPONSIVE')", name="ck_observation_consciousness"),
        CheckConstraint("respiration_rate IS NOT NULL OR spo2 IS NOT NULL OR supplemental_o2 IS NOT NULL OR systolic_bp IS NOT NULL OR pulse IS NOT NULL OR consciousness IS NOT NULL OR temperature IS NOT NULL", name="ck_observation_has_value"),
        Index("ix_observation_admission_measured", "admission_id", text("measured_at DESC")),
    )
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    admission_id: Mapped[str]=mapped_column(ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False)
    measured_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    respiration_rate: Mapped[int|None]=mapped_column(Integer, nullable=True)
    spo2: Mapped[int|None]=mapped_column(Integer, nullable=True)
    supplemental_o2: Mapped[bool|None]=mapped_column(Boolean, nullable=True)
    systolic_bp: Mapped[int|None]=mapped_column(Integer, nullable=True)
    pulse: Mapped[int|None]=mapped_column(Integer, nullable=True)
    consciousness: Mapped[str|None]=mapped_column(String(20), nullable=True)
    temperature: Mapped[float|None]=mapped_column(Numeric(3,1), nullable=True)
    source: Mapped[str]=mapped_column(String(40), nullable=False)
    source_record_id: Mapped[str]=mapped_column(String(120), nullable=False)
    is_simulated: Mapped[bool]=mapped_column(Boolean, nullable=False, default=False)
    entered_by: Mapped[str|None]=mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str]=mapped_column(String(20), nullable=False, default="VALID")
    payload_hash: Mapped[str]=mapped_column(String(64), nullable=False)

class IngestionRejection(Base):
    __tablename__="ingestion_rejection"
    __table_args__=(CheckConstraint("reason_code IN ('HARD_RANGE', 'FUTURE_TIMESTAMP', 'INVALID_PRECISION', 'INVALID_VALUE', 'IDEMPOTENCY_CONFLICT')", name="ck_ingestion_rejection_reason"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    admission_id: Mapped[str|None]=mapped_column(String(36), nullable=True)
    reason_code: Mapped[str]=mapped_column(String(40), nullable=False)
    source: Mapped[str]=mapped_column(String(40), nullable=False)
    received_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, default=now_utc, index=True)

class LabResult(Base):
    __tablename__="lab_result"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    admission_id: Mapped[str]=mapped_column(ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False, index=True)
    test_code: Mapped[str]=mapped_column(String(40), nullable=False)
    value: Mapped[str]=mapped_column(String(80), nullable=False)
    unit: Mapped[str]=mapped_column(String(30), nullable=False)
    measured_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)
    is_simulated: Mapped[bool]=mapped_column(Boolean, nullable=False, default=True)

class RiskAssessment(Base):
    __tablename__="risk_assessment"
    __table_args__=(CheckConstraint("completeness BETWEEN 0 AND 7", name="ck_risk_assessment_completeness"), CheckConstraint("total >= 0", name="ck_risk_assessment_total"), Index("ix_risk_assessment_admission_computed", "admission_id", "computed_at"))
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    admission_id: Mapped[str]=mapped_column(ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False)
    scoring_version: Mapped[str]=mapped_column(String(40), nullable=False)
    spo2_scale: Mapped[int]=mapped_column(Integer, nullable=False, default=1)
    observation_ids: Mapped[list]=mapped_column(JSON, nullable=False)
    per_parameter_scores: Mapped[dict]=mapped_column(JSON, nullable=False)
    completeness: Mapped[int]=mapped_column(Integer, nullable=False)
    level: Mapped[str]=mapped_column(String(20), nullable=False)
    total: Mapped[int]=mapped_column(Integer, nullable=False)
    explanation: Mapped[dict]=mapped_column(JSON, nullable=False)
    computed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)

class Alert(Base):
    __tablename__="alert"
    __table_args__=(
        CheckConstraint("status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')", name="ck_alert_status"),
        CheckConstraint("level IN ('LOW_MEDIUM', 'MEDIUM', 'HIGH')", name="ck_alert_level"),
        Index("uq_alert_one_open_per_admission", "admission_id", unique=True, postgresql_where=text("status IN ('OPEN', 'ACKNOWLEDGED')")),
        Index("ix_alert_status_level_created", "status", "level", "created_at"),
    )
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    admission_id: Mapped[str]=mapped_column(ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str]=mapped_column(String(20), nullable=False, default="OPEN")
    level: Mapped[str]=mapped_column(String(20), nullable=False)
    latest_assessment_id: Mapped[str]=mapped_column(ForeignKey("risk_assessment.id", ondelete="RESTRICT"), nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False, default=now_utc)
    acknowledged_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[str|None]=mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by: Mapped[str|None]=mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True)
    consecutive_lower: Mapped[int]=mapped_column(Integer, nullable=False, default=0)
    score_returned_to_low: Mapped[bool]=mapped_column(Boolean, nullable=False, default=False)
    last_score_level: Mapped[str]=mapped_column(String(20), nullable=False)

class AlertEvent(Base):
    __tablename__="alert_event"
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    alert_id: Mapped[str]=mapped_column(ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False, index=True)
    actor_id: Mapped[str|None]=mapped_column(ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True)
    event_type: Mapped[str]=mapped_column(String(40), nullable=False)
    from_level: Mapped[str|None]=mapped_column(String(20), nullable=True)
    to_level: Mapped[str|None]=mapped_column(String(20), nullable=True)
    detail_code: Mapped[str|None]=mapped_column(String(60), nullable=True)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)

class ClinicalResponse(Base):
    __tablename__="clinical_response"
    __table_args__=(CheckConstraint("length(notes) <= 500", name="ck_clinical_response_notes_length"), CheckConstraint("action IN ('CLINICAL_REVIEW', 'OBSERVATIONS_REPEATED', 'LOCAL_ESCALATION', 'OTHER')", name="ck_clinical_response_action"))
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    alert_id: Mapped[str]=mapped_column(ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False, index=True)
    assessed_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str]=mapped_column(String(40), nullable=False)
    escalated_to_role: Mapped[str|None]=mapped_column(String(40), nullable=True)
    notes: Mapped[str|None]=mapped_column(String(500), nullable=True)
    actor_id: Mapped[str]=mapped_column(ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False)

class Escalation(Base):
    __tablename__="escalation"
    __table_args__=(UniqueConstraint("alert_id", name="uq_escalation_alert"), CheckConstraint("target_role = 'SENIOR_CLINICIAN'", name="ck_escalation_target_role"))
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    alert_id: Mapped[str]=mapped_column(ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False)
    ward_id: Mapped[str]=mapped_column(ForeignKey("ward.id", ondelete="RESTRICT"), nullable=False)
    target_role: Mapped[str]=mapped_column(String(40), nullable=False, default="SENIOR_CLINICIAN")
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)

class DataSourceStatus(Base):
    __tablename__="data_source_status"
    __table_args__=(UniqueConstraint("source", name="uq_data_source_status_source"),)
    id: Mapped[str]=mapped_column(String(36), primary_key=True, default=lambda:str(uuid.uuid4()))
    source: Mapped[str]=mapped_column(String(40), nullable=False)
    ward_id: Mapped[str|None]=mapped_column(ForeignKey("ward.id", ondelete="CASCADE"), nullable=True)
    connected: Mapped[bool]=mapped_column(Boolean, nullable=False)
    is_simulated: Mapped[bool]=mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), nullable=False)
    status_code: Mapped[str]=mapped_column(String(40), nullable=False)
