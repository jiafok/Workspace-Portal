from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ========== Auth ==========
class UserCreate(BaseModel):
    username: str
    password: str
    email: str = ""
    display_name: str = ""


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str = ""
    display_name: str = ""
    role: str = "user"
    oauth_provider: str = ""
    avatar_url: str = ""
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OAuthConfig(BaseModel):
    provider: str
    client_id: str
    client_secret: str = ""
    tenant_id: str = ""
    redirect_uri: str = ""
    enabled: bool = False


# ========== Category ==========
class CategoryBase(BaseModel):
    name: str
    icon: str = "Folder"
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    id: int
    is_default: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    website_count: int = 0

    class Config:
        from_attributes = True


# ========== Website ==========
class WebsiteBase(BaseModel):
    name: str
    url: str
    icon_url: str = ""
    description: str = ""
    category_id: int
    sort_order: int = 0
    is_pinned: bool = False
    is_favorite: bool = False
    tags: str = ""
    notes: str = ""


class WebsiteCreate(WebsiteBase):
    pass


class WebsiteUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    icon_url: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    sort_order: Optional[int] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    tags: Optional[str] = None
    notes: Optional[str] = None


class WebsiteResponse(WebsiteBase):
    id: int
    visit_count: int = 0
    last_visited: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== AI Provider ==========
class AIProviderBase(BaseModel):
    name: str
    url: str
    icon_url: str = ""
    api_url: str = ""
    api_key: str = ""
    api_type: str = "web"
    is_enabled: bool = True
    is_pinned: bool = False
    is_favorite: bool = False
    sort_order: int = 0


class AIProviderCreate(AIProviderBase):
    pass


class AIProviderUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    icon_url: Optional[str] = None
    api_url: Optional[str] = None
    api_key: Optional[str] = None
    api_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    sort_order: Optional[int] = None


class AIProviderResponse(AIProviderBase):
    id: int
    visit_count: int = 0
    last_visited: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== AI Chat ==========
class AIChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str


class AIChatRequest(BaseModel):
    provider_id: int
    model: str = ""
    messages: List[AIChatMessage]
    stream: bool = False


class AIMultiCompareRequest(BaseModel):
    prompt: str
    provider_ids: List[int]
    models: List[str] = []


class AIChatHistoryCreate(BaseModel):
    title: str = "New Chat"
    model: str = ""
    provider_id: Optional[int] = None


class AIChatHistoryUpdate(BaseModel):
    title: Optional[str] = None
    messages: Optional[str] = None


class AIChatHistoryResponse(BaseModel):
    id: int
    title: str
    model: str = ""
    provider_id: Optional[int] = None
    messages: str = "[]"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Prompt ==========
class PromptBase(BaseModel):
    title: str
    content: str
    category: str = "通用"
    tags: str = ""
    is_public: bool = False


class PromptCreate(PromptBase):
    pass


class PromptUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    is_public: Optional[bool] = None


class PromptResponse(PromptBase):
    id: int
    version: int = 1
    use_count: int = 0
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PromptVersionCreate(BaseModel):
    content: str
    changelog: str = ""


class PromptVersionResponse(BaseModel):
    id: int
    prompt_id: int
    version: int
    content: str
    changelog: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Enterprise System ==========
class EnterpriseSystemBase(BaseModel):
    name: str
    url: str
    icon_url: str = ""
    description: str = ""
    system_type: str = "other"
    is_enabled: bool = True
    is_pinned: bool = False
    sort_order: int = 0


class EnterpriseSystemCreate(EnterpriseSystemBase):
    pass


class EnterpriseSystemUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    icon_url: Optional[str] = None
    description: Optional[str] = None
    system_type: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_pinned: Optional[bool] = None
    sort_order: Optional[int] = None


class EnterpriseSystemResponse(EnterpriseSystemBase):
    id: int
    visit_count: int = 0
    last_visited: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Document Source ==========
class DocumentSourceBase(BaseModel):
    name: str
    source_type: str = "sharepoint"
    url: str = ""
    site_id: str = ""
    drive_id: str = ""
    folder_path: str = ""
    is_enabled: bool = True
    sort_order: int = 0


class DocumentSourceCreate(DocumentSourceBase):
    pass


