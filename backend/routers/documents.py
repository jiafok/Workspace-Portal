from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import DocumentSource, SharePointFile, User
from schemas import (
    DocumentSourceCreate, DocumentSourceUpdate, DocumentSourceResponse,
    SharePointFileResponse, SortUpdate
)
from routers.auth import get_current_user, require_editor
import httpx
from datetime import datetime
import os as os_mod
import mimetypes
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import Query

router = APIRouter(prefix="/api/documents", tags=["documents"])


# Document Sources
@router.get("/sources", response_model=List[DocumentSourceResponse])
def list_sources(db: Session = Depends(get_db)):
    return db.query(DocumentSource).order_by(DocumentSource.sort_order).all()


@router.post("/sources", response_model=DocumentSourceResponse)
def create_source(data: DocumentSourceCreate, db: Session = Depends(get_db), editor: User = Depends(require_editor)):
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


# Local folder browsing
@router.get("/local/browse")
def browse_local_folder(
    path: str = Query(default="", description="Directory path relative to source folder_path"),
    source_id: int = Query(default=None, description="Document source ID")
):
    """Browse a local folder source. Returns tree structure: groups (dirs) and files."""
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required")

    source = None
    if source_id:
        from database import SessionLocal
        db = SessionLocal()
        try:
            source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
        finally:
            db.close()

    if not source or source.source_type != "local":
        raise HTTPException(status_code=404, detail="Local source not found")

    root = source.folder_path or source.url or "."
    root = os_mod.path.abspath(os_mod.path.expanduser(root))
    if not os_mod.path.exists(root):
        raise HTTPException(status_code=404, detail=f"Folder not found: {root}")

    # Resolve the target directory
    target = os_mod.path.abspath(os_mod.path.join(root, path.lstrip("/\\")))
    # Security: don't escape root
    if not target.startswith(root):
        raise HTTPException(status_code=403, detail="Access denied")

    if not os_mod.path.exists(target):
        raise HTTPException(status_code=404, detail=f"Path not found: {path}")

    groups = []
    files = []

    try:
        entries = sorted(os_mod.listdir(target), key=lambda e: (not os_mod.path.isdir(os_mod.path.join(target, e)), e.lower()))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Permission denied")

    for entry in entries:
        full = os_mod.path.join(target, entry)
        rel = os_mod.path.relpath(full, root).replace("\\", "/")
        if os_mod.path.isdir(full):
            try:
                child_count = len(os_mod.listdir(full))
            except Exception:
                child_count = 0
            groups.append({
                "name": entry,
                "path": rel,
                "type": "group",
                "children_count": child_count,
            })
        else:
            stat = os_mod.stat(full)
            mime, _ = mimetypes.guess_type(entry)
            files.append({
                "name": entry,
                "path": rel,
                "type": "file",
                "size": stat.st_size,
                "mime": mime or "application/octet-stream",
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            })

    return {
        "path": path,
        "groups": groups,
        "files": files,
    }


@router.get("/local/file")
def serve_local_file(
    path: str = Query(..., description="File path relative to source folder_path"),
    source_id: int = Query(..., description="Document source ID"),
    download: bool = Query(default=False, description="Force download instead of inline")
):
    """Serve or download a file from a local folder source."""
    if not source_id:
        raise HTTPException(status_code=400, detail="source_id is required")

    from database import SessionLocal
    db = SessionLocal()
    try:
        source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
    finally:
        db.close()

    if not source or source.source_type != "local":
        raise HTTPException(status_code=404, detail="Local source not found")

    root = source.folder_path or source.url or "."
    root = os_mod.path.abspath(os_mod.path.expanduser(root))
    target = os_mod.path.abspath(os_mod.path.join(root, path.lstrip("/\\")))

    if not target.startswith(root):
        raise HTTPException(status_code=403, detail="Access denied")
    if not os_mod.path.isfile(target):
        raise HTTPException(status_code=404, detail="File not found")

    mime, _ = mimetypes.guess_type(target)
    media_type = mime or "application/octet-stream"

    # Previewable in browser: text, images, PDF
    previewable = media_type and (
        media_type.startswith("text/") or
        media_type.startswith("image/") or
        media_type == "application/pdf"
    )

    if download or not previewable:
        return FileResponse(target, media_type=media_type, filename=os_mod.path.basename(target))
    else:
        return FileResponse(target, media_type=media_type)


@router.get("/local/search")
def search_local_folder(
    q: str = Query(..., description="Search term"),
    source_id: int = Query(..., description="Document source ID")
):
    """Fuzzy search files and folders within a local source."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        source = db.query(DocumentSource).filter(DocumentSource.id == source_id).first()
    finally:
        db.close()

    if not source or source.source_type != "local":
        raise HTTPException(status_code=404, detail="Local source not found")

    root = source.folder_path or source.url or "."
    root = os_mod.path.abspath(os_mod.path.expanduser(root))
    if not os_mod.path.exists(root):
        return {"results": []}

    query = q.lower()
    results = []

    for dirpath, dirnames, filenames in os_mod.walk(root):
        rel_dir = os_mod.path.relpath(dirpath, root).replace("\\", "/")
        if rel_dir == ".": rel_dir = ""

        for entry in dirnames + filenames:
            if query not in entry.lower():
                continue
            full = os_mod.path.join(dirpath, entry)
            rel = os_mod.path.join(rel_dir, entry).replace("\\", "/")
            is_dir = os_mod.path.isdir(full)
            stat = os_mod.stat(full) if not is_dir else None
            results.append({
                "name": entry,
                "path": rel,
                "type": "group" if is_dir else "file",
                "size": stat.st_size if stat else 0,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat() if stat else "",
            })
            if len(results) >= 200:
                break
        if len(results) >= 200:
            break

    return {"results": results}
