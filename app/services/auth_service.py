from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.password import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserRegister


def register_user(db: Session, user_data: UserRegister) -> User:
    existing_user = db.scalar(
        select(User).where(
            or_(
                User.username == user_data.username,
                User.email == user_data.email,
            )
        )
    )

    if existing_user:
        if existing_user.username == user_data.username:
            raise ValueError("Username already registered")

        raise ValueError("Email already registered")

    user = User(
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    username: str,
    password: str,
) -> User | None:
    user = db.scalar(
        select(User).where(User.username == username)
    )

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
