from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AIProvider, NASService, User
from schemas import (
    AIProviderCreate, AIProviderUpdate, AIProviderResponse,
    NASServiceCreate, NASServiceUpdate, NASServiceResponse,
    SortUpdate
)
from datetime import datetime
from routers.auth import require_editor

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


# ---- AI Providers ----

@router.get("/ai-providers", response_model=List[AIProviderResponse])
def get_ai_providers(db: Session = Depends(get_db)):
    return db.query(AIProvider).order_by(AIProvider.sort_order).all()


@router.post("/ai-providers", response_model=AIProviderResponse)
def create_ai_provider(data: AIProviderCreate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    provider = AIProvider(**data.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider


@router.put("/ai-providers/{pid}", response_model=AIProviderResponse)
def update_ai_provider(pid: int, data: AIProviderUpdate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    provider = db.query(AIProvider).filter(AIProvider.id == pid).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(provider, key, value)
    db.commit()
    db.refresh(provider)
    return provider


@router.delete("/ai-providers/{pid}")
def delete_ai_provider(pid: int, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    provider = db.query(AIProvider).filter(AIProvider.id == pid).first()
    if not provider:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(provider)
    db.commit()
    return {"ok": True}


@router.put("/ai-providers/sort")
def sort_ai_providers(data: SortUpdate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    for item in data.items:
        db.query(AIProvider).filter(AIProvider.id == item["id"]).update(
            {"sort_order": item["sort_order"]}
        )
    db.commit()
    return {"ok": True}


@router.post("/ai-providers/{pid}/visit")
def record_ai_visit(pid: int, db: Session = Depends(get_db)):
    provider = db.query(AIProvider).filter(AIProvider.id == pid).first()
    if provider:
        provider.visit_count = (provider.visit_count or 0) + 1
        provider.last_visited = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.get("/ai-recent", response_model=List[AIProviderResponse])
def get_recent_ai(limit: int = 8, db: Session = Depends(get_db)):
    return db.query(AIProvider).filter(AIProvider.is_enabled == True).order_by(
        AIProvider.last_visited.desc().nullslast()
    ).limit(limit).all()


# ---- NAS Services ----

@router.get("/nas-services", response_model=List[NASServiceResponse])
def get_nas_services(db: Session = Depends(get_db)):
    return db.query(NASService).order_by(NASService.sort_order).all()


@router.post("/nas-services", response_model=NASServiceResponse)
def create_nas_service(data: NASServiceCreate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    svc = NASService(**data.model_dump())
    db.add(svc)
    db.commit()
    db.refresh(svc)
    return svc


@router.put("/nas-services/{sid}", response_model=NASServiceResponse)
def update_nas_service(sid: int, data: NASServiceUpdate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    svc = db.query(NASService).filter(NASService.id == sid).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(svc, key, value)
    db.commit()
    db.refresh(svc)
    return svc


@router.delete("/nas-services/{sid}")
def delete_nas_service(sid: int, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    svc = db.query(NASService).filter(NASService.id == sid).first()
    if not svc:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(svc)
    db.commit()
    return {"ok": True}


@router.put("/nas-services/sort")
def sort_nas_services(data: SortUpdate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
    for item in data.items:
        db.query(NASService).filter(NASService.id == item["id"]).update(
            {"sort_order": item["sort_order"]}
        )
    db.commit()
    return {"ok": True}


@router.post("/nas-services/{sid}/visit")
def record_nas_visit(sid: int, db: Session = Depends(get_db)):
    svc = db.query(NASService).filter(NASService.id == sid).first()
    if svc:
        svc.visit_count = (svc.visit_count or 0) + 1
        svc.last_visited = datetime.utcnow()
        db.commit()
    return {"ok": True}
