from alembic import op
import sqlalchemy as sa

revision = "0002_clinical_core"
down_revision = "0001_security_spine"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "patient",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_identifier", sa.String(16), nullable=False, unique=True),
        sa.Column("age_years", sa.Integer(), nullable=False),
        sa.Column("sex", sa.String(20), nullable=False),
        sa.CheckConstraint("age_years BETWEEN 0 AND 120", name="ck_patient_age_range"),
        sa.CheckConstraint("patient_identifier ~ '^SIM-[0-9]{6}$'", name="ck_patient_synthetic_identifier"),
    )
    op.create_index("ix_patient_patient_identifier", "patient", ["patient_identifier"])
    op.create_table(
        "admission",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("patient_id", sa.String(36), sa.ForeignKey("patient.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ward_id", sa.String(36), sa.ForeignKey("ward.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("bed_label", sa.String(40), nullable=False),
        sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discharged_at", sa.DateTime(timezone=True)),
        sa.Column("spo2_scale", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.CheckConstraint("spo2_scale IN (1, 2)", name="ck_admission_spo2_scale"),
        sa.CheckConstraint("status IN ('ACTIVE', 'DISCHARGED')", name="ck_admission_status"),
        sa.CheckConstraint("discharged_at IS NULL OR discharged_at >= admitted_at", name="ck_admission_dates"),
    )
    op.create_index("ix_admission_patient_id", "admission", ["patient_id"])
    op.create_index("ix_admission_ward_status", "admission", ["ward_id", "status"])
    op.create_table(
        "observation",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admission_id", sa.String(36), sa.ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("respiration_rate", sa.Integer()), sa.Column("spo2", sa.Integer()),
        sa.Column("supplemental_o2", sa.Boolean()), sa.Column("systolic_bp", sa.Integer()),
        sa.Column("pulse", sa.Integer()), sa.Column("consciousness", sa.String(20)),
        sa.Column("temperature", sa.Numeric(3, 1)),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("source_record_id", sa.String(120), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("entered_by", sa.String(36), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(20), nullable=False, server_default="VALID"),
        sa.Column("payload_hash", sa.String(64), nullable=False),
        sa.UniqueConstraint("admission_id", "measured_at", "source", "source_record_id", name="uq_observation_idempotency"),
        sa.CheckConstraint("respiration_rate IS NULL OR respiration_rate BETWEEN 1 AND 100", name="ck_observation_rr"),
        sa.CheckConstraint("spo2 IS NULL OR spo2 BETWEEN 50 AND 100", name="ck_observation_spo2"),
        sa.CheckConstraint("systolic_bp IS NULL OR systolic_bp BETWEEN 30 AND 300", name="ck_observation_sbp"),
        sa.CheckConstraint("pulse IS NULL OR pulse BETWEEN 20 AND 300", name="ck_observation_pulse"),
        sa.CheckConstraint("temperature IS NULL OR temperature BETWEEN 25 AND 45", name="ck_observation_temperature"),
        sa.CheckConstraint("consciousness IS NULL OR consciousness IN ('ALERT', 'NEW_CONFUSION', 'VOICE', 'PAIN', 'UNRESPONSIVE')", name="ck_observation_consciousness"),
        sa.CheckConstraint("respiration_rate IS NOT NULL OR spo2 IS NOT NULL OR supplemental_o2 IS NOT NULL OR systolic_bp IS NOT NULL OR pulse IS NOT NULL OR consciousness IS NOT NULL OR temperature IS NOT NULL", name="ck_observation_has_value"),
    )
    op.create_index("ix_observation_admission_measured", "observation", ["admission_id", sa.text("measured_at DESC")])
    op.create_table(
        "ingestion_rejection",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admission_id", sa.String(36)),
        sa.Column("reason_code", sa.String(40), nullable=False),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("reason_code IN ('HARD_RANGE', 'FUTURE_TIMESTAMP', 'INVALID_PRECISION', 'INVALID_VALUE', 'IDEMPOTENCY_CONFLICT')", name="ck_ingestion_rejection_reason"),
    )
    op.create_index("ix_ingestion_rejection_received_at", "ingestion_rejection", ["received_at"])
    op.create_table(
        "lab_result",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admission_id", sa.String(36), sa.ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("test_code", sa.String(40), nullable=False), sa.Column("value", sa.String(80), nullable=False),
        sa.Column("unit", sa.String(30), nullable=False), sa.Column("measured_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_lab_result_admission_id", "lab_result", ["admission_id"])
    op.create_table(
        "risk_assessment",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admission_id", sa.String(36), sa.ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("scoring_version", sa.String(40), nullable=False), sa.Column("observation_ids", sa.JSON(), nullable=False),
        sa.Column("spo2_scale", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("per_parameter_scores", sa.JSON(), nullable=False), sa.Column("completeness", sa.Integer(), nullable=False),
        sa.Column("level", sa.String(20), nullable=False), sa.Column("total", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False), sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("completeness BETWEEN 0 AND 7", name="ck_risk_assessment_completeness"),
        sa.CheckConstraint("total >= 0", name="ck_risk_assessment_total"),
    )
    op.create_index("ix_risk_assessment_admission_computed", "risk_assessment", ["admission_id", "computed_at"])


def downgrade():
    for name in ("risk_assessment", "lab_result", "ingestion_rejection", "observation", "admission", "patient"):
        op.drop_table(name)
