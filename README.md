# Digital Resource Marketplace (资源售卖网站)

一个提供电子书、视频课程、文档资料等数字资源的售卖平台，已实现站内币购买与云盘链接交付等核心业务，当前处于发布验收收尾阶段。

## 🎯 项目特点

- ✅ **核心后端能力** - FastAPI + PostgreSQL + Redis
- ✅ **现代化前端** - Next.js 15 App Router + TypeScript
- 🔐 **JWT 认证** - 安全的用户认证和授权
- 💰 **站内币交易** - 支持钱包、签到奖励、充值套餐和书币购买资源
- 📊 **监控配置** - Prometheus + Grafana + Loki + Promtail（完整运行验收待执行）
- 📝 **审计日志** - 关键认证、管理和写操作追踪
- 🔍 **SEO 优化** - 启动自动生成 sitemap/RSS/robots，资源静态 HTML 按需生成
- 📦 **批量导入** - 支持 Excel/CSV 批量导入资源
- 🎨 **现代UI设计** - 响应式设计、渐变效果、动画
- 🐳 **Docker Compose 编排** - 完整服务定义、健康检查与监控配置

## 🏗️ 项目结构

```
ibooks/
├── backend/              # FastAPI 后端 ✅
│   ├── app/
│   │   ├── api/         # API 端点
│   │   ├── models/      # 数据库模型
│   │   ├── schemas/     # Pydantic 模式
│   │   ├── middleware/  # 中间件 (审计、性能)
│   │   ├── utils/       # 工具函数
│   │   └── static_generator/  # SEO 生成器
│   ├── alembic/         # 数据库迁移
│   ├── tests/           # 测试
│   ├── logs/            # 非 Docker 本地运行时的日志目录
│   ├── requirements.txt      # 生产运行依赖
│   └── requirements-dev.txt  # 测试、审计与 lint 依赖
├── frontend/             # Next.js 前端 ✅
│   ├── src/
│   │   ├── app/        # Next.js 15 App Router
│   │   ├── components/ # React 组件
│   │   ├── lib/        # API 客户端
│   │   ├── styles/     # 全局样式
│   │   └── types/      # TypeScript 类型
│   └── package.json
├── docker-compose.yml   # Docker 编排
└── monitoring/          # 监控配置
    ├── prometheus/
    ├── grafana/
    ├── loki/
    └── promtail/
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository_url>
cd ibooks
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 填写空值：数据库/JWT/Grafana 密钥、SITE_URL、API_PUBLIC_URL、CORS_ORIGINS
# 本机 Docker 调试还需显式设置 DEBUG=true 和 localhost URL；生产保持 DEBUG=false
```

### 3. 使用 Docker Compose 启动

```bash
docker compose config --quiet
docker compose up -d --build
```

服务将在以下端口启动：
- **前端网站**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs（仅 `DEBUG=true`）
- **Grafana**: http://localhost:3001（用户名 `admin`，密码来自 `GRAFANA_PASSWORD`）
- **Prometheus**: http://localhost:9090

PostgreSQL、Redis、Loki 和两个指标 exporter 不映射宿主机端口；前端、后端、
Prometheus 与 Grafana 的宿主机端口默认都只监听 `127.0.0.1`，可通过 `.env`
中的绑定地址和端口变量调整。

### 4. 数据库初始化

Docker Compose 启动后端时会先执行 `alembic upgrade head`，自动创建/更新数据库表结构。

PostgreSQL、Redis、后端文件日志、生成的 SEO 文件和上传文件都使用 Docker
命名卷持久化；执行 `docker compose down -v` 会删除这些卷，不属于普通停止流程。

