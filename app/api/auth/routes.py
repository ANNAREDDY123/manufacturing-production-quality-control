from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.api.auth.dependencies import get_current_user, require_roles
from app.models.user import User, UserRole
from app.models.user import User
from app.core.security import create_access_token, create_refresh_token
from app.db.database import get_db
from app.schemas.auth import (
    RefreshTokenRequest,
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.services.auth_service import authenticate_user, register_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, user_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db,
        user_data.username,
        user_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    refresh_token = create_refresh_token(
        subject=str(user.id),
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    from jose import JWTError, jwt

    from app.core.security import ALGORITHM, SECRET_KEY

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            request.refresh_token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        if payload.get("type") != "refresh":
            raise credentials_exception

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        try:
            user_id = int(user_id)
        except (TypeError, ValueError) as exc:
            raise credentials_exception from exc

    except JWTError as exc:
        raise credentials_exception from exc

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=request.refresh_token,
    )

from app.api.auth.dependencies import get_current_user
from app.models.user import User


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.token_store import revoke_token

@router.post(
    "/logout",
)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(
        HTTPBearer()
    ),
):
    revoke_token(credentials.credentials)

    return {
        "message": "Successfully logged out",
    }

@router.get(
    "/admin-test",
)
def admin_test(
    current_user: User = Depends(
        require_roles(UserRole.SUPER_ADMIN)
    ),
):
    return {
        "message": "Super Admin access granted",
        "username": current_user.username,
        "role": current_user.role.value,
    }