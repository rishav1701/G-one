from alembic import op
import sqlalchemy as sa
revision="0001_security_spine"; down_revision=None; branch_labels=None; depends_on=None
def upgrade():
    role=sa.Enum("ADMIN","SENIOR_CLINICIAN","CLINICIAN","VIEWER",name="user_role")
    op.create_table("ward",sa.Column("id",sa.String(36),primary_key=True),sa.Column("name",sa.String(80),nullable=False,unique=True))
    op.create_table("app_user",sa.Column("id",sa.String(36),primary_key=True),sa.Column("username",sa.String(120),nullable=False,unique=True),sa.Column("password_hash",sa.String(255),nullable=False),sa.Column("role",role,nullable=False),sa.Column("active",sa.Boolean,nullable=False,server_default=sa.true()),sa.Column("failed_logins",sa.Integer,nullable=False,server_default="0"),sa.Column("locked_until",sa.DateTime(timezone=True)))
    op.create_index("ix_app_user_username","app_user",["username"])
    op.create_table("user_ward",sa.Column("user_id",sa.String(36),sa.ForeignKey("app_user.id",ondelete="CASCADE"),primary_key=True),sa.Column("ward_id",sa.String(36),sa.ForeignKey("ward.id",ondelete="CASCADE"),primary_key=True))
    op.create_table("session",sa.Column("id",sa.String(36),primary_key=True),sa.Column("token_hash",sa.String(64),nullable=False,unique=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("app_user.id",ondelete="CASCADE"),nullable=False),sa.Column("csrf_hash",sa.String(64),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("last_seen_at",sa.DateTime(timezone=True),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_session_token_hash","session",["token_hash"])
    op.create_table("api_key",sa.Column("id",sa.String(36),primary_key=True),sa.Column("key_hash",sa.String(64),nullable=False,unique=True),sa.Column("scope",sa.String(40),nullable=False,server_default="ingest:write"))
    op.create_table("system_config",sa.Column("key",sa.String(100),primary_key=True),sa.Column("value",sa.String(500),nullable=False))
    op.create_table("audit_log",sa.Column("id",sa.String(36),primary_key=True),sa.Column("actor_id",sa.String(36)),sa.Column("action",sa.String(100),nullable=False),sa.Column("object_type",sa.String(60),nullable=False),sa.Column("object_id",sa.String(36)),sa.Column("request_id",sa.String(36),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False))
    op.create_index("ix_audit_log_created_at","audit_log",["created_at"])
def downgrade():
    for table in ("audit_log","system_config","api_key","session","user_ward","app_user","ward"): op.drop_table(table)
    sa.Enum(name="user_role").drop(op.get_bind(),checkfirst=True)
