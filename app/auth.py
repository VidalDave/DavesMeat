import os
from functools import wraps
from typing import Callable

from fastapi import HTTPException, Request, status
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import User


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.query(User).filter(User.username == username, User.is_active.is_(True)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def current_user(request: Request, db: Session) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()


def require_admin_user(request: Request, db: Session) -> User:
    user = current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/admin/login"})
    return user


def require_role(user: User, roles: set[str]) -> None:
    if user.role not in roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="אין הרשאה לפעולה זו")


def session_cookie_secure() -> bool:
    return os.getenv("APP_ENV", "development").lower() in {"production", "prod"}

