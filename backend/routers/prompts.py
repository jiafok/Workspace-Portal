from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import Prompt, PromptVersion, User
from schemas import (
    PromptCreate, PromptUpdate, PromptResponse,
    PromptVersionCreate, PromptVersionResponse
)
from routers.auth import get_current_user
import json
from datetime import datetime

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

PROMPT_CATEGORIES = [
    "邮件模板", "客户回复", "日志分析", "固件发布",
    "SharePoint开发", "Python开发", "需求分析", "会议纪要",
    "日报周报", "代码审查", "技术方案", "故障排查",
    "通用"
]


@router.get("/categories")
def get_prompt_categories():
    return {"categories": PROMPT_CATEGORIES}


@router.get("", response_model=List[PromptResponse])
def list_prompts(
    category: Optional[str] = None,
    tag: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Prompt).filter(
        (Prompt.is_public == True) | (Prompt.user_id == current_user.id)
    )
    if category:
        q = q.filter(Prompt.category == category)
    if tag:
        q = q.filter(Prompt.tags.ilike(f"%{tag}%"))
    return q.order_by(Prompt.updated_at.desc()).all()


@router.post("", response_model=PromptResponse)
def create_prompt(
    data: PromptCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompt = Prompt(
        title=data.title, content=data.content,
        category=data.category, tags=data.tags,
        is_public=data.is_public, user_id=current_user.id,
        version=1
    )
    db.add(prompt)
    db.flush()
    # Create version 1
    db.add(PromptVersion(prompt_id=prompt.id, version=1, content=data.content))
    db.commit()
    db.refresh(prompt)
    return prompt


@router.put("/{prompt_id}", response_model=PromptResponse)
def update_prompt(
    prompt_id: int,
    data: PromptUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Not found")
    if prompt.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")

    if data.title is not None: prompt.title = data.title
    if data.content is not None:
        prompt.content = data.content
        prompt.version += 1
        # Create new version
        db.add(PromptVersion(prompt_id=prompt.id, version=prompt.version, content=data.content))
    if data.category is not None: prompt.category = data.category
    if data.tags is not None: prompt.tags = data.tags
    if data.is_public is not None: prompt.is_public = data.is_public
    prompt.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
def delete_prompt(
    prompt_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Not found")
    if prompt.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    db.delete(prompt)
    db.commit()
    return {"ok": True}


@router.post("/{prompt_id}/use")
def record_use(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if prompt:
        prompt.use_count = (prompt.use_count or 0) + 1
        db.commit()
    return {"ok": True}


# Versions
@router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
def list_versions(prompt_id: int, db: Session = Depends(get_db)):
    return db.query(PromptVersion).filter(
        PromptVersion.prompt_id == prompt_id
    ).order_by(PromptVersion.version.desc()).all()


# Import/Export
@router.post("/import")
def import_prompts(data: dict, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    imported = 0
    for p in data.get("prompts", []):
        prompt = Prompt(
            title=p["title"], content=p["content"],
            category=p.get("category", "通用"), tags=p.get("tags", ""),
            is_public=False, user_id=current_user.id, version=1
        )
        db.add(prompt)
        imported += 1
    db.commit()
    return {"ok": True, "imported": imported}


@router.get("/export")
def export_prompts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    prompts = db.query(Prompt).filter(
        (Prompt.is_public == True) | (Prompt.user_id == current_user.id)
    ).all()
    data = [
        {"title": p.title, "content": p.content, "category": p.category, "tags": p.tags}
        for p in prompts
    ]
    return {"prompts": data}
