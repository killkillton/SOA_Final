import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, UserRole
from app.schemas import StaffCreateRequest, StaffUpdateRequest, UserResponse
from app.security import require_roles
from app.services import create_staff_account, list_staff_accounts, update_staff_account

router = APIRouter(prefix="/api/v1/staff", tags=["staff"])
staff_actor_dep = require_roles(UserRole.HOTEL_PARTNER, UserRole.ADMIN)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_staff(
    payload: StaffCreateRequest,
    actor: User = Depends(staff_actor_dep),
    db: Session = Depends(get_db),
) -> User:
    return create_staff_account(db, actor, payload)


@router.get("", response_model=list[UserResponse])
def list_staff(
    hotel_id: uuid.UUID | None = None,
    actor: User = Depends(staff_actor_dep),
    db: Session = Depends(get_db),
) -> list[User]:
    return list_staff_accounts(db, actor, hotel_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_staff(
    user_id: uuid.UUID,
    payload: StaffUpdateRequest,
    actor: User = Depends(staff_actor_dep),
    db: Session = Depends(get_db),
) -> User:
    return update_staff_account(db, actor, user_id, payload)
