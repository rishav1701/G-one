from alembic import op
import sqlalchemy as sa

revision = "0003_alerts_simulation"
down_revision = "0002_clinical_core"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("patient", sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("admission", sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("admission", sa.Column("simulation_scenario", sa.String(40)))
    op.create_check_constraint("ck_admission_simulation_scenario", "admission", "simulation_scenario IS NULL OR simulation_scenario IN ('stable', 'gradual_deterioration', 'sudden_concerning_change', 'missing_observations', 'sensor_disconnection', 'data_quality_problems')")
    op.create_table(
        "alert",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("admission_id", sa.String(36), sa.ForeignKey("admission.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("level", sa.String(20), nullable=False),
        sa.Column("latest_assessment_id", sa.String(36), sa.ForeignKey("risk_assessment.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True)),
        sa.Column("acknowledged_by", sa.String(36), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("resolved_at", sa.DateTime(timezone=True)),
        sa.Column("resolved_by", sa.String(36), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("consecutive_lower", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("score_returned_to_low", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("last_score_level", sa.String(20), nullable=False),
        sa.CheckConstraint("status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')", name="ck_alert_status"),
        sa.CheckConstraint("level IN ('LOW_MEDIUM', 'MEDIUM', 'HIGH')", name="ck_alert_level"),
    )
    op.create_index("ix_alert_admission_id", "alert", ["admission_id"])
    op.create_index("ix_alert_latest_assessment_id", "alert", ["latest_assessment_id"])
    op.create_index("uq_alert_one_open_per_admission", "alert", ["admission_id"], unique=True, postgresql_where=sa.text("status IN ('OPEN', 'ACKNOWLEDGED')"))
    op.create_index("ix_alert_status_level_created", "alert", ["status", "level", "created_at"])
    op.create_table(
        "alert_event",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("app_user.id", ondelete="SET NULL")),
        sa.Column("event_type", sa.String(40), nullable=False), sa.Column("from_level", sa.String(20)),
        sa.Column("to_level", sa.String(20)), sa.Column("detail_code", sa.String(60)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_alert_event_alert_id", "alert_event", ["alert_id"])
    op.create_table(
        "clinical_response",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("action", sa.String(40), nullable=False),
        sa.Column("escalated_to_role", sa.String(40)), sa.Column("notes", sa.String(500)),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("app_user.id", ondelete="RESTRICT"), nullable=False),
        sa.CheckConstraint("length(notes) <= 500", name="ck_clinical_response_notes_length"),
        sa.CheckConstraint("action IN ('CLINICAL_REVIEW', 'OBSERVATIONS_REPEATED', 'LOCAL_ESCALATION', 'OTHER')", name="ck_clinical_response_action"),
    )
    op.create_index("ix_clinical_response_alert_id", "clinical_response", ["alert_id"])
    op.create_table(
        "escalation",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("alert_id", sa.String(36), sa.ForeignKey("alert.id", ondelete="RESTRICT"), nullable=False, unique=True),
        sa.Column("ward_id", sa.String(36), sa.ForeignKey("ward.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_role", sa.String(40), nullable=False, server_default="SENIOR_CLINICIAN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("target_role = 'SENIOR_CLINICIAN'", name="ck_escalation_target_role"),
    )
    op.create_table(
        "data_source_status",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("source", sa.String(40), nullable=False, unique=True),
        sa.Column("ward_id", sa.String(36), sa.ForeignKey("ward.id", ondelete="CASCADE")),
        sa.Column("connected", sa.Boolean(), nullable=False), sa.Column("is_simulated", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.Column("status_code", sa.String(40), nullable=False),
    )
    op.execute("""
        CREATE FUNCTION reject_audit_mutation() RETURNS trigger AS $$
        BEGIN
          RAISE EXCEPTION 'audit_log is append-only';
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("CREATE TRIGGER audit_log_append_only BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION reject_audit_mutation()")


def downgrade():
    op.execute("DROP TRIGGER audit_log_append_only ON audit_log")
    op.execute("DROP FUNCTION reject_audit_mutation()")
    for name in ("data_source_status", "escalation", "clinical_response", "alert_event", "alert"):
        op.drop_table(name)
    op.drop_constraint("ck_admission_simulation_scenario", "admission", type_="check")
    op.drop_column("admission", "simulation_scenario")
    op.drop_column("admission", "is_simulated")
    op.drop_column("patient", "is_simulated")
