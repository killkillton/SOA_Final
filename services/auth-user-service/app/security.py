import secrets

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.firebase import TokenIdentity, verify_id_token
from app.models import User, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_token_identity(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> TokenIdentity:
    if creds is None or not creds.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return verify_id_token(creds.credentials)


def get_current_user(
    identity: TokenIdentity = Depends(get_token_identity),
    db: Session = Depends(get_db),
) -> User:
    user = db.scalar(select(User).where(User.firebase_uid == identity.firebase_uid))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User profile not synced; call /api/v1/auth/sync first",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")
    return user


def require_roles(*allowed_roles: UserRole):
    def _dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return _dependency


def verify_internal_api_key(
    x_internal_api_key: str | None = Header(default=None, alias="X-Internal-API-Key"),
) -> None:
    if x_internal_api_key is None or not secrets.compare_digest(x_internal_api_key, settings.internal_api_key):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid internal API key")
