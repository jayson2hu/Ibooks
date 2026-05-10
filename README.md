# Digital Resource Marketplace (资源售卖网站)

一个提供电子书、视频课程、文档资料等数字资源售卖的完整平台，支持云盘链接交付。

## 🎯 项目特点

- ✅ **完整后端系统** - FastAPI + PostgreSQL + Redis
- ✅ **现代化前端** - Next.js 14 + TypeScript + SSR/SSG
- 🔐 **JWT 认证** - 安全的用户认证和授权
- 💰 **站内币交易** - 支持钱包、签到奖励、充值套餐和书币购买资源
- 📊 **性能监控** - Prometheus + Grafana 实时监控
- 📝 **审计日志** - 完整的用户行为追踪
- 🔍 **SEO 优化** - 自动生成 sitemap、RSS、静态页面、JSON-LD
- 📦 **批量导入** - 支持 Excel/CSV 批量导入资源
- 🎨 **现代UI设计** - 响应式设计、渐变效果、动画
- 🐳 **Docker 部署** - 一键启动完整服务栈

## 🏗️ 项目结构

```
ibooks/
├── backend/              # FastAPI 后端 ✅
│   ├── app/
│   │   ├── api/         # API 端点 (8组)
│   │   ├── models/      # 数据库模型 (5个)
│   │   ├── schemas/     # Pydantic 模式
│   │   ├── middleware/  # 中间件 (审计、性能)
│   │   ├── utils/       # 工具函数
│   │   └── static_generator/  # SEO 生成器
│   ├── alembic/         # 数据库迁移
│   ├── tests/           # 测试
│   └── requirements.txt
├── frontend/             # Next.js 前端 ✅
│   ├── src/
│   │   ├── app/        # Next.js 14 App Router
│   │   ├── components/ # React 组件
│   │   ├── lib/        # API 客户端
│   │   ├── styles/     # 全局样式
│   │   └── types/      # TypeScript 类型
│   └── package.json
├── docker-compose.yml   # Docker 编排
├── monitoring/          # 监控配置
│   ├── prometheus/
│   ├── grafana/
│   ├── loki/
│   └── promtail/
└── logs/                # 本地日志目录
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
# 编辑 .env 文件，设置数据库密码、JWT 密钥等
```

### 3. 使用 Docker Compose 启动

```bash
docker-compose up -d
```

服务将在以下端口启动：
- **前端网站**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **Grafana**: http://localhost:3001 (默认用户名/密码: admin/admin)
- **Prometheus**: http://localhost:9090

### 4. 数据库初始化

Docker Compose 启动后端时会先执行 `alembic upgrade head`，自动创建/更新数据库表结构。

如需手动执行迁移：

```bash
docker-compose exec backend alembic upgrade head
docker-compose exec backend alembic downgrade -1
```

详细启动指南请查看 [QUICKSTART.md](QUICKSTART.md)

## 📚 API 文档

启动服务后访问:
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
- 慢查询监控
- 系统资源监控
- 审计日志
- Grafana 可视化仪表板

## 📊 监控与日志

### 查看日志

所有日志保存在 `logs/` 目录:

```bash
# 后端访问日志
tail -f logs/backend/access.log

# 性能日志
tail -f logs/backend/performance.log

# 审计日志
tail -f logs/backend/audit.log
```

### Grafana 仪表板

访问 http://localhost:3001 查看:
- API 性能监控
- 系统资源使用
- 数据库状态
- Redis 状态

## 🛠️ 开发

### 本地开发（不使用 Docker）

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn app.main:app --reload
```

### 运行测试

```bash
cd backend
pytest tests/ -v --cov=app
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
DATABASE_URL=postgresql://...

# 安全
JWT_SECRET_KEY=your-secret-key

# 监控开关
MONITOR_PERFORMANCE=true
MONITOR_AUDIT=true

# 日志
LOG_LEVEL=INFO
LOG_FORMAT=json

# SEO
SITE_URL=https://your-domain.com
SEO_AUTO_GENERATE=true

# 支付宝充值（仅用于购买书币）
ALIPAY_APP_ID=your-alipay-app-id
ALIPAY_PRIVATE_KEY=your-private-key
ALIPAY_PUBLIC_KEY=alipay-public-key
ALIPAY_GATEWAY=https://openapi.alipaydev.com/gateway.do
```

## 💰 站内币 API 概览

```text
GET  /api/v1/wallet/me
GET  /api/v1/wallet/ledger
POST /api/v1/signin
GET  /api/v1/recharge/packages
POST /api/v1/recharge/orders
POST /api/v1/recharge/alipay/create
POST /api/v1/orders
GET  /api/v1/resources/{slug}/access
```

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

## 📝 项目完成度

### 后端: 100% ✅
- ✅ 数据库模型 (5个)
- ✅ 认证系统 (JWT)
- ✅ API 端点 (8组)
- ✅ 中间件 (审计、性能)
- ✅ 日志系统 (5种日志)
- ✅ SEO 生成器
- ✅ 批量导入
- ✅ Docker 部署
- ✅ 监控配置

### 前端: 90% ✅
- ✅ Next.js 14 项目配置
- ✅ 设计系统和全局样式
- ✅ Header 和 Footer 组件
- ✅ 首页
- ✅ 资源列表页 (SSR)
- ✅ 资源详情页 (SEO优化)
- ✅ 搜索页面
- ✅ 分类浏览页面
- ✅ 联系我们页面
- ✅ 关于我们页面

### 整体进度: ~95%

## 📱 下一步

可选的扩展开发:
- [ ] 移动端 APP
- [ ] AI 功能集成
- [ ] 微信充值渠道
- [ ] 支付宝沙箱真实联调
- [ ] 前端测试覆盖

## 📄 许可证

MIT License
