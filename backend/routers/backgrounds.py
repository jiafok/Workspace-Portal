from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import UserBackground, User
from schemas import UserBackgroundCreate, UserBackgroundResponse
from routers.auth import get_current_user
import os
import shutil

router = APIRouter(prefix="/api/backgrounds", tags=["backgrounds"])

BG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "backgrounds")
os.makedirs(BG_DIR, exist_ok=True)


@router.get("", response_model=List[UserBackgroundResponse])
def list_backgrounds(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(UserBackground).filter(
        (UserBackground.user_id == current_user.id) | (UserBackground.user_id.is_(None))
    ).all()


@router.post("", response_model=UserBackgroundResponse)
async def create_background(
    bg_type: str = "color",
    bg_value: str = "",
    file: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if file:
        bg_type = "image"
        ext = os.path.splitext(file.filename or "bg.jpg")[1]
        filename = f"bg_{current_user.id}_{int(os.path.getmtime(BG_DIR) * 1000)}{ext}"
        filepath = os.path.join(BG_DIR, filename)
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        bg_value = f"/api/backgrounds/file/{filename}"

    bg = UserBackground(user_id=current_user.id, bg_type=bg_type, bg_value=bg_value)
    db.add(bg)
    db.commit()
    db.refresh(bg)
    return bg


@router.put("/{bg_id}", response_model=UserBackgroundResponse)
def update_background(bg_id: int, data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bg = db.query(UserBackground).filter(UserBackground.id == bg_id).first()
    if not bg:
        raise HTTPException(status_code=404, detail="Not found")
    if "bg_type" in data: bg.bg_type = data["bg_type"]
    if "bg_value" in data: bg.bg_value = data["bg_value"]
    db.commit()
    return bg


@router.delete("/{bg_id}")
def delete_background(bg_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bg = db.query(UserBackground).filter(UserBackground.id == bg_id).first()
    if not bg:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(bg)
    db.commit()
    return {"ok": True}


@router.post("/set-active/{bg_id}")
def set_active(bg_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bg = db.query(UserBackground).filter(UserBackground.id == bg_id).first()
    if not bg:
        raise HTTPException(status_code=404, detail="Not found")

    # Deactivate all others for this user
    db.query(UserBackground).filter(UserBackground.user_id == current_user.id).update(
        {"is_default": False}
    )
    bg.is_default = True
    db.commit()
    return {"ok": True}


@router.get("/active")
def get_active(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bg = db.query(UserBackground).filter(
        UserBackground.user_id == current_user.id, UserBackground.is_default == True
    ).first()
    if bg:
        return bg
    return {"bg_type": "color", "bg_value": ""}


from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# This will be mounted in main.py
def mount_backgrounds(app: FastAPI):
    app.mount("/api/backgrounds/file", StaticFiles(directory=BG_DIR), name="backgrounds_files")
