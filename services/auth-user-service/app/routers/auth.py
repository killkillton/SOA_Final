from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.firebase import TokenIdentity
from app.models import User
from app.schemas import AuthSyncRequest, UserResponse, VerifyTokenResponse
from app.security import get_current_user, get_token_identity
from app.services import sync_firebase_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/sync", response_model=UserResponse)
def sync_user(
    payload: AuthSyncRequest | None = None,
    identity: TokenIdentity = Depends(get_token_identity),
    db: Session = Depends(get_db),
) -> User:
    return sync_firebase_user(db, identity, payload)


@router.get("/verify", response_model=VerifyTokenResponse)
def verify_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user
