from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Category, Website
from schemas import (
    CategoryCreate, CategoryUpdate, CategoryResponse,
    WebsiteCreate, WebsiteUpdate, WebsiteResponse, SortUpdate
)
from services.favicon_service import fetch_site_info, download_icon

router = APIRouter(prefix="/api/navigation", tags=["navigation"])


# ---- Categories ----

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    categories = db.query(Category).order_by(Category.sort_order).all()
    result = []
    for cat in categories:
        website_count = db.query(Website).filter(Website.category_id == cat.id).count()
        result.append(CategoryResponse(
            id=cat.id, name=cat.name, icon=cat.icon,
            sort_order=cat.sort_order, is_default=cat.is_default,
            created_at=cat.created_at, updated_at=cat.updated_at,
            website_count=website_count
        ))
    return result


@router.post("/categories", response_model=CategoryResponse)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    cat = Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return CategoryResponse(
        id=cat.id, name=cat.name, icon=cat.icon,
        sort_order=cat.sort_order, is_default=cat.is_default,
        created_at=cat.created_at, updated_at=cat.updated_at,
        website_count=0
    )


@router.put("/categories/{cat_id}", response_model=CategoryResponse)
def update_category(cat_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cat, key, value)
    db.commit()
    db.refresh(cat)
    website_count = db.query(Website).filter(Website.category_id == cat.id).count()
    return CategoryResponse(
        id=cat.id, name=cat.name, icon=cat.icon,
        sort_order=cat.sort_order, is_default=cat.is_default,
        created_at=cat.created_at, updated_at=cat.updated_at,
        website_count=website_count
    )


@router.delete("/categories/{cat_id}")
def delete_category(cat_id: int, db: Session = Depends(get_db)):
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
    return {"ok": True}


@router.put("/categories/sort")
def sort_categories(data: SortUpdate, db: Session = Depends(get_db)):
    for item in data.items:
        db.query(Category).filter(Category.id == item["id"]).update(
            {"sort_order": item["sort_order"]}
        )
    db.commit()
    return {"ok": True}


# ---- Websites ----

@router.get("/websites", response_model=List[WebsiteResponse])
def get_websites(category_id: int = None, db: Session = Depends(get_db)):
    q = db.query(Website).order_by(Website.sort_order)
    if category_id is not None:
        q = q.filter(Website.category_id == category_id)
    return q.all()


@router.post("/websites", response_model=WebsiteResponse)
async def create_website(data: WebsiteCreate, db: Session = Depends(get_db)):
    if not data.name or not data.description:
        try:
            info = await fetch_site_info(data.url)
            if not data.name and info.get("name"):
                data.name = info["name"]
            if not data.description and info.get("description"):
                data.description = info["description"]
            if not data.icon_url and info.get("icon_url"):
                local_path = await download_icon(info["icon_url"])
                if local_path:
                    data.icon_url = local_path
                else:
                    data.icon_url = info["icon_url"]
        except Exception:
            pass

    website = Website(**data.model_dump())
    db.add(website)
    db.commit()
    db.refresh(website)
    return website


@router.put("/websites/{web_id}", response_model=WebsiteResponse)
def update_website(web_id: int, data: WebsiteUpdate, db: Session = Depends(get_db)):
    web = db.query(Website).filter(Website.id == web_id).first()
    if not web:
        raise HTTPException(status_code=404, detail="Website not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(web, key, value)
    db.commit()
    db.refresh(web)
    return web


@router.delete("/websites/{web_id}")
def delete_website(web_id: int, db: Session = Depends(get_db)):
    web = db.query(Website).filter(Website.id == web_id).first()
    if not web:
        raise HTTPException(status_code=404, detail="Website not found")
    db.delete(web)
    db.commit()
    return {"ok": True}


@router.put("/websites/sort")
def sort_websites(data: SortUpdate, db: Session = Depends(get_db)):
    for item in data.items:
        updates = {"sort_order": item["sort_order"]}
        if "category_id" in item:
            updates["category_id"] = item["category_id"]
        db.query(Website).filter(Website.id == item["id"]).update(updates)
    db.commit()
    return {"ok": True}


@router.post("/websites/{web_id}/visit")
def record_visit(web_id: int, db: Session = Depends(get_db)):
    from datetime import datetime
    web = db.query(Website).filter(Website.id == web_id).first()
    if web:
        web.visit_count = (web.visit_count or 0) + 1
        web.last_visited = datetime.utcnow()
        db.commit()
    return {"ok": True}


@router.get("/recent", response_model=List[WebsiteResponse])
def get_recent_websites(limit: int = 10, db: Session = Depends(get_db)):
    return db.query(Website).order_by(Website.last_visited.desc().nullslast()).limit(limit).all()


@router.get("/search")
def search_navigation(q: str, db: Session = Depends(get_db)):
    like = f"%{q}%"
    websites = db.query(Website).filter(
        (Website.name.ilike(like)) | (Website.url.ilike(like)) | (Website.description.ilike(like))
    ).all()
    categories = db.query(Category).filter(Category.name.ilike(like)).all()
    return {
        "websites": websites,
        "categories": categories
    }
