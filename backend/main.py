from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base, SessionLocal
from models import (
    Category, Website, AIProvider, NASService, ContainerInfo, SystemSettings,
    User, EnterpriseSystem, Prompt, Plugin, UserSettings,
    DEFAULT_CATEGORIES, DEFAULT_AI_PROVIDERS, DEFAULT_NAS_SERVICES, BUILTIN_PLUGINS
)
from routers import navigation, workspace, docker_monitor, dashboard_data
from routers import auth, ai_aggregator, prompts, enterprise, documents, backgrounds
from routers import plugins, monitoring, github_gitlab, webhooks
import os
import hashlib
import json

Base.metadata.create_all(bind=engine)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(DATA_DIR, exist_ok=True)


def init_defaults():
    db = SessionLocal()
    try:
        if db.query(Category).count() == 0:
            for i, (name, icon, is_default) in enumerate(DEFAULT_CATEGORIES):
                db.add(Category(name=name, icon=icon, sort_order=i, is_default=is_default))

        if db.query(AIProvider).count() == 0:
            ai_defaults = [
                ("ChatGPT", "https://chat.openai.com", "web", "", ""),
                ("DeepSeek", "https://chat.deepseek.com", "deepseek", "https://api.deepseek.com/v1/chat/completions", ""),
                ("Gemini", "https://gemini.google.com", "web", "", ""),
                ("Claude", "https://claude.ai", "web", "", ""),
                ("Copilot", "https://copilot.microsoft.com", "web", "", ""),
                ("Grok", "https://x.com/i/grok", "web", "", ""),
                ("Kimi", "https://kimi.moonshot.cn", "web", "", ""),
                ("豆包", "https://www.doubao.com", "web", "", ""),
                ("通义千问", "https://tongyi.aliyun.com", "web", "", ""),
            ]
            for i, (name, url, api_type, api_url, api_key) in enumerate(ai_defaults):
                db.add(AIProvider(name=name, url=url, api_type=api_type, api_url=api_url, api_key=api_key, sort_order=i))

        if db.query(NASService).count() == 0:
            for i, (name, internal, external) in enumerate(DEFAULT_NAS_SERVICES):
                db.add(NASService(name=name, internal_url=internal,
                                  external_url=external, sort_order=i))

        # Create demo/admin account if no users exist
        if db.query(User).count() == 0:
            from routers.auth import hash_password
            admin_pw = hash_password("admin123")
            demo_pw = hash_password("demo123")
            guest_pw = hash_password("guest123")

            db.add(User(username="admin", hashed_password=admin_pw,
                       display_name="管理员", role="admin", email="admin@workspace.local"))
            db.add(User(username="demo", hashed_password=demo_pw,
                       display_name="演示用户", role="user", email="demo@workspace.local"))
            db.add(User(username="guest", hashed_password=guest_pw,
                       display_name="访客", role="guest", email="guest@workspace.local",
                       oauth_provider="local"))

        # Initialize enterprise systems
        if db.query(EnterpriseSystem).count() == 0:
            enterprise_defaults = [
                ("EIP", "https://eip.example.com", "eip"),
                ("BPM", "https://bpm.example.com", "bpm"),
                ("HR系统", "https://hr.example.com", "hr"),
                ("SharePoint", "https://yourtenant.sharepoint.com", "sharepoint"),
                ("OneDrive", "https://yourtenant-my.sharepoint.com", "onedrive"),
                ("Outlook", "https://outlook.office.com", "outlook"),
                ("Teams", "https://teams.microsoft.com", "teams"),
                ("Jira", "https://jira.example.com", "jira"),
                ("Confluence", "https://confluence.example.com", "confluence"),
                ("DevOps", "https://dev.azure.com", "devops"),
                ("IT工单", "https://ticket.example.com", "it_ticket"),
                ("E-Service", "https://eservice.example.com", "eservice"),
                ("QCN查询", "https://qcn.example.com", "qcn"),
                ("IMEI查询", "https://imei.example.com", "imei"),
            ]
            for i, (name, url, stype) in enumerate(enterprise_defaults):
                db.add(EnterpriseSystem(name=name, url=url, system_type=stype, sort_order=i))

        # Initialize builtin plugins
        if db.query(Plugin).count() == 0:
            for bp in BUILTIN_PLUGINS:
                db.add(Plugin(
                    plugin_id=bp["plugin_id"], name=bp["name"], version=bp["version"],
                    author=bp["author"], description=bp["description"],
                    icon_url=bp.get("icon_url", ""), category=bp["category"],
                    entry_url=bp.get("entry_url", ""),
                    config_schema=json.dumps(bp.get("config_schema", {})),
                    config_data="{}", is_builtin=True, is_enabled=True,
                ))

        # Sample prompts
        if db.query(Prompt).count() == 0:
            sample_prompts = [
                ("邮件回复模板-客户问题", "邮件模板",
                 "作为技术支持工程师，请根据以下客户问题起草专业回复邮件：\n\n客户问题：{{issue}}\n产品型号：{{product}}\n\n要求：礼貌、专业、提供明确解决方案"),
                ("日志分析", "日志分析",
                 "请分析以下系统日志，识别关键错误和异常：\n\n```\n{{log_content}}\n```\n\n请输出：1.错误摘要 2.根因分析 3.修复建议"),
                ("日报模板", "日报周报",
                 "根据我今天完成的工作生成日报：\n\n完成事项：\n{{done_items}}\n\n进行中：\n{{in_progress}}\n\n遇到的困难：\n{{blockers}}"),
                ("需求分析", "需求分析",
                 "作为项目经理，请分析以下需求并输出：\n1.需求拆解\n2.技术可行性评估\n3.风险点\n4.预估工时\n\n需求内容：\n{{requirement}}"),
            ]
            for title, cat, content in sample_prompts:
                db.add(Prompt(title=title, content=content, category=cat, is_public=True, version=1))

        db.commit()
    finally:
        db.close()


init_defaults()

app = FastAPI(title="Workspace Portal API", version="4.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:6066",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:6066",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
app.include_router(auth.router)
app.include_router(navigation.router)
app.include_router(workspace.router)
app.include_router(docker_monitor.router)
app.include_router(dashboard_data.router)
app.include_router(ai_aggregator.router)
app.include_router(prompts.router)
app.include_router(enterprise.router)
app.include_router(documents.router)
app.include_router(backgrounds.router)
app.include_router(plugins.router)
app.include_router(monitoring.router)
app.include_router(github_gitlab.router)
app.include_router(webhooks.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "4.0.0"}

# Serve static files
icons_dir = os.path.join(DATA_DIR, "icons")
os.makedirs(icons_dir, exist_ok=True)
app.mount("/api/icons", StaticFiles(directory=icons_dir), name="icons")

bg_dir = os.path.join(DATA_DIR, "backgrounds")
os.makedirs(bg_dir, exist_ok=True)
app.mount("/api/backgrounds/file", StaticFiles(directory=bg_dir), name="backgrounds_files")

# Serve frontend dist (single-container mode)
FRONTEND_DIR = os.path.join(DATA_DIR, "..", "frontend", "dist")
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    print(f"[Workspace Portal] Serving frontend from {FRONTEND_DIR}")
else:
    print("[Workspace Portal] Frontend dist not found. API-only mode.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
