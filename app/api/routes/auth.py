from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import SESSION_COOKIE_NAME, get_current_session
from app.core.config import settings
from app.core.security import generate_session_token, verify_password
from app.db.session import get_db
from app.models.admin_user import AdminSession, AdminUser
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> LoginResponse:
    result = await db.execute(select(AdminUser).where(AdminUser.username == payload.username))
    admin = result.scalar_one_or_none()

    if admin is None or not verify_password(payload.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(minutes=settings.SESSION_TOKEN_EXPIRE_MINUTES)

    session = AdminSession(token=token, admin_user_id=admin.id, expires_at=expires_at)
    db.add(session)
    await db.commit()

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.SESSION_TOKEN_EXPIRE_MINUTES * 60,
    )

    return LoginResponse(token=token, expires_at=expires_at.isoformat())


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    session: AdminSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> None:
    await db.execute(delete(AdminSession).where(AdminSession.id == session.id))
    await db.commit()
    response.delete_cookie(SESSION_COOKIE_NAME)
