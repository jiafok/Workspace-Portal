from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import EnterpriseSystem
from schemas import (
    EnterpriseSystemCreate, EnterpriseSystemUpdate, EnterpriseSystemResponse,
    SortUpdate
)
from datetime import datetime

router = APIRouter(prefix="/api/enterprise", tags=["enterprise"])

DEFAULT_ENTERPRISE_SYSTEMS = [
    ("EIP", "eip", "https://eip.example.com"),
    ("BPM", "bpm", "https://bpm.example.com"),
    ("HR系统", "hr", "https://hr.example.com"),
    ("SharePoint", "sharepoint", "https://sharepoint.example.com"),
    ("OneDrive", "onedrive", "https://onedrive.example.com"),
    ("Outlook", "outlook", "https://outlook.office.com"),
    ("Teams", "teams", "https://teams.microsoft.com"),
    ("Jira", "jira", "https://jira.example.com"),
    ("Confluence", "confluence", "https://confluence.example.com"),
    ("DevOps", "devops", "https://devops.example.com"),
    ("IT工单", "it_ticket", "https://ticket.example.com"),
    ("E-Service", "eservice", "https://eservice.example.com"),
    ("QCN查询", "qcn", "https://qcn.example.com"),
    ("IMEI查询", "imei", "https://imei.example.com"),
]


@router.get("", response_model=List[EnterpriseSystemResponse])
def list_systems(db: Session = Depends(get_db)):
    return db.query(EnterpriseSystem).order_by(EnterpriseSystem.sort_order).all()


@router.post("", response_model=EnterpriseSystemResponse)
def create_system(data: EnterpriseSystemCreate, db: Session = Depends(get_db)):
    system = EnterpriseSystem(**data.model_dump())
    db.add(system)
    db.commit()
    db.refresh(system)
    return system


@router.put("/{sid}", response_model=EnterpriseSystemResponse)
def update_system(sid: int, data: EnterpriseSystemUpdate, db: Session = Depends(get_db)):
    system = db.query(EnterpriseSystem).filter(EnterpriseSystem.id == sid).first()
    if not system:
        raise HTTPException(status_code=404, detail="Not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(system, k, v)
    db.commit()
    db.refresh(system)
    return system


@router.delete("/{sid}")
def delete_system(sid: int, db: Session = Depends(get_db)):
    system = db.query(EnterpriseSystem).filter(EnterpriseSystem.id == sid).first()
    if not system:
        raise HTTPException(status_code=404, detail="Not found")
    db.delete(system)
    db.commit()
    return {"ok": True}


@router.put("/sort")
def sort_systems(data: SortUpdate, db: Session = Depends(get_db)):
    for item in data.items:
        db.query(EnterpriseSystem).filter(EnterpriseSystem.id == item["id"]).update(
            {"sort_order": item["sort_order"]}
        )
    db.commit()
    return {"ok": True}


@router.post("/{sid}/visit")
def record_visit(sid: int, db: Session = Depends(get_db)):
    system = db.query(EnterpriseSystem).filter(EnterpriseSystem.id == sid).first()
    if system:
        system.visit_count = (system.visit_count or 0) + 1
        system.last_visited = datetime.utcnow()
        db.commit()
    return {"ok": True}
