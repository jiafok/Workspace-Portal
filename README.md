# 🚀 Workspace Portal V5

**Engineer Workspace Center** — 现代化自托管个人/团队工作台

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://hub.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

> 替代 Homepage、Sun-Panel、Edge Sidebar 和浏览器收藏夹的下一代统一工作入口。

打开浏览器即可在一个页面内访问 AI 工具、企业系统、NAS、Docker、文档资源和所有导航网站。

---

## ✨ 功能特性

### 🏠 工作台首页
- 问候语 + 实时时间 + 天气组件
- 网站/AI/NAS 统计卡片
- 最近访问网站 / AI 工具 / 文档
- CPU / 内存 / 磁盘 系统仪表盘

### 🧭 导航管理
- 9 大默认分类，Web 界面 CRUD（**禁止 YAML 配置**）
- 拖拽排序 + 跨分类移动（Trello 风格）
- 自动获取 favicon + 网站标题 + 描述
- 失败自动使用默认图标，支持手动上传替换

### 🤖 AI 聚合中心（核心亮点）
- 预置 9 个主流 AI：ChatGPT / DeepSeek / Gemini / Claude / Copilot / Grok / Kimi / 豆包 / 通义千问
- **网页模式**：点击直接访问官网，无需任何 Token
- **API 模式**：在 Portal 内直接对话，支持 OpenAI / DeepSeek / Claude / Gemini / OpenRouter
- **多模型对比**：同一问题同时发送到多个 AI，四栏结果展示
- 对话历史管理 + Markdown 渲染

### 📝 Prompt 管理中心
- 12 种内置分类（邮件模板 / 客户回复 / 日志分析 / 代码审查 / 日报周报 等）
- 版本管理 + 导入/导出 JSON
- 一键调用到 AI 聊天

### 🔌 插件市场（6 个内置插件）
- 天气组件（OpenWeatherMap）
- Home Assistant 智能家居集成
- OpenWRT 路由器监控
- RSS 阅读器
- 快捷便签（Markdown）
- 内嵌框架（嵌入任意网页）

### 🏢 企业系统中心
- 14 个预设系统：EIP / BPM / HR / SharePoint / OneDrive / Outlook / Teams / Jira / Confluence / DevOps / IT工单 / E-Service / QCN / IMEI
- 拖拽排序 / 启用禁用 / 类型标签 / 访问统计

### 📄 文档中心
- SharePoint / OneDrive / QuecLib 集成
- Microsoft Graph API 同步框架
- 文件搜索 / 收藏

### 🖥️ NAS 中心
- DSM / Portainer / Emby / MoviePilot / OpenWebUI / xTeVe / Threadfin
- **双地址智能切换**：内网可达用 LAN，否则自动切远程

### 🐳 Docker 监控
- `/var/run/docker.sock` 自动发现容器
- 容器 CPU / 内存 / 状态 / 运行时间
- 启动 / 停止 / 重启 / 查看日志

### 🔍 全局搜索
- **Ctrl + K** 命令面板（Raycast 风格）
- 搜索网站 / 分类 / AI / 文档 / 快捷操作

### 🎨 个性化
- 深色 / 浅色 / 自动 主题
- 自定义背景（纯色 / 渐变 / 壁纸上传）
- 8 种主题色切换
- 4 种布局：卡片 / 列表 / 桌面 / 侧边栏

### 📡 端点监控
- 自定义 HTTP 健康检查端点
- 可用率统计 + 失败通知

### 🔔 通知中心 + 📝 审计日志
- 系统事件通知 + 操作审计追踪

### 📦 数据管理
- 导出 JSON / CSV，导入 JSON
- 自动备份（7 天滚动）
- 浏览器收藏夹导入（Chrome / Edge / Firefox HTML）

### 🔐 安全性
- **PBKDF2-SHA256** 密码哈希（600K 迭代 + 随机盐）
- 本地账号登录 + Entra ID / OAuth2 / OIDC
- Admin / User / Guest 三级权限

### 📱 移动端
- PWA 支持（安装到桌面）
- 底部导航栏（手机/平板自动适配）

