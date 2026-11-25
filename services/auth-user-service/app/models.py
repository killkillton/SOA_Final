import enum
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    HOTEL_PARTNER = "HOTEL_PARTNER"
    HOTEL_STAFF = "HOTEL_STAFF"
    ADMIN = "ADMIN"


class CustomerSegment(str, enum.Enum):
    STUDENT = "STUDENT"
    BUSINESS = "BUSINESS"
    SENIOR = "SENIOR"
    FOREIGNER = "FOREIGNER"


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Null until first Firebase login links an admin/partner-provisioned account.
    firebase_uid: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False, default=UserRole.CUSTOMER)
    customer_segment: Mapped[CustomerSegment | None] = mapped_column(
        Enum(CustomerSegment, name="customer_segment"),
        nullable=True,
    )
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(100), nullable=True)
    student_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    hotel_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
