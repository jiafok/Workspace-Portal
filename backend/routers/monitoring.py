"""
Endpoint Monitoring + Notification + Audit Log router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import EndpointMonitor, Notification, AuditLog, User
from schemas import (
    EndpointMonitorCreate, EndpointMonitorUpdate, EndpointMonitorResponse,
    NotificationResponse, AuditLogResponse,
)
from routers.auth import get_current_user
from datetime import datetime
import httpx
import asyncio
import json

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


# ---- Endpoint Monitors ----
@router.get("/endpoints", response_model=List[EndpointMonitorResponse])
def list_endpoints(db: Session = Depends(get_db)):
    return db.query(EndpointMonitor).all()


@router.post("/endpoints", response_model=EndpointMonitorResponse)
def create_endpoint(data: EndpointMonitorCreate, db: Session = Depends(get_db)):
    ep = EndpointMonitor(**data.model_dump())
    db.add(ep)
    db.commit()
    db.refresh(ep)
    return ep


@router.put("/endpoints/{eid}", response_model=EndpointMonitorResponse)
def update_endpoint(eid: int, data: EndpointMonitorUpdate, db: Session = Depends(get_db)):
    ep = db.query(EndpointMonitor).filter(EndpointMonitor.id == eid).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(ep, k, v)
    db.commit()
    db.refresh(ep)
    return ep


@router.delete("/endpoints/{eid}")
def delete_endpoint(eid: int, db: Session = Depends(get_db)):
    ep = db.query(EndpointMonitor).filter(EndpointMonitor.id == eid).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(ep)
    db.commit()
    return {"ok": True}


@router.post("/endpoints/{eid}/check", response_model=EndpointMonitorResponse)
async def check_endpoint(eid: int, db: Session = Depends(get_db)):
    ep = db.query(EndpointMonitor).filter(EndpointMonitor.id == eid).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Not found")

    start = datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=ep.timeout_seconds, follow_redirects=True) as client:
            if ep.method == "HEAD":
                resp = await client.head(ep.url)
            elif ep.method == "POST":
                resp = await client.post(ep.url)
            else:
                resp = await client.get(ep.url)
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        ep.last_status = "up" if resp.status_code == ep.expected_code else "down"
        ep.last_response_ms = elapsed
    except Exception:
        elapsed = int((datetime.utcnow() - start).total_seconds() * 1000)
        ep.last_status = "down"
        ep.last_response_ms = elapsed
        ep.total_failures += 1

    ep.last_checked = datetime.utcnow()
    ep.total_checks += 1
    if ep.total_checks > 0:
        ep.uptime_percent = round(((ep.total_checks - ep.total_failures) / ep.total_checks) * 100, 1)
    db.commit()
    db.refresh(ep)

    # Create notification if status changed to down
    if ep.last_status == "down":
        notif = Notification(
            title=f"⚠️ {ep.name} 不可达",
            body=f"端点 {ep.url} 检测失败 ({ep.last_response_ms}ms)",
            level="error", source="monitor",
        )
        db.add(notif)
        db.commit()

    return ep


@router.post("/check-all")
async def check_all_endpoints(db: Session = Depends(get_db)):
    endpoints = db.query(EndpointMonitor).filter(EndpointMonitor.is_enabled == True).all()
    results = []
    for ep in endpoints:
        res = await check_endpoint(ep.id, db)
        results.append({"id": ep.id, "status": ep.last_status})
    return {"checked": len(results), "results": results}


# ---- Notifications ----
@router.get("/notifications", response_model=List[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Notification).filter(
        (Notification.user_id.is_(None)) | (Notification.user_id == current_user.id)
    ).order_by(Notification.created_at.desc())
    if unread_only:
        q = q.filter(Notification.is_read == False)
    return q.limit(limit).all()


@router.put("/notifications/{nid}/read")
def mark_read(nid: int, db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == nid).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"ok": True}


@router.put("/notifications/read-all")
def mark_all_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    return {"ok": True}


@router.get("/notifications/count")
def unread_count(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    count = db.query(Notification).filter(Notification.is_read == False).count()
    return {"count": count}


# ---- Audit Logs ----
@router.get("/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(limit: int = 100, action: str = None, db: Session = Depends(get_db)):
    q = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.filter(AuditLog.action == action)
    return q.limit(limit).all()


def create_audit_log(db: Session, user_id: int, username: str, action: str,
                     resource_type: str = "", resource_name: str = "", details: str = ""):
    """Helper to create audit log entry. Call from other routers."""
    log = AuditLog(
        user_id=user_id, username=username, action=action,
        resource_type=resource_type, resource_name=resource_name, details=details
    )
    db.add(log)
    db.commit()