---

## 🚀 快速部署

### 方式一：Docker 镜像拉取（无需 Clone 代码）

```bash
# 1. 创建目录和数据文件夹
mkdir workspace-portal && cd workspace-portal
mkdir data

# 2. 下载 docker-compose 文件
curl -O https://raw.githubusercontent.com/jiafok/Workspace-Portal/main/docker-compose.pull.yml

# 3. 一键启动（自动拉取预构建镜像）
docker-compose -f docker-compose.pull.yml up -d
```

**访问：** `http://localhost:8080`  |  账号：`admin` / `admin123`

### 方式二：Docker Compose 本地构建

```bash
# 克隆项目
git clone https://github.com/jiafok/Workspace-Portal.git
cd Workspace-Portal

# 一键启动（本地构建 Docker 镜像）
docker-compose up -d
```

**访问：** `http://localhost:8080`  |  API：`http://localhost:8000/docs`

### 方式三：开发环境

```bash
# 后端 (Python 3.11+)
cd backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000

# 前端 (Node.js 20+)
cd frontend
npm install
npm run dev
# → http://localhost:6066
```

---

## 🔑 默认账号

首次启动自动创建：

| 用户名 | 密码 | 角色 | 说明 |
|--------|------|------|------|
| `admin` | `admin123` | 管理员 | 全部权限 |
| `demo` | `demo123` | 用户 | 普通用户 |
| `guest` | `guest123` | 访客 | 只读访问 |

---

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **前端** | Vue 3 + TypeScript + Vite + Pinia + Element Plus + TailwindCSS + SortableJS |
| **后端** | Python FastAPI + SQLAlchemy + Pydantic |
| **数据库** | SQLite（默认），支持切换 PostgreSQL |
| **部署** | Docker + Docker Compose + PWA |
| **支持平台** | Linux / Windows / Synology DSM / Unraid / CasaOS |

---

## 📂 项目结构

```
workspace-portal/
├── docker-compose.yml              # 一键部署
├── .gitignore
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI 入口 + 初始化
│   ├── database.py                 # SQLite 配置
│   ├── models.py                   # 23 张数据表
│   ├── schemas.py                  # Pydantic 校验
│   ├── routers/
│   │   ├── auth.py                # 认证 + OAuth + i18n
│   │   ├── navigation.py          # 导航管理
│   │   ├── workspace.py           # AI / NAS CRUD
│   │   ├── ai_aggregator.py       # AI 聚合聊天 + 对比
│   │   ├── prompts.py             # Prompt 中心
│   │   ├── enterprise.py          # 企业系统
│   │   ├── documents.py           # 文档中心
│   │   ├── docker_monitor.py      # Docker 监控
│   │   ├── dashboard_data.py      # 仪表盘 + 导入导出
│   │   ├── backgrounds.py         # 壁纸管理
│   │   ├── plugins.py             # 插件系统
│   │   ├── monitoring.py          # 端点监控 + 通知 + 审计
│   │   ├── github_gitlab.py       # GitHub/GitLab 集成
│   │   └── webhooks.py            # Webhook 系统
│   └── services/
│       ├── favicon_service.py
│       ├── bookmark_import.py
│       └── system_info.py
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── vite.config.ts             # PWA 配置
│   └── src/
│       ├── App.vue                # 主布局 + 认证守卫
│       ├── router/index.ts        # 20 条路由
│       ├── stores/                # 6 个 Pinia Store
│       ├── api/index.ts           # 60+ API 端点
│       ├── views/                 # 20 个页面视图
│       └── components/            # 11 个可复用组件
└── data/                          # 运行时生成
```

---

## 🧪 测试

```bash
# 运行自动化测试（Python）
python -c "
import urllib.request, json
# 见下方完整测试脚本
"
```

**52 条测试用例 100% 通过** — 覆盖认证、导航、AI、Prompt、企业、仪表盘、插件、监控、Webhook 等 13 个模块。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request。

---

## 📄 License

MIT — 自由使用、修改和分发。

---

**Made with ❤️ for Engineers**
