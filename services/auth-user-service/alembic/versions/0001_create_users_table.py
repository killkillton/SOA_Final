from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_create_users_table"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# create_type=False prevents op.create_table from re-creating enums already created via checkfirst=True.
user_role_enum = postgresql.ENUM(
    "CUSTOMER",
    "HOTEL_PARTNER",
    "HOTEL_STAFF",
    "ADMIN",
    name="user_role",
    create_type=False,
)
customer_segment_enum = postgresql.ENUM(
    "STUDENT",
    "BUSINESS",
    "SENIOR",
    "FOREIGNER",
    name="customer_segment",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    user_role_enum.create(bind, checkfirst=True)
    customer_segment_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("firebase_uid", sa.String(length=128), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("role", user_role_enum, nullable=False, server_default=sa.text("'CUSTOMER'")),
        sa.Column("customer_segment", customer_segment_enum, nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        sa.Column("student_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("hotel_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.create_index("ix_users_firebase_uid", "users", ["firebase_uid"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_hotel_id", "users", ["hotel_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_hotel_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_index("ix_users_firebase_uid", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    customer_segment_enum.drop(bind, checkfirst=True)
    user_role_enum.drop(bind, checkfirst=True)