class DocumentSourceUpdate(BaseModel):
    name: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None
    site_id: Optional[str] = None
    drive_id: Optional[str] = None
    folder_path: Optional[str] = None
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class DocumentSourceResponse(DocumentSourceBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SharePointFileResponse(BaseModel):
    id: int
    name: str
    web_url: str = ""
    file_type: str = ""
    size: int = 0
    last_modified: Optional[datetime] = None
    modified_by: str = ""
    is_favorite: bool = False

    class Config:
        from_attributes = True


# ========== NAS ==========
class NASServiceBase(BaseModel):
    name: str
    internal_url: str = ""
    external_url: str = ""
    icon_url: str = ""
    is_enabled: bool = True
    sort_order: int = 0


class NASServiceCreate(NASServiceBase):
    pass


class NASServiceUpdate(BaseModel):
    name: Optional[str] = None
    internal_url: Optional[str] = None
    external_url: Optional[str] = None
    icon_url: Optional[str] = None
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None


class NASServiceResponse(NASServiceBase):
    id: int
    visit_count: int = 0
    last_visited: Optional[datetime] = None
    internal_available: bool = False
    last_status_check: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Docker ==========
class ContainerInfoResponse(BaseModel):
    id: int
    container_id: str
    name: str
    status: str
    image: str
    ports: str
    cpu_percent: float
    memory_usage: str
    uptime: str

    class Config:
        from_attributes = True


# ========== Background ==========
class UserBackgroundCreate(BaseModel):
    bg_type: str = "color"
    bg_value: str = ""


class UserBackgroundResponse(BaseModel):
    id: int
    bg_type: str
    bg_value: str
    is_default: bool = False

    class Config:
        from_attributes = True


# ========== Generic ==========
class SortUpdate(BaseModel):
    items: List[dict]


class SettingsUpdate(BaseModel):
    key: str
    value: str


class SearchQuery(BaseModel):
    query: str


class BookmarkImportData(BaseModel):
    content: str
    source: str = "html"


# ========== V5: Plugins ==========
class PluginCreate(BaseModel):
    plugin_id: str
    name: str
    version: str = "1.0.0"
    author: str = ""
    description: str = ""
    icon_url: str = ""
    category: str = "tool"
    entry_url: str = ""
    config_schema: str = "{}"
    config_data: str = "{}"
    is_enabled: bool = False


class PluginUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config_data: Optional[str] = None
    is_enabled: Optional[bool] = None


class PluginResponse(PluginCreate):
    id: int
    is_builtin: bool = False
    installed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== V5: Endpoint Monitor ==========
class EndpointMonitorCreate(BaseModel):
    name: str
    url: str
    method: str = "GET"
    expected_code: int = 200
    interval_seconds: int = 300
    timeout_seconds: int = 10
    is_enabled: bool = True


class EndpointMonitorUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    method: Optional[str] = None
    expected_code: Optional[int] = None
    interval_seconds: Optional[int] = None
    timeout_seconds: Optional[int] = None
    is_enabled: Optional[bool] = None


class EndpointMonitorResponse(EndpointMonitorCreate):
    id: int
    last_status: str = "unknown"
    last_response_ms: int = 0
    last_checked: Optional[datetime] = None
    uptime_percent: float = 100.0
    total_checks: int = 0
    total_failures: int = 0

    class Config:
        from_attributes = True


# ========== V5: Notification ==========
class NotificationResponse(BaseModel):
    id: int
    title: str
    body: str = ""
    level: str = "info"
    source: str = "system"
    link: str = ""
    is_read: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== V5: Audit Log ==========
class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    username: str = ""
    action: str
    resource_type: str = ""
    resource_name: str = ""
    details: str = ""
    ip_address: str = ""
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== V5: GitHub/GitLab ==========
class GitHubConnectionCreate(BaseModel):
    name: str
    platform: str = "github"
    base_url: str = "https://api.github.com"
    api_token: str = ""
    username: str = ""
    repos: str = "[]"
    sync_pull_requests: bool = True
    sync_issues: bool = True
    is_enabled: bool = False


class GitHubConnectionUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_token: Optional[str] = None
    username: Optional[str] = None
    repos: Optional[str] = None
    sync_pull_requests: Optional[bool] = None
    sync_issues: Optional[bool] = None
    is_enabled: Optional[bool] = None


class GitHubConnectionResponse(GitHubConnectionCreate):
    id: int
    last_synced: Optional[datetime] = None

    class Config:
        from_attributes = True


class GitHubItemResponse(BaseModel):
    id: int
    connection_id: int
    item_type: str = "pr"
    repo_name: str = ""
    title: str
    url: str = ""
    state: str = "open"
    author: str = ""
    labels: str = "[]"
    created_at_remote: Optional[datetime] = None
    updated_at_remote: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== V5: Webhook ==========
class WebhookCreate(BaseModel):
    name: str
    url: str
    event_type: str = "all"
    secret: str = ""
    is_enabled: bool = True


class WebhookUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    event_type: Optional[str] = None
    secret: Optional[str] = None
    is_enabled: Optional[bool] = None


class WebhookResponse(WebhookCreate):
    id: int
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0

    class Config:
        from_attributes = True


# ========== V5: User Settings ==========
class UserSettingsUpdate(BaseModel):
    language: Optional[str] = None
    timezone: Optional[str] = None
    preferences: Optional[str] = None


class UserSettingsResponse(BaseModel):
    language: str = "zh-CN"
    timezone: str = "Asia/Shanghai"
    preferences: str = "{}"

    class Config:
        from_attributes = True
