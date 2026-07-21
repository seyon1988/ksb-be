import sys
import os
from datetime import datetime, timezone
import jwt
sys.path.append(os.path.dirname(__file__))

from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, Base, get_db
from models import AdminUser, AdminDetails, RefreshToken, GlobalSetting
from schemas import (
    LoginRequest, TokenResponse, RefreshTokenRequest, 
    RefreshTokenResponse, AdminUserResponse
)
from auth import (
    verify_password, create_access_token, create_refresh_token, 
    get_current_admin, SECRET_KEY, ALGORITHM
)
from seed import seed

# Auto-create tables & seed default admin on boot
Base.metadata.create_all(bind=engine)
try:
    seed()
except Exception as e:
    print("Seed warning:", e)

app = FastAPI(
    title="KSB Construction API",
    description="Backend API with Dual Token Auth (6h Access Token, 7d Refresh Token)",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json"
)

# Enable CORS for Angular frontend (Allows localhost:4200, Vercel, and all client origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.options("/{full_path:path}", include_in_schema=False)
def options_handler(full_path: str):
    return Response(status_code=200)

@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "KSB Construction API",
        "docs": "/api/docs",
        "health": "/api/health"
    }

@app.get("/favicon.ico", include_in_schema=False)
@app.get("/favicon.png", include_in_schema=False)
def favicon():
    return Response(status_code=204)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "KSB Construction API",
        "auth": "Dual Token (Access: 6h, Refresh: 7d)",
        "version": "1.0.0"
    }

@app.post("/api/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == req.username).first()
    if not admin or not verify_password(req.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    # Generate 6-hour Access Token & 7-day Refresh Token
    access_token, access_expires_at = create_access_token(admin.username, admin.id)
    refresh_token, refresh_expires_at = create_refresh_token(admin.username, admin.id, db)

    user_response = AdminUserResponse.model_validate(admin)

    return TokenResponse(
        access_token=access_token,
        access_token_expires_at=access_expires_at,
        refresh_token=refresh_token,
        refresh_token_expires_at=refresh_expires_at,
        token_type="bearer",
        user=user_response
    )

@app.post("/api/auth/refresh", response_model=RefreshTokenResponse)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    token_str = req.refresh_token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
        username: str = payload.get("sub")
        admin_id: int = payload.get("admin_id")
    except jwt.PyJWTError:
        raise credentials_exception

    # Check database for revoked/expired refresh token
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == token_str,
        RefreshToken.is_revoked == False
    ).first()

    if not db_token:
        raise credentials_exception

    if db_token.expires_at < datetime.utcnow():
        db_token.is_revoked = True
        db.commit()
        raise credentials_exception

    # Generate NEW 6-hour Access Token
    new_access_token, new_access_expires_at = create_access_token(username, admin_id)

    return RefreshTokenResponse(
        access_token=new_access_token,
        access_token_expires_at=new_access_expires_at,
        token_type="bearer"
    )

@app.post("/api/auth/logout")
def logout(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    db_token = db.query(RefreshToken).filter(RefreshToken.token == req.refresh_token).first()
    if db_token:
        db_token.is_revoked = True
        db.commit()
    return {"message": "Logged out successfully"}

@app.get("/api/auth/me", response_model=AdminUserResponse)
def get_me(current_admin: AdminUser = Depends(get_current_admin)):
    return AdminUserResponse.model_validate(current_admin)

@app.get("/api/auth/verify")
def verify_token(current_admin: AdminUser = Depends(get_current_admin)):
    return {
        "valid": True,
        "username": current_admin.username
    }

# Public Open Theme API Endpoints (No Token Required)
@app.get("/api/settings/theme")
def get_active_theme(db: Session = Depends(get_db)):
    setting = db.query(GlobalSetting).filter(GlobalSetting.key == "active_theme").first()
    theme_id = setting.value if setting else "theme-2"
    return {"theme_id": theme_id}

@app.post("/api/settings/theme")
def update_active_theme(req: dict, db: Session = Depends(get_db)):
    theme_id = req.get("theme_id", "theme-2")
    setting = db.query(GlobalSetting).filter(GlobalSetting.key == "active_theme").first()
    if setting:
        setting.value = theme_id
    else:
        setting = GlobalSetting(key="active_theme", value=theme_id)
        db.add(setting)
    db.commit()
    return {"status": "success", "theme_id": theme_id}
