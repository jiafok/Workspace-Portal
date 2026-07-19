from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import DocumentSource, SharePointFile, User
from schemas import (
    DocumentSourceCreate, DocumentSourceUpdate, DocumentSourceResponse,
    SharePointFileResponse, SortUpdate
)
from routers.auth import get_current_user
import httpx
from datetime import datetime

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Document Sources
@router.get("/sources", response_model=List[DocumentSourceResponse])
def list_sources(db: Session = Depends(get_db)):
    return db.query(DocumentSource).order_by(DocumentSource.sort_order).all()


@router.post("/sources", response_model=DocumentSourceResponse)
def create_source(data: DocumentSourceCreate, db: Session = Depends(get_db)):
    source = DocumentSource(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@router.put("/sources/{sid}", response_model=DocumentSourceResponse)
def update_source(sid: int, data: DocumentSourceUpdate, db: Session = Depends(get_db)):
    source = db.query(DocumentSource).filter(DocumentSource.id == sid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(source, k, v)
    db.commit()
    db.refresh(source)
    return source


@router.delete("/sources/{sid}")
def delete_source(sid: int, db: Session = Depends(get_db)):
    source = db.query(DocumentSource).filter(DocumentSource.id == sid).first()
    if not source:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(source)
    db.commit()
    return {"ok": True}


@router.put("/sources/sort")
def sort_sources(data: SortUpdate, db: Session = Depends(get_db)):
    for item in data.items:
        db.query(DocumentSource).filter(DocumentSource.id == item["id"]).update(
            {"sort_order": item["sort_order"]}
        )
    db.commit()
    return {"ok": True}


# SharePoint / Graph API integration
@router.get("/sharepoint/files", response_model=List[SharePointFileResponse])
def get_sharepoint_files(source_id: int = None, db: Session = Depends(get_db)):
    """Get cached SharePoint files. Use /api/documents/sharepoint/sync to refresh."""
    q = db.query(SharePointFile)
    if source_id:
        q = q.filter(SharePointFile.source_id == source_id)
    return q.order_by(SharePointFile.last_modified.desc().nullslast()).limit(100).all()


@router.post("/sharepoint/sync")
async def sync_sharepoint(source_id: int, db: Session = Depends(get_db)):
    """Sync files from SharePoint using Microsoft Graph API."""
    source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # This would use the Microsoft Graph API with an access token
    # For now, return the cached data and provide configuration instructions
    return {
        "ok": True,
        "message": "To enable SharePoint sync, configure Microsoft Graph API credentials in settings.",
        "config_hint": {
            "required": ["tenant_id", "client_id", "client_secret"],
            "graph_endpoint": "https://graph.microsoft.com/v1.0",
            "example_endpoint": f"/sites/{source.site_id or '{site-id}'}/drive/root/children"
        }
    }


@router.post("/sharepoint/favorite/{file_id}")
def toggle_favorite(file_id: int, db: Session = Depends(get_db)):
    file = db.query(SharePointFile).filter(SharePointFile.id == file_id).first()
    if file:
        file.is_favorite = not file.is_favorite
        db.commit()
    return {"ok": True}


@router.get("/sharepoint/favorites", response_model=List[SharePointFileResponse])
def get_favorites(db: Session = Depends(get_db)):
    return db.query(SharePointFile).filter(SharePointFile.is_favorite == True).all()


@router.get("/sharepoint/search")
def search_sharepoint(q: str, db: Session = Depends(get_db)):
    files = db.query(SharePointFile).filter(
        SharePointFile.name.ilike(f"%{q}%")
    ).limit(50).all()
    return files
