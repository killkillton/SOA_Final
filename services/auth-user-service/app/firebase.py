from dataclasses import dataclass
from pathlib import Path

import firebase_admin
from fastapi import HTTPException, status
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.config import settings


@dataclass(frozen=True)
class TokenIdentity:
    firebase_uid: str
    email: str
    name: str | None = None


def _ensure_firebase_app() -> bool:
    if firebase_admin._apps:
        return True

    if settings.firebase_credentials_path:
        cred_path = Path(settings.firebase_credentials_path)
        if cred_path.is_file():
            options = {"projectId": settings.firebase_project_id} if settings.firebase_project_id else None
            firebase_admin.initialize_app(credentials.Certificate(str(cred_path)), options=options)
            return True

    if not settings.auth_dev_mode and settings.firebase_project_id:
        firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
        return True

    return False


def verify_id_token(token: str) -> TokenIdentity:
    # Allow synthetic `dev:<uid>:<email>[:<name>]` tokens locally when Firebase credentials are absent.
    if settings.auth_dev_mode and token.startswith("dev:"):
        parts = token.split(":", 3)
        if len(parts) < 3:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed dev token")
        uid = parts[1].strip()
        email = parts[2].strip().lower()
        name = parts[3].strip() if len(parts) == 4 and parts[3].strip() else None
        if not uid or "@" not in email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed dev token")
        return TokenIdentity(firebase_uid=uid, email=email, name=name)

    if not _ensure_firebase_app():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Firebase Auth is not configured",
        )

    try:
        decoded = firebase_auth.verify_id_token(token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Firebase ID token") from exc

    uid = decoded.get("uid")
    email = decoded.get("email")
    if not uid or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firebase token missing required uid or email",
        )

    return TokenIdentity(firebase_uid=uid, email=email.lower(), name=decoded.get("name"))
