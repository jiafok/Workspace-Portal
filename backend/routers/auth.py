from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User, LoginSession, UserSettings
from schemas import UserCreate, UserLogin, TokenResponse, UserResponse, OAuthConfig, UserSettingsUpdate, UserSettingsResponse
import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)
OAUTH_FILE = os.path.join(DATA_DIR, "oauth_config.json")


def hash_password(password: str) -> str:
    """PBKDF2 with per-user salt. Equivalent to Werkzeug generate_password_hash."""
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600000)
    return f"pbkdf2:sha256:600000${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify PBKDF2 password hash."""
    if not stored_hash or not stored_hash.startswith("pbkdf2:"):
        return False
    try:
        # Format: pbkdf2:sha256:600000$salt$dkhex
        _, algo, rest = stored_hash.split(":", 2)
        parts = rest.split("$")
        if len(parts) != 3:
            return False
        iterations, salt, hash_val = int(parts[0]), parts[1], parts[2]
        dk = hashlib.pbkdf2_hmac(algo, password.encode(), salt.encode(), iterations)
        return dk.hex() == hash_val
    except Exception:
        return False


def create_session(user_id: int, db: Session) -> str:
    token = secrets.token_hex(32)
    session = LoginSession(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    db.add(session)
    db.commit()
    return token


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization[7:]
    session = db.query(LoginSession).filter(
        LoginSession.token == token,
        LoginSession.expires_at > datetime.utcnow()
    ).first()
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == session.user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/register", response_model=UserResponse)
def register(data: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        email=data.email,
        display_name=data.display_name or data.username,
        role="user" if db.query(User).count() > 0 else "admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if user.oauth_provider and user.oauth_provider != "local":
        raise HTTPException(status_code=400, detail=f"Please login via {user.oauth_provider}")
    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user.last_login = datetime.utcnow()
    db.commit()
    token = create_session(user.id, db)
    return TokenResponse(access_token=token, user=user)


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        db.query(LoginSession).filter(LoginSession.token == token).delete()
        db.commit()
    return {"ok": True}


@router.get("/users", response_model=list[UserResponse])
def list_users(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    return db.query(User).all()


@router.put("/users/{user_id}/role")
def update_user_role(user_id: int, role: dict, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = role["role"]
    db.commit()
    return {"ok": True}


@router.put("/users/{user_id}/active")
def toggle_user_active(user_id: int, active: dict, current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = active["is_active"]
    db.commit()
    return {"ok": True}


# OAuth2 / OIDC Configuration
@router.get("/oauth/config")
def get_oauth_config():
    if os.path.exists(OAUTH_FILE):
        with open(OAUTH_FILE, "r") as f:
            return json.load(f)
    return {"providers": []}


@router.put("/oauth/config")
def update_oauth_config(config: dict, current_user: User = Depends(get_admin_user)):
    with open(OAUTH_FILE, "w") as f:
        json.dump(config, f, indent=2)
    return {"ok": True}


# Demo account check
@router.get("/demo-status")
def demo_status(db: Session = Depends(get_db)):
    demo = db.query(User).filter(User.username == "demo").first()
    return {"has_demo": demo is not None, "user_count": db.query(User).count()}


# User Settings (language, timezone, preferences)
@router.get("/settings", response_model=UserSettingsResponse)
def get_user_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id, language="zh-CN", timezone="Asia/Shanghai", preferences="{}")
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.put("/settings", response_model=UserSettingsResponse)
def update_user_settings(data: UserSettingsUpdate,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    s = db.query(UserSettings).filter(UserSettings.user_id == current_user.id).first()
    if not s:
        s = UserSettings(user_id=current_user.id)
        db.add(s)
    if data.language is not None: s.language = data.language
    if data.timezone is not None: s.timezone = data.timezone
    if data.preferences is not None: s.preferences = data.preferences
    db.commit()
    db.refresh(s)
    return s


# i18n translations endpoint
@router.get("/i18n/{lang}")
def get_i18n(lang: str):
    translations = {
        "zh-CN": {
            "app.title": "Workspace Portal",
            "app.subtitle": "工程师工作中心",
            "nav.home": "工作台首页",
            "nav.ai_chat": "AI 对话",
            "nav.plugins": "插件市场",
            "nav.monitoring": "系统监控",
            "nav.github": "代码平台",
            "nav.webhooks": "Webhook",
            "nav.audit": "审计日志",
            "search.placeholder": "搜索网站、分类、AI、文档...",
            "search.hotkeys": "Ctrl+K",
            "theme.dark": "深色模式",
            "theme.light": "浅色模式",
            "theme.auto": "自动",
        },
        "en": {
            "app.title": "Workspace Portal",
            "app.subtitle": "Engineer Workspace Center",
            "nav.home": "Dashboard",
            "nav.ai_chat": "AI Chat",
            "nav.plugins": "Plugin Market",
            "nav.monitoring": "Monitoring",
            "nav.github": "Code Platform",
            "nav.webhooks": "Webhooks",
            "nav.audit": "Audit Log",
            "search.placeholder": "Search sites, categories, AI, docs...",
            "search.hotkeys": "Ctrl+K",
            "theme.dark": "Dark",
            "theme.light": "Light",
            "theme.auto": "Auto",
        },
    }
    return translations.get(lang, translations["en"])
