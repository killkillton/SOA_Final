import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.firebase import TokenIdentity
from app.models import CustomerSegment, User, UserRole
from app.schemas import (
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    AuthSyncRequest,
    StaffCreateRequest,
    StaffUpdateRequest,
    UserProfileUpdate,
)


def calculate_age(dob: date, today: date | None = None) -> int:
    ref = today or date.today()
    return ref.year - dob.year - ((ref.month, ref.day) < (dob.month, dob.day))


def is_edu_email(email: str) -> bool:
    domain = email.strip().lower().split("@")[-1]
    return domain.endswith(".edu") or ".edu." in domain


def sync_firebase_user(db: Session, identity: TokenIdentity, payload: AuthSyncRequest | None) -> User:
    email = identity.email.lower()
    user = db.scalar(select(User).where(User.firebase_uid == identity.firebase_uid))

    if user is None:
        user = db.scalar(select(User).where(User.email == email))
        if user is not None:
            # Admin/partner-provisioned accounts start with firebase_uid=None until their first Firebase login.
            if user.firebase_uid is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email is already linked to another Firebase account",
                )
            user.firebase_uid = identity.firebase_uid

    if user is None:
        dob = payload.date_of_birth if payload else None
        full_name = (
            (payload.full_name.strip() if payload and payload.full_name else None)
            or identity.name
            or email.split("@")[0]
        )
        user = User(
            firebase_uid=identity.firebase_uid,
            email=email,
            full_name=full_name,
            phone=payload.phone if payload else None,
            date_of_birth=dob,
            nationality=payload.nationality if payload else None,
            role=UserRole.CUSTOMER,
            student_verified=is_edu_email(email),
            customer_segment=CustomerSegment.SENIOR if (dob and calculate_age(dob) >= 60) else None,
            is_active=True,
        )
        db.add(user)
    elif not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    db.commit()
    db.refresh(user)
    return user


def update_my_profile(db: Session, user: User, payload: UserProfileUpdate) -> User:
    updates = payload.model_dump(exclude_unset=True)
    effective_dob = updates.get("date_of_birth", user.date_of_birth)
    effective_segment = updates.get("customer_segment", user.customer_segment)

    if effective_segment == CustomerSegment.SENIOR:
        if effective_dob is None or calculate_age(effective_dob) < 60:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Senior segment requires age 60 or older",
            )

    for field, value in updates.items():
        setattr(user, field, value)

    if (
        "date_of_birth" in updates
        and "customer_segment" not in updates
        and effective_dob is not None
        and calculate_age(effective_dob) >= 60
        and user.customer_segment is None
    ):
        user.customer_segment = CustomerSegment.SENIOR

    if user.customer_segment == CustomerSegment.STUDENT and is_edu_email(user.email):
        user.student_verified = True

    db.commit()
    db.refresh(user)
    return user


def create_staff_account(db: Session, actor: User, payload: StaffCreateRequest) -> User:
    if actor.role == UserRole.HOTEL_PARTNER and actor.hotel_id is not None and payload.hotel_id != actor.hotel_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create staff for another hotel")

    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    staff = User(
        email=email,
        full_name=payload.full_name,
        phone=payload.phone,
        role=UserRole.HOTEL_STAFF,
        hotel_id=payload.hotel_id,
        firebase_uid=None,
        is_active=True,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


def list_staff_accounts(db: Session, actor: User, hotel_id: uuid.UUID | None) -> list[User]:
    stmt = select(User).where(User.role == UserRole.HOTEL_STAFF)
    if actor.role == UserRole.HOTEL_PARTNER and actor.hotel_id is not None:
        if hotel_id is not None and hotel_id != actor.hotel_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot list staff for another hotel")
        stmt = stmt.where(User.hotel_id == actor.hotel_id)
    elif hotel_id is not None:
        stmt = stmt.where(User.hotel_id == hotel_id)

    return list(db.scalars(stmt.order_by(User.email)))


def update_staff_account(
    db: Session,
    actor: User,
    staff_id: uuid.UUID,
    payload: StaffUpdateRequest,
) -> User:
    staff = db.scalar(select(User).where(User.user_id == staff_id, User.role == UserRole.HOTEL_STAFF))
    if staff is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff account not found")

    updates = payload.model_dump(exclude_unset=True)
    if actor.role == UserRole.HOTEL_PARTNER and actor.hotel_id is not None:
        if staff.hotel_id != actor.hotel_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot manage staff of another hotel")
        if "hotel_id" in updates and updates["hotel_id"] != actor.hotel_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot reassign staff to another hotel")

    for field, value in updates.items():
        setattr(staff, field, value)

    db.commit()
    db.refresh(staff)
    return staff


def admin_list_users(
    db: Session,
    role: UserRole | None,
    customer_segment: CustomerSegment | None,
    is_active: bool | None,
    hotel_id: uuid.UUID | None,
) -> list[User]:
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if customer_segment is not None:
        stmt = stmt.where(User.customer_segment == customer_segment)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if hotel_id is not None:
        stmt = stmt.where(User.hotel_id == hotel_id)

    return list(db.scalars(stmt.order_by(User.email)))


def admin_create_user(db: Session, payload: AdminUserCreateRequest) -> User:
    if payload.role == UserRole.HOTEL_STAFF and payload.hotel_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="HOTEL_STAFF requires hotel_id")

    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        firebase_uid=None,
        email=email,
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        customer_segment=payload.customer_segment,
        date_of_birth=payload.date_of_birth,
        nationality=payload.nationality,
        student_verified=payload.student_verified,
        hotel_id=payload.hotel_id,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def admin_get_user(db: Session, user_id: uuid.UUID) -> User:
    user = db.scalar(select(User).where(User.user_id == user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def admin_update_user(db: Session, user_id: uuid.UUID, payload: AdminUserUpdateRequest) -> User:
    user = admin_get_user(db, user_id)
    updates = payload.model_dump(exclude_unset=True)

    effective_role = updates.get("role", user.role)
    effective_hotel_id = updates.get("hotel_id", user.hotel_id)
    if effective_role == UserRole.HOTEL_STAFF and effective_hotel_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="HOTEL_STAFF requires hotel_id")

    for field, value in updates.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
