import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import AdminUser, RefreshToken

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ksb_super_secret_jwt_key_2026_selvanathan_biranavan")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 6
REFRESH_TOKEN_EXPIRE_DAYS = 7

security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def create_access_token(username: str, admin_id: int) -> Tuple[str, str]:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode = {
        "sub": username,
        "admin_id": admin_id,
        "type": "access",
        "exp": expire,
        "iat": now
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire.isoformat()

def create_refresh_token(username: str, admin_id: int, db: Session) -> Tuple[str, str]:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": username,
        "admin_id": admin_id,
        "type": "refresh",
        "exp": expire,
        "iat": now
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # Store refresh token record in DB
    db_token = RefreshToken(
        admin_id=admin_id,
        token=encoded_jwt,
        expires_at=expire.replace(tzinfo=None),
        is_revoked=False
    )
    db.add(db_token)
    db.commit()
    return encoded_jwt, expire.isoformat()

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Access token expired or invalid. Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session Expired: Access token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    admin = db.query(AdminUser).filter(AdminUser.username == username).first()
    if admin is None or not admin.is_active:
        raise credentials_exception
    return admin
