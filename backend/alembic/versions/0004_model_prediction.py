from alembic import op
import sqlalchemy as sa

revision = "0004_model_prediction"
down_revision = "0003_alerts_simulation"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_prediction",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("assessment_id", sa.String(36), sa.ForeignKey("risk_assessment.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_id", sa.String(120), nullable=False),
        sa.Column("model_version", sa.String(80), nullable=False),
        sa.Column("probability", sa.Numeric(6, 5), nullable=False),
        sa.Column("calibrated", sa.Boolean(), nullable=False),
        sa.Column("feature_hash", sa.String(64), nullable=False),
        sa.Column("explanation", sa.JSON(), nullable=False),
        sa.Column("interface_demo", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.UniqueConstraint("assessment_id", "model_id", "model_version", name="uq_model_prediction_assessment_model"),
        sa.CheckConstraint("probability >= 0 AND probability <= 1", name="ck_model_prediction_probability"),
    )
    op.create_index("ix_model_prediction_assessment_id", "model_prediction", ["assessment_id"])


def downgrade():
    op.drop_table("model_prediction")
