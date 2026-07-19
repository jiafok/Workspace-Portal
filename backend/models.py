from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), default="")
    hashed_password = Column(String(255), default="")
    display_name = Column(String(100), default="")
    role = Column(String(20), default="user")  # admin, user, guest
    oauth_provider = Column(String(50), default="")  # local, azure_ad, microsoft, oidc
    oauth_sub = Column(String(255), default="")
    avatar_url = Column(String(500), default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class LoginSession(Base):
    __tablename__ = "login_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    icon = Column(String(50), default="Folder")
    sort_order = Column(Integer, default=0)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    websites = relationship("Website", back_populates="category", cascade="all, delete-orphan",
                            order_by="Website.sort_order")


class Website(Base):
    __tablename__ = "websites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    icon_url = Column(String(500), default="")
    description = Column(Text, default="")
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    sort_order = Column(Integer, default=0)
    is_pinned = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    visit_count = Column(Integer, default=0)
    last_visited = Column(DateTime, nullable=True)
    tags = Column(Text, default="")  # comma-separated tags
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="websites")


class AIProvider(Base):
    __tablename__ = "ai_providers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False)
    icon_url = Column(String(500), default="")
    api_url = Column(String(500), default="")
    api_key = Column(Text, default="")
    api_type = Column(String(50), default="web")  # web, openai, azure, deepseek, claude, gemini, openrouter
    is_enabled = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    visit_count = Column(Integer, default=0)
    last_visited = Column(DateTime, nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class AIChatHistory(Base):
    __tablename__ = "ai_chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    provider_id = Column(Integer, ForeignKey("ai_providers.id"), nullable=True)
    title = Column(String(200), default="New Chat")
    messages = Column(Text, default="[]")  # JSON array of messages
    model = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), default="通用")  # 邮件模板, 客户回复, 日志分析, etc.
    tags = Column(String(300), default="")
    version = Column(Integer, default=1)
    is_public = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    use_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan",
                            order_by="PromptVersion.version.desc()")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id"), nullable=False)
    version = Column(Integer, default=1)
    content = Column(Text, nullable=False)
    changelog = Column(String(500), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    prompt = relationship("Prompt", back_populates="versions")


class EnterpriseSystem(Base):
    __tablename__ = "enterprise_systems"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    icon_url = Column(String(500), default="")
    description = Column(Text, default="")
    system_type = Column(String(50), default="other")  # eip, bpm, hr, sharepoint, jira, devops, etc.
    is_enabled = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    visit_count = Column(Integer, default=0)
    last_visited = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentSource(Base):
    __tablename__ = "document_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50), default="sharepoint")  # sharepoint, onedrive, quecilb, custom
    url = Column(String(500), default="")
    site_id = Column(String(200), default="")
    drive_id = Column(String(200), default="")
    folder_path = Column(String(500), default="")
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class SharePointFile(Base):
    __tablename__ = "sharepoint_files"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("document_sources.id"), nullable=True)
    name = Column(String(300), nullable=False)
    web_url = Column(String(500), default="")
    file_type = Column(String(50), default="")
    size = Column(Integer, default=0)
    last_modified = Column(DateTime, nullable=True)
    modified_by = Column(String(100), default="")
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NASService(Base):
    __tablename__ = "nas_services"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    internal_url = Column(String(500), default="")
    external_url = Column(String(500), default="")
    icon_url = Column(String(500), default="")
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    visit_count = Column(Integer, default=0)
    last_visited = Column(DateTime, nullable=True)
    internal_available = Column(Boolean, default=False)
    last_status_check = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContainerInfo(Base):
    __tablename__ = "container_info"

    id = Column(Integer, primary_key=True, autoincrement=True)
    container_id = Column(String(200), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    status = Column(String(50), default="unknown")
    image = Column(String(300), default="")
    ports = Column(Text, default="")
    cpu_percent = Column(Float, default=0.0)
    memory_usage = Column(String(100), default="")
    uptime = Column(String(100), default="")
    last_updated = Column(DateTime, default=datetime.utcnow)


class SystemSettings(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, default="")


class UserBackground(Base):
    __tablename__ = "user_backgrounds"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    bg_type = Column(String(20), default="color")  # color, image, gradient, dynamic
    bg_value = Column(Text, default="")  # color hex, image URL/path, gradient CSS
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


DEFAULT_CATEGORIES = [
    ("AI助手", "Cpu", True),
    ("办公协作", "OfficeBuilding", True),
    ("研发支持", "Monitor", True),
    ("文档资源", "Document", True),
    ("客户支持", "Service", True),
    ("NAS中心", "FolderOpened", True),
    ("内网系统", "Connection", True),
    ("企业系统", "Office", True),
    ("Docker中心", "Odometer", True),
]

DEFAULT_AI_PROVIDERS = [
    ("ChatGPT", "https://chat.openai.com"),
    ("DeepSeek", "https://chat.deepseek.com"),
    ("Gemini", "https://gemini.google.com"),
    ("Claude", "https://claude.ai"),
    ("Copilot", "https://copilot.microsoft.com"),
    ("Grok", "https://x.com/i/grok"),
    ("Kimi", "https://kimi.moonshot.cn"),
    ("豆包", "https://www.doubao.com"),
    ("通义千问", "https://tongyi.aliyun.com"),
]

DEFAULT_NAS_SERVICES = [
    ("DSM", ":5000", ":5000"),
    ("Docker", ":9000", ":9000"),
    ("Portainer", ":9443", ":9443"),
    ("Emby", ":8096", ":8096"),
    ("MoviePilot", ":3000", ":3000"),
    ("DeepTutor", ":8080", ":8080"),
    ("OpenWebUI", ":3000", ":3000"),
    ("xTeVe", ":34400", ":34400"),
    ("Threadfin", ":34400", ":34400"),
]


# ============================================================
# V5 Models: Plugin System | Monitoring | Notifications |
#   Audit Log | GitHub/GitLab | Webhooks | Tabs
# ============================================================

class Plugin(Base):
    __tablename__ = "plugins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plugin_id = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    version = Column(String(20), default="1.0.0")
    author = Column(String(200), default="")
    description = Column(Text, default="")
    icon_url = Column(String(500), default="")
    category = Column(String(50), default="tool")  # tool, integration, monitoring, theme, widget
    entry_url = Column(String(500), default="")  # iframe URL or frontend component path
    config_schema = Column(Text, default="{}")  # JSON schema for plugin config
    config_data = Column(Text, default="{}")  # user-configured data
    is_enabled = Column(Boolean, default=False)
    is_builtin = Column(Boolean, default=False)
    installed_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EndpointMonitor(Base):
    __tablename__ = "endpoint_monitors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    method = Column(String(10), default="GET")  # GET, POST, HEAD
    expected_code = Column(Integer, default=200)
    interval_seconds = Column(Integer, default=300)  # check every 5min
    timeout_seconds = Column(Integer, default=10)
    is_enabled = Column(Boolean, default=True)
    last_status = Column(String(20), default="unknown")  # up, down, unknown
    last_response_ms = Column(Integer, default=0)
    last_checked = Column(DateTime, nullable=True)
    uptime_percent = Column(Float, default=100.0)
    total_checks = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(300), nullable=False)
    body = Column(Text, default="")
    level = Column(String(20), default="info")  # info, warning, error, success
    source = Column(String(50), default="system")  # system, plugin, monitor, github
    link = Column(String(500), default="")
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    username = Column(String(100), default="")
    action = Column(String(50), nullable=False)  # create, update, delete, login, logout
    resource_type = Column(String(50), default="")  # website, category, ai_provider, etc.
    resource_id = Column(Integer, nullable=True)
    resource_name = Column(String(300), default="")
    details = Column(Text, default="")
    ip_address = Column(String(50), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class GitHubConnection(Base):
    __tablename__ = "github_connections"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    platform = Column(String(20), default="github")  # github, gitlab
    base_url = Column(String(500), default="https://api.github.com")
    api_token = Column(Text, default="")
    username = Column(String(200), default="")
    repos = Column(Text, default="[]")  # JSON array of repo names to watch
    sync_pull_requests = Column(Boolean, default=True)
    sync_issues = Column(Boolean, default=True)
    is_enabled = Column(Boolean, default=False)
    last_synced = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class GitHubItem(Base):
    __tablename__ = "github_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    connection_id = Column(Integer, ForeignKey("github_connections.id"), nullable=False)
    item_type = Column(String(20), default="pr")  # pr, issue
    repo_name = Column(String(200), default="")
    title = Column(String(500), nullable=False)
    url = Column(String(500), default="")
    state = Column(String(20), default="open")  # open, closed, merged
    author = Column(String(100), default="")
    labels = Column(Text, default="[]")
    created_at_remote = Column(DateTime, nullable=True)
    updated_at_remote = Column(DateTime, nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    event_type = Column(String(50), default="all")  # all, navigation, docker, system, custom
    secret = Column(String(200), default="")
    is_enabled = Column(Boolean, default=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    language = Column(String(10), default="zh-CN")
    timezone = Column(String(50), default="Asia/Shanghai")
    preferences = Column(Text, default="{}")  # JSON blob for arbitrary prefs
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


BUILTIN_PLUGINS = [
    {
        "plugin_id": "weather-widget",
        "name": "天气组件",
        "version": "1.0.0",
        "author": "Workspace Portal",
        "description": "在仪表盘显示实时天气信息，支持 OpenWeatherMap API，可按城市配置",
        "icon_url": "",
        "category": "widget",
        "entry_url": "",
        "config_schema": '{"api_key":"","city":"Shanghai","units":"metric"}',
        "is_builtin": True,
    },
    {
        "plugin_id": "home-assistant",
        "name": "Home Assistant",
        "version": "1.0.0",
        "author": "Workspace Portal",
        "description": "集成 Home Assistant 智能家居，显示设备状态并支持快速控制",
        "icon_url": "",
        "category": "integration",
        "entry_url": "",
        "config_schema": '{"url":"http://homeassistant.local:8123","access_token":""}',
        "is_builtin": True,
    },
    {
        "plugin_id": "openwrt-monitor",
        "name": "OpenWRT 监控",
        "version": "1.0.0",
        "author": "Workspace Portal",
        "description": "监控 OpenWRT 路由器状态：CPU/内存/网络流量/客户端列表",
        "icon_url": "",
        "category": "monitoring",
        "entry_url": "",
        "config_schema": '{"url":"http://192.168.1.1","username":"root","password":""}',
        "is_builtin": True,
    },
    {
        "plugin_id": "rss-reader",
        "name": "RSS 阅读器",
        "version": "1.0.0",
        "author": "Workspace Portal",
        "description": "订阅 RSS/Atom 源，聚合技术新闻和博客到工作台",
        "icon_url": "",
        "category": "widget",
        "entry_url": "",
        "config_schema": '{"feeds":[]}',
        "is_builtin": True,
    },
    {
        "plugin_id": "quick-notes",
        "name": "快捷便签",
        "version": "1.0.0",
        "author": "Workspace Portal",
        "description": "Markdown 便签，快速记录想法和待办事项",
        "icon_url": "",
        "category": "tool",
        "entry_url": "",
        "config_schema": "{}",
        "is_builtin": True,
    },
    {
        "plugin_id": "iframe-embed",
        "name": "内嵌框架",
        "version": "1.0.0",
        "author": "Workspace Portal",
        "description": "将任意网页嵌入工作台面板，如监控大屏、数据看板",
        "icon_url": "",
        "category": "tool",
        "entry_url": "",
        "config_schema": '{"url":"","title":""}',
        "is_builtin": True,
    },
]
