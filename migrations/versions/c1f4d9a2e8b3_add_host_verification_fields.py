"""add host verification fields

Revision ID: c1f4d9a2e8b3
Revises: 7e77665bce2a
Create Date: 2026-07-08 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c1f4d9a2e8b3"
down_revision = "7e77665bce2a"
branch_labels = None
depends_on = None


host_verification_status_enum = sa.Enum(
    "Pending",
    "Verified",
    "Suspended",
    name="host_verification_status",
)


def upgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_in_number"))
        batch_op.drop_column("in_number")
        batch_op.add_column(sa.Column("nin_number", sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column("nin_document", sa.String(length=255), nullable=True))
        batch_op.add_column(
            sa.Column(
                "verification_status",
                host_verification_status_enum,
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("verified_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("verified_by", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("verification_reason", sa.Text(), nullable=True))
        batch_op.create_index("ix_users_nin_number", ["nin_number"], unique=False)
        batch_op.create_index("ix_users_verification_status", ["verification_status"], unique=False)
        batch_op.create_foreign_key(
            "fk_users_verified_by_admins",
            "admins",
            ["verified_by"],
            ["admin_id"],
        )


def downgrade():
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_constraint("fk_users_verified_by_admins", type_="foreignkey")
        batch_op.drop_index("ix_users_verification_status")
        batch_op.drop_index("ix_users_nin_number")
        batch_op.drop_column("verification_reason")
        batch_op.drop_column("verified_by")
        batch_op.drop_column("verified_at")
        batch_op.drop_column("verification_status")
        batch_op.drop_column("nin_document")
        batch_op.drop_column("nin_number")
        batch_op.add_column(sa.Column("in_number", sa.String(length=20), nullable=True))
        batch_op.create_index(batch_op.f("ix_users_in_number"), ["in_number"], unique=False)
