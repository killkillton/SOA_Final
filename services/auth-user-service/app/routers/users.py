import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserProfileUpdate, UserResponse
from app.security import get_current_user, verify_internal_api_key
from app.services import admin_get_user, update_my_profile

router = APIRouter(tags=["users"])


@router.get("/api/v1/users/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/api/v1/users/me", response_model=UserResponse)
def update_me(
    payload: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> User:
    return update_my_profile(db, current_user, payload)


@router.get(
    "/api/v1/internal/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(verify_internal_api_key)],
)
def read_internal_user(user_id: uuid.UUID, db: Session = Depends(get_db)) -> User:
    return admin_get_user(db, user_id)
