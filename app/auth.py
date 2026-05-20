import os
import hashlib

import bcrypt
from fastapi import HTTPException, Request, status
from sqlalchemy.orm import Session

from app.models import User


HASH_PREFIX = "$bcrypt-sha256$"


def _password_digest(password: str) -> bytes:
    return hashlib.sha256(password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    password_hash = bcrypt.hashpw(_password_digest(password), bcrypt.gensalt(rounds=12)).decode("utf-8")
    return f"{HASH_PREFIX}{password_hash}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith(HASH_PREFIX):
        stored_hash = password_hash.removeprefix(HASH_PREFIX).encode("utf-8")
        return bcrypt.checkpw(_password_digest(password), stored_hash)

    # Backward compatibility for plain bcrypt hashes created before the
    # bcrypt-sha256 wrapper. bcrypt 5 rejects inputs over 72 bytes.
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(password_bytes, password_hash.encode("utf-8"))
    except ValueError:
        return False


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
