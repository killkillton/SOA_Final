from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.routers import admin, auth, staff, users

app = FastAPI(title="Auth & User Service", version="0.1.0")


@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc
    return {"status": "ok", "service": settings.service_name, "database": "connected"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(staff.router)
app.include_router(admin.router)
