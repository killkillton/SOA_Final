import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import CustomerSegment, UserRole


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    firebase_uid: str | None
    email: EmailStr
    full_name: str
    phone: str | None
    role: UserRole
    customer_segment: CustomerSegment | None
    date_of_birth: date | None
    nationality: str | None
    student_verified: bool
    hotel_id: uuid.UUID | None
    is_active: bool


class VerifyTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    firebase_uid: str | None
    email: str
    role: UserRole
    customer_segment: CustomerSegment | None
    student_verified: bool
    hotel_id: uuid.UUID | None
    is_active: bool


class AuthSyncRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    customer_segment: CustomerSegment | None = None


class StaffCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1)
    phone: str | None = None
    hotel_id: uuid.UUID


class StaffUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    is_active: bool | None = None
    hotel_id: uuid.UUID | None = None


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=1)
    phone: str | None = None
    role: UserRole = UserRole.CUSTOMER
    customer_segment: CustomerSegment | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    student_verified: bool = False
    hotel_id: uuid.UUID | None = None
    is_active: bool = True


class AdminUserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    role: UserRole | None = None
    customer_segment: CustomerSegment | None = None
    date_of_birth: date | None = None
    nationality: str | None = None
    student_verified: bool | None = None
    hotel_id: uuid.UUID | None = None
    is_active: bool | None = None
