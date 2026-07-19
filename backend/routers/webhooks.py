"""
Webhook System router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import WebhookEndpoint, User
from schemas import WebhookCreate, WebhookUpdate, WebhookResponse
from routers.auth import get_current_user
from datetime import datetime
import httpx
import hashlib
import hmac

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("", response_model=List[WebhookResponse])
def list_webhooks(db: Session = Depends(get_db)):
    return db.query(WebhookEndpoint).all()


@router.post("", response_model=WebhookResponse)
def create_webhook(data: WebhookCreate, db: Session = Depends(get_db)):
    wh = WebhookEndpoint(**data.model_dump())
    db.add(wh)
    db.commit()
    db.refresh(wh)
    return wh


@router.put("/{wid}", response_model=WebhookResponse)
def update_webhook(wid: int, data: WebhookUpdate, db: Session = Depends(get_db)):
    wh = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == wid).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(wh, k, v)
    db.commit()
    db.refresh(wh)
    return wh


@router.delete("/{wid}")
def delete_webhook(wid: int, db: Session = Depends(get_db)):
    wh = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == wid).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(wh)
    db.commit()
    return {"ok": True}


@router.post("/{wid}/test")
async def test_webhook(wid: int, db: Session = Depends(get_db)):
    wh = db.query(WebhookEndpoint).filter(WebhookEndpoint.id == wid).first()
    if not wh:
        raise HTTPException(status_code=404, detail="Not found")
    return await trigger_webhook(wh, {"test": True, "timestamp": str(datetime.utcnow())})


async def trigger_webhook(wh: WebhookEndpoint, payload: dict) -> dict:
    """Trigger a single webhook. Called both from test and from other routers."""
    try:
        body = payload
        headers = {"Content-Type": "application/json"}
        if wh.secret:
            body_str = str(payload)
            sig = hmac.new(wh.secret.encode(), body_str.encode(), hashlib.sha256).hexdigest()
            headers["X-Workspace-Signature"] = sig

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(wh.url, json=body, headers=headers)
            return {"ok": resp.status_code < 400, "status": resp.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def fire_event(event_type: str, payload: dict, db: Session):
    """Fire all matching webhooks for an event. Called from other routers."""
    webhooks = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.is_enabled == True,
        (WebhookEndpoint.event_type == event_type) | (WebhookEndpoint.event_type == "all")
    ).all()
    for wh in webhooks:
        try:
            result = await trigger_webhook(wh, payload)
            wh.last_triggered = datetime.utcnow()
            wh.trigger_count += 1
        except Exception:
            pass
    db.commit()
