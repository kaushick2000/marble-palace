from datetime import datetime, timezone

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.admin_user import AdminSession, AdminUser

SESSION_COOKIE_NAME = "session_token"


def _extract_token(authorization: str | None, session_token: str | None) -> str:
    if authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() == "bearer" and value:
            return value
    if session_token:
        return session_token
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing session token",
    )


async def get_current_session(
    authorization: str | None = Header(default=None),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
) -> AdminSession:
    token = _extract_token(authorization, session_token)

    result = await db.execute(select(AdminSession).where(AdminSession.token == token))
    session = result.scalar_one_or_none()

    if session is None or session.expires_at < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    return session


async def get_current_admin(
    session: AdminSession = Depends(get_current_session),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    admin = await db.get(AdminUser, session.admin_user_id)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session token",
        )

    return admin