如需手动执行迁移：

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend alembic downgrade -1
```

详细启动指南请查看 [QUICKSTART.md](QUICKSTART.md)

## 📚 API 文档

本地开发以 `DEBUG=true` 启动后访问（生产模式会关闭交互式文档）:
- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## 🔑 主要功能

### 用户管理
- 邮箱注册登录
- JWT Token 认证
- 角色权限控制 (admin/user/moderator)
- 邮箱验证与密码重置

### 站内币与购买流程
- 钱包余额与不可变书币流水
- 每日签到按后台开关发放书币
- 支付宝用于充值书币，不用于资源订单支付
- 资源购买统一使用书币扣款
- 免费资源或已购买资源可查看云盘链接

### 资源管理
- CRUD 操作
- 分类管理(支持层级结构)
- 标签系统
- 云盘链接管理
- 批量导入 (Excel/CSV)

### SEO 优化
- 自动生成 sitemap.xml
- RSS 订阅源
- robots.txt
- 静态 HTML 页面
- JSON-LD 结构化数据

### 监控系统
- API 性能追踪
- 慢请求监控
- PostgreSQL / Redis exporter 指标采集
- 审计日志
- Grafana API 指标与日志仪表板配置

## 📊 监控与日志

### 查看日志

Compose 运行时优先通过 Docker 查看服务标准输出：

```bash
docker compose logs -f backend
```

后端文件日志位于 `backend_logs` 命名卷，并由 Promtail 只读采集；不要假定
Compose 会在宿主机生成 `logs/backend/*`。直接在 `backend/` 中本地运行时，
日志仍写入 `LOG_DIR`（默认 `logs`）。

### Grafana 仪表板

访问 http://localhost:3001 查看:
- API 请求速率、响应时间和错误率
- 慢接口统计
- Loki 后端日志

PostgreSQL 与 Redis exporter 指标由 Prometheus 采集；当前预置 Grafana
Dashboard 不应描述为已包含数据库或 Redis 专用面板。

## 🛠️ 开发

### 本地开发（不使用 Docker）

```bash
cd backend

# 安装本地开发与测试依赖（已包含 requirements.txt）
python -m pip install -r requirements-dev.txt

# 复制并检查 backend/.env；Redis 是完整运行和 /health 就绪检查的依赖
cp .env.example .env

# 初始化/升级数据库
alembic upgrade head

# 运行开发服务器
python -m uvicorn app.main:app --reload
```

### 运行测试

```bash
cd backend
python -m pytest tests --cov=app --cov-report=term-missing
ruff check app tests
```

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

## 📦 批量导入资源

### 1. 下载模板

访问 API 端点下载 Excel 模板:
```
GET /api/v1/bulk-import/template
```

### 2. 填写数据

按照模板格式填写资源信息。

### 3. 上传导入

```
POST /api/v1/bulk-import/resources
```

## 🔧 配置说明

主要环境变量 (`.env`):

```env
# 数据库
DB_PASSWORD=<random-hex-value>

# 安全
JWT_SECRET_KEY=<random-value-at-least-32-characters>
GRAFANA_PASSWORD=<independent-random-value>
DEBUG=false

# 宿主机绑定（默认全部仅监听本机）
FRONTEND_BIND_ADDRESS=127.0.0.1
FRONTEND_PORT=3000
BACKEND_BIND_ADDRESS=127.0.0.1
BACKEND_PORT=8000
MONITORING_BIND_ADDRESS=127.0.0.1
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001

# 监控保留期与 Docker json-file 日志轮转
PROMETHEUS_RETENTION=15d
LOKI_RETENTION=168h
LOG_MAX_SIZE=10m
LOG_MAX_FILES=5

# 监控开关
MONITOR_PERFORMANCE=true
MONITOR_AUDIT=true

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json

# SEO
SITE_URL=https://your-domain.com

# 后端公网地址（支付宝异步通知使用）
API_PUBLIC_URL=https://api.your-domain.com
CORS_ORIGINS=https://your-domain.com
SEO_AUTO_GENERATE=true
# 百度推送为可选能力；保持 false 时 BAIDU_API_KEY 可留空
SEO_SUBMIT_BAIDU=false
BAIDU_API_KEY=

# 支付宝充值（仅用于购买书币；不联调充值时三个凭据可留空）
ALIPAY_APP_ID=
ALIPAY_PRIVATE_KEY=
ALIPAY_PUBLIC_KEY=
ALIPAY_SANDBOX=false

# 邮件验证与密码重置（真实投递时才需要完整 SMTP 凭据）
EMAIL_SMTP_HOST=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_FROM=
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_USE_TLS=true
```

`SEO_AUTO_GENERATE=true` 会在后端启动时仅在本地刷新 `sitemap.xml`、`rss.xml`
和 `robots.txt`；它不会触发百度、Google 或 360 提交，资源 HTML 仍由管理员接口按需生成。

Compose 会把 `SITE_URL` 和 `API_PUBLIC_URL` 同时作为前端构建参数。修改任一
公网地址后必须重新构建前端镜像；支付宝网关由 `ALIPAY_SANDBOX` 自动选择。

### 静态 SEO HTML 访问

管理员调用 `POST /api/v1/seo/generate-static-pages` 后，已发布资源的生成文件可
通过前端同域地址访问：

```text
https://your-domain.com/generated/resources/{slug}.html
```

本地开发对应 `http://localhost:3000/generated/resources/{slug}.html`。Next.js
rewrite 在容器内优先使用 `INTERNAL_API_URL`，其他环境回退到
`NEXT_PUBLIC_API_URL`。该页面用于检查或投放预生成 SEO HTML；正常产品页及
canonical 地址仍为 `/resources/{slug}`。文件尚未生成、已删除或 slug 非法时
返回 `404`。

## 💰 站内币 API 概览

```text
GET  /api/v1/wallet/me
GET  /api/v1/wallet/ledger
POST /api/v1/signin
GET  /api/v1/recharge/packages
POST /api/v1/recharge/orders
POST /api/v1/recharge/alipay/create
POST /api/v1/orders
GET  /api/v1/resources/{slug}/access    # 仅检查权限，返回 has_access
POST /api/v1/resources/{slug}/download  # 返回交付字段并原子增加下载计数
```

资源详情页只用 `GET .../access` 判断是否已有访问权，不会从权限检查接口取得
云盘链接。用户明确点击“获取资源”后才调用 `POST .../download`，返回
`cloud_link`、`backup_links`、`access_code` 并记录一次下载。

后台资产管理：

```text
GET  /api/v1/admin/wallets
GET  /api/v1/admin/coin-ledger
POST /api/v1/admin/wallets/{user_id}/adjust
GET  /api/v1/admin/recharge-orders
GET  /api/v1/admin/recharge-packages
POST /api/v1/admin/recharge-packages
PATCH /api/v1/admin/recharge-packages/{id}
PUT  /api/v1/admin/settings/signin
```

## 📝 当前验证状态

2026-09-12 已复核代码与进度记录，并重新通过前端 Jest `33 suites / 104 tests`、TypeScript、ESLint、后端 Ruff 和 `pip check`。核心业务及本地验收完成，真实支付、邮件、百度及生产服务栈联调仍待完成；详情见 [DEV_PLAN.md](DEV_PLAN.md)。本次归档分支为 `codex/project-closeout-20260912`。

以下完整验收数据记录于 **2026-09-10**；后端全量覆盖率、生产构建、迁移、浏览器及漏洞审计本次未重新执行。

- 后端完整质量门禁：`292 passed`，总覆盖率 `72.42%`（约 `72%`）；Ruff、`pip check`、`pip-audit` 均通过，依赖审计为 0 已知漏洞。
- 前端已升级到 Next.js `15.5.25`；锁文件解析 Axios `1.20.0`、PostCSS `8.5.28`。Jest `33 suites / 104 tests passed`，TypeScript、ESLint、完整生产构建与 `npm audit` 均通过，`npm audit` 为 0 已知漏洞。
- 浏览器验收：10 个公开路由分别覆盖桌面和 375px，共 20 组；HTTP、控制台错误、失败响应、破损图片和横向溢出检查均通过。
- 数据库迁移：全新数据库 `upgrade -> downgrade -1 -> upgrade` 往返及 `alembic check` 均通过；paid 订单部分唯一索引及爬虫来源唯一约束已验证。
- 爬虫已消除资源查重 N+1，并通过数据库唯一约束与 Redis 跨进程租约防止重复抓取；`moderator` 仅能管理爬虫白名单配置。
- `SEO_AUTO_GENERATE=true` 的启动生成已验证为纯本地操作，失败不会阻止服务启动，也不会隐式提交到搜索引擎。
- `POST /seo/generate-all` 会等待 sitemap、RSS、robots 的真实生成结果；全部成功返回文件清单，部分失败返回不含内部异常细节的 500，并列出成功/失败文件。
- 匿名站点设置接口仅返回允许公开的展示键，响应项只含 `key/value`，不暴露分类、说明、更新时间或更新人等后台元数据。
- Access/refresh token 已分离并轮换；前端能识别其他标签页已经写入的新 token，过时请求的 401 或旧 refresh 失败不会清除新会话。
- FAQ、联系方式与分类页区分“真实空数据”和“加载失败”，故障时展示明确的可重试错误态；`GET /api/v1/admin/users` 统一返回 `items/total/page/page_size/pages` 分页对象。
- Compose、监控 provisioning 和健康检查配置已具备，但尚未完成使用生产式显式密钥与公网 URL 的整套容器运行验收，因此不应描述为“生产已验收”。

## 📱 后续工作

发布验收仍需：

- [ ] 启动完整 Compose 服务栈并验证全部健康检查及 Grafana/Prometheus/Loki 联动。
- [ ] 若 Docker Hub 镜像拉取继续超时，需先解决部署主机网络/镜像源这一外部环境问题再完成整栈验收。
- [ ] 使用真实支付宝沙箱凭据完成充值、异步回调和到账验证。
- [ ] 使用真实 SMTP 与百度站长平台凭据完成公网投递/推送验证。
- [ ] 确认是否仍需实现 Google Search Console / 360 自动提交。

可选扩展：

- [ ] 移动端 APP
- [ ] AI 功能集成
- [ ] 微信充值渠道

## 📄 许可证

MIT License
