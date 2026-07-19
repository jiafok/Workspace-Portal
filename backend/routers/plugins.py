"""
Plugin System Router - plugin registry, enable/disable, configure, marketplace
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import Plugin, BUILTIN_PLUGINS
from schemas import PluginCreate, PluginUpdate, PluginResponse
import json

router = APIRouter(prefix="/api/plugins", tags=["plugins"])


@router.get("", response_model=List[PluginResponse])
def list_plugins(db: Session = Depends(get_db)):
    installed = db.query(Plugin).all()
    installed_ids = {p.plugin_id for p in installed}

    # Merge builtin plugins that aren't in DB yet
    for bp in BUILTIN_PLUGINS:
        if bp["plugin_id"] not in installed_ids:
            plugin = Plugin(
                plugin_id=bp["plugin_id"], name=bp["name"], version=bp["version"],
                author=bp["author"], description=bp["description"],
                icon_url=bp.get("icon_url", ""), category=bp["category"],
                entry_url=bp.get("entry_url", ""),
                config_schema=json.dumps(bp.get("config_schema", {})),
                config_data="{}", is_builtin=True, is_enabled=True,
            )
            db.add(plugin)
    db.commit()
    return db.query(Plugin).all()


@router.put("/{plugin_id}/toggle", response_model=PluginResponse)
def toggle_plugin(plugin_id: str, db: Session = Depends(get_db)):
    plugin = db.query(Plugin).filter(Plugin.plugin_id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin.is_enabled = not plugin.is_enabled
    db.commit()
    db.refresh(plugin)
    return plugin


@router.put("/{plugin_id}/config", response_model=PluginResponse)
def update_plugin_config(plugin_id: str, data: dict, db: Session = Depends(get_db)):
    plugin = db.query(Plugin).filter(Plugin.plugin_id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    plugin.config_data = json.dumps(data.get("config_data", {}))
    db.commit()
    db.refresh(plugin)
    return plugin


@router.post("", response_model=PluginResponse)
def install_plugin(data: PluginCreate, db: Session = Depends(get_db)):
    existing = db.query(Plugin).filter(Plugin.plugin_id == data.plugin_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Plugin already installed")
    plugin = Plugin(**data.model_dump())
    db.add(plugin)
    db.commit()
    db.refresh(plugin)
    return plugin


@router.delete("/{plugin_id}")
def uninstall_plugin(plugin_id: str, db: Session = Depends(get_db)):
    plugin = db.query(Plugin).filter(Plugin.plugin_id == plugin_id).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    if plugin.is_builtin:
        raise HTTPException(status_code=400, detail="Builtin plugins cannot be uninstalled")
    db.delete(plugin)
    db.commit()
    return {"ok": True}


@router.get("/categories")
def plugin_categories():
    return {
        "categories": [
            {"value": "tool", "label": "工具", "icon": "Tools"},
            {"value": "integration", "label": "集成", "icon": "Connection"},
            {"value": "monitoring", "label": "监控", "icon": "Odometer"},
            {"value": "theme", "label": "主题", "icon": "Brush"},
            {"value": "widget", "label": "组件", "icon": "Grid"},
        ]
    }
