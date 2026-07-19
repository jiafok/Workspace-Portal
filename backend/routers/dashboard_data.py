from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Website, Category, AIProvider, NASService, SystemSettings
from schemas import BookmarkImportData
from services.bookmark_import import parse_bookmark_html
from services.system_info import get_system_info
import json
import csv
from io import StringIO
from fastapi.responses import StreamingResponse, JSONResponse
import datetime

router = APIRouter(prefix="/api", tags=["dashboard", "data"])


@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    sys_info = get_system_info()
    recent_websites = db.query(Website).order_by(
        Website.last_visited.desc().nullslast()
    ).limit(8).all()
    recent_ai = db.query(AIProvider).filter(AIProvider.is_enabled == True).order_by(
        AIProvider.last_visited.desc().nullslast()
    ).limit(6).all()

    total_websites = db.query(Website).count()
    total_categories = db.query(Category).count()
    total_ai = db.query(AIProvider).filter(AIProvider.is_enabled == True).count()
    total_nas = db.query(NASService).filter(NASService.is_enabled == True).count()

    return {
        "system": sys_info,
        "recent_websites": recent_websites,
        "recent_ai": recent_ai,
        "stats": {
            "total_websites": total_websites,
            "total_categories": total_categories,
            "total_ai": total_ai,
            "total_nas": total_nas,
        }
    }


@router.post("/bookmarks/import")
def import_bookmarks(data: BookmarkImportData, db: Session = Depends(get_db)):
    parsed = parse_bookmark_html(data.content)
    imported_categories = 0
    imported_websites = 0

    for cat_data in parsed:
        cat = Category(name=cat_data["name"])
        db.add(cat)
        db.flush()
        imported_categories += 1

        for web_data in cat_data.get("websites", []):
            web = Website(
                name=web_data["name"],
                url=web_data["url"],
                icon_url=web_data.get("icon_url", ""),
                category_id=cat.id
            )
            db.add(web)
            imported_websites += 1

    db.commit()
    return {
        "ok": True,
        "imported_categories": imported_categories,
        "imported_websites": imported_websites
    }


@router.get("/export/json")
def export_json(db: Session = Depends(get_db)):
    categories = db.query(Category).all()
    data = {"categories": [], "websites": [], "ai_providers": [], "nas_services": []}

    for cat in categories:
        data["categories"].append({
            "name": cat.name, "icon": cat.icon, "sort_order": cat.sort_order
        })
        for web in cat.websites:
            data["websites"].append({
                "name": web.name, "url": web.url, "icon_url": web.icon_url,
                "description": web.description, "category_name": cat.name,
                "sort_order": web.sort_order, "notes": web.notes
            })

    for ai in db.query(AIProvider).all():
        data["ai_providers"].append({
            "name": ai.name, "url": ai.url, "is_enabled": ai.is_enabled
        })

    for nas in db.query(NASService).all():
        data["nas_services"].append({
            "name": nas.name, "internal_url": nas.internal_url,
            "external_url": nas.external_url, "is_enabled": nas.is_enabled
        })

    return JSONResponse(content=data,
                        headers={"Content-Disposition": "attachment; filename=workspace_export.json"})


@router.post("/import/json")
async def import_json(request: dict, db: Session = Depends(get_db)):
    data = request
    for cat_data in data.get("categories", []):
        cat = Category(**cat_data)
        db.add(cat)
    db.commit()

    cat_map = {c.name: c.id for c in db.query(Category).all()}

    for web_data in data.get("websites", []):
        cat_name = web_data.pop("category_name", None)
        cat_id = cat_map.get(cat_name) if cat_name else None
        if cat_id is None and cat_map:
            cat_id = list(cat_map.values())[0]
        if cat_id:
            web_data["category_id"] = cat_id
            db.add(Website(**web_data))

    for ai_data in data.get("ai_providers", []):
        db.add(AIProvider(**ai_data))

    for nas_data in data.get("nas_services", []):
        db.add(NASService(**nas_data))

    db.commit()
    return {"ok": True}


@router.get("/export/excel")
def export_excel(db: Session = Depends(get_db)):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["类型", "名称", "网址", "分类", "图标URL", "描述", "备注"])
    for web in db.query(Website).all():
        writer.writerow(["网站", web.name, web.url, web.category.name if web.category else "",
                          web.icon_url, web.description, web.notes])
    for ai in db.query(AIProvider).all():
        writer.writerow(["AI", ai.name, ai.url, "", "", "", ""])
    for nas in db.query(NASService).all():
        writer.writerow(["NAS", nas.name, nas.internal_url or nas.external_url, "", "", "", ""])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=workspace_export.csv"}
    )


@router.get("/settings/{key}")
def get_setting(key: str, db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    return {"key": key, "value": setting.value if setting else ""}


@router.put("/settings/{key}")
def update_setting(key: str, value: dict, db: Session = Depends(get_db)):
    setting = db.query(SystemSettings).filter(SystemSettings.key == key).first()
    if setting:
        setting.value = value["value"]
    else:
        setting = SystemSettings(key=key, value=value["value"])
        db.add(setting)
    db.commit()
    return {"ok": True}


@router.post("/auto-backup")
def auto_backup(db: Session = Depends(get_db)):
    import os
    backup_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data", "backups")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(backup_dir, f"backup_{timestamp}.json")

    categories = db.query(Category).all()
    data = {"categories": [], "websites": [], "ai_providers": [], "nas_services": []}
    for cat in categories:
        data["categories"].append({"name": cat.name, "icon": cat.icon, "sort_order": cat.sort_order})
        for web in cat.websites:
            data["websites"].append({
                "name": web.name, "url": web.url, "category_name": cat.name,
                "sort_order": web.sort_order
            })
    for ai in db.query(AIProvider).all():
        data["ai_providers"].append({"name": ai.name, "url": ai.url})
    for nas in db.query(NASService).all():
        data["nas_services"].append({"name": nas.name, "internal_url": nas.internal_url,
                                     "external_url": nas.external_url})

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Keep only last 7 backups
    files = sorted([f for f in os.listdir(backup_dir) if f.endswith(".json")], reverse=True)
    for old_file in files[7:]:
        os.remove(os.path.join(backup_dir, old_file))

    return {"ok": True, "path": filepath}
