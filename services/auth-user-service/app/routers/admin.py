import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CustomerSegment, User, UserRole
from app.schemas import AdminUserCreateRequest, AdminUserUpdateRequest, UserResponse
from app.security import require_roles
from app.services import admin_create_user, admin_get_user, admin_list_users, admin_update_user

router = APIRouter(
    prefix="/api/v1/admin/users",
    tags=["admin"],
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)


@router.get("", response_model=list[UserResponse])
def list_users(
    role: UserRole | None = None,
    customer_segment: CustomerSegment | None = None,
    is_active: bool | None = None,
    hotel_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
) -> list[User]:
    return admin_list_users(db, role, customer_segment, is_active, hotel_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: AdminUserCreateRequest, db: Session = Depends(get_db)) -> User:
    return admin_create_user(db, payload)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> User:
    return admin_get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    payload: AdminUserUpdateRequest,
    db: Session = Depends(get_db),
) -> User:
    return admin_update_user(db, user_id, payload)
