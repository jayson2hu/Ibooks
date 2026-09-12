# 数字资源售卖平台 - 快速启动指南

## 🚀 本地启动系统

### 前置要求

- Docker & Docker Compose
- Node.js 18.18+（Docker/CI 使用 Node.js 20）
- Python 3.11+ (本地开发)

### 方式一：Docker Compose (推荐)

```bash
# 1. 进入项目目录
cd ibooks

# 2. 配置环境变量
cp .env.example .env
# 必填：DB_PASSWORD、JWT_SECRET_KEY、GRAFANA_PASSWORD、SITE_URL、
# API_PUBLIC_URL、CORS_ORIGINS，并显式设置 ALIPAY_SANDBOX。
# 本机调试使用 DEBUG=true 和 localhost URL；支付宝、SMTP、百度凭据
# 在不测试对应外部集成时可以留空，BAIDU_API_KEY 不是普通启动必填项。

# 本机 Compose 调试至少改为类似以下值：
# DB_PASSWORD=<local-random-value>
# JWT_SECRET_KEY=<local-random-value-at-least-32-characters>
# GRAFANA_PASSWORD=<different-local-random-value>
# DEBUG=true
# SITE_URL=http://localhost:3000
# API_PUBLIC_URL=http://localhost:8000
# CORS_ORIGINS=http://localhost:3000
# ALIPAY_SANDBOX=true

# 3. 校验配置并构建、启动服务
docker compose config --quiet
docker compose up -d --build

# 4. 查看服务状态（后端启动命令会先自动执行 alembic upgrade head）
docker compose ps

# 5. 访问服务
# 前端网站: http://localhost:3000
# 后端API文档: http://localhost:8000/api/docs（仅 DEBUG=true）
# Grafana监控: http://127.0.0.1:3001（密码来自 GRAFANA_PASSWORD）
```

### 方式二：本地开发

#### 后端

```bash
cd backend

# 安装本地开发与质量门禁依赖（已包含生产运行依赖）
python -m pip install -r requirements-dev.txt

# 配置环境变量
cp .env.example .env

# 运行数据库迁移
alembic upgrade head

# 启动后端
python -m uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动前端
npm run dev -- --hostname 127.0.0.1
```

### 当前验证基线

- 后端：`292 passed`，总覆盖率 `72.42%`（约 `72%`）；Ruff、`pip check`、`pip-audit` 均通过，依赖审计为 0 已知漏洞。
- 数据库：全新数据库 `alembic upgrade head -> downgrade -1 -> upgrade head` 往返和 `alembic check` 均通过。
- 前端：Next.js `15.5.25`，Jest `33 suites / 104 tests passed`，TypeScript、ESLint、完整生产构建与 `npm audit` 通过，`npm audit` 为 0 已知漏洞。
- 浏览器：10 个公开路由 × 桌面/375px 共 20 组，HTTP、控制台错误、失败响应、破损图片和横向溢出检查全部通过。

以上是代码质量门禁，不等同于生产环境整栈验收。

当前接口与页面行为约定：

- `GET /api/v1/resources/{slug}/access` 只检查权限并返回 `has_access`；只有用户明确获取资源时调用 `POST /api/v1/resources/{slug}/download`，后者返回交付字段并原子增加下载计数。
- 匿名 `GET /api/v1/settings` 只返回白名单展示设置，每项仅含 `key/value`，后台元数据不会公开。
- 多标签页同时触发 token 刷新时，旧请求不会清除另一个标签页已经轮换成功的新凭据。
- FAQ、联系方式、分类及分类资源区分加载失败与真实空数据；失败态提供明确提示和可用时的重试入口。
- `GET /api/v1/admin/users` 返回 `items`、`total`、`page`、`page_size`、`pages` 分页对象，不再使用顶层数组契约。

## 📊 服务端口

| 服务 | 宿主机地址/端口 | 说明 |
|------|-----------------|------|
| 前端 (Next.js) | `127.0.0.1:3000` | 默认仅本机访问 |
| 后端 (FastAPI) | `127.0.0.1:8000` | 默认仅本机访问 |
| Prometheus | `127.0.0.1:9090` | 默认仅本机访问 |
| Grafana | `127.0.0.1:3001` | 默认仅本机访问 |
| PostgreSQL / Redis | 不映射 | 仅 Compose 私有网络访问 |
| Exporters / Loki / Promtail | 不映射 | 仅 Compose 私有网络访问 |

可通过 `FRONTEND_BIND_ADDRESS` / `FRONTEND_PORT`、
`BACKEND_BIND_ADDRESS` / `BACKEND_PORT`、`MONITORING_BIND_ADDRESS`、
`PROMETHEUS_PORT` 和 `GRAFANA_PORT` 调整宿主机绑定。仅在明确需要直接网络暴露时
才把绑定地址改为 `0.0.0.0`，并应同时配置防火墙和反向代理。

## 🔧 常用命令

### Docker 管理

```bash
# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启服务
docker compose restart backend

# 停止所有服务
docker compose down

# 危险：仅在明确需要重置本地数据库、上传、SEO 文件、日志和监控数据时删除数据卷
docker compose down -v
```

### 数据库迁移

```bash
# 创建新迁移
docker compose exec backend alembic revision --autogenerate -m "描述"

# 执行迁移
docker compose exec backend alembic upgrade head

# 回滚迁移
docker compose exec backend alembic downgrade -1
```

### SEO 生成

```bash
# SEO_AUTO_GENERATE=true 时，后端启动会在本地生成 sitemap.xml、rss.xml、
# robots.txt，不会访问搜索引擎。以下手动接口需要 admin 或 moderator Token；
# 只有 SEO_SUBMIT_BAIDU=true 且配置 BAIDU_API_KEY 时才会尝试百度推送。
# generate-all 会等待三个文件的实际结果；全部成功返回 generated 清单，
# 部分失败返回 500，并在 detail 中列出 generated/failed 文件名。
curl -X POST "http://localhost:8000/api/v1/seo/generate-all" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 站内币主流程调试

```bash
# 查看钱包
curl "http://localhost:8000/api/v1/wallet/me" \
  -H "Authorization: Bearer USER_TOKEN"

# 签到领取书币（需后台开启签到）
curl -X POST "http://localhost:8000/api/v1/signin" \
  -H "Authorization: Bearer USER_TOKEN"

# 查看充值套餐
curl "http://localhost:8000/api/v1/recharge/packages" \
  -H "Authorization: Bearer USER_TOKEN"

# 创建充值订单
curl -X POST "http://localhost:8000/api/v1/recharge/orders" \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"package_id": 1, "payment_method": "alipay"}'

# 创建支付宝充值链接（需要支付宝沙箱或正式凭证）
curl -X POST "http://localhost:8000/api/v1/recharge/alipay/create" \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"recharge_no": "RCH..."}'

# 使用书币购买资源，成功后订单直接 paid
curl -X POST "http://localhost:8000/api/v1/orders" \
  -H "Authorization: Bearer USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resource_id": 1}'

# 无副作用地检查是否有访问权；响应只包含 has_access
curl "http://localhost:8000/api/v1/resources/RESOURCE_SLUG/access" \
  -H "Authorization: Bearer USER_TOKEN"

# 用户明确点击获取资源时交付云盘字段，并原子记录一次下载
curl -X POST "http://localhost:8000/api/v1/resources/RESOURCE_SLUG/download" \
  -H "Authorization: Bearer USER_TOKEN"
```

### 后台资产管理

```bash
# 管理员调整用户余额
curl -X POST "http://localhost:8000/api/v1/admin/wallets/USER_ID/adjust" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 10, "description": "测试加币"}'

# 查看资产流水
curl "http://localhost:8000/api/v1/admin/coin-ledger?user_id=USER_ID" \
  -H "Authorization: Bearer ADMIN_TOKEN"

# 开启签到并设置奖励
curl -X PUT "http://localhost:8000/api/v1/admin/settings/signin" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"enabled": true, "reward_coins": 5}'
```

## 📝 首次使用

### 1. 创建管理员账户

以下流程仅用于受控的本地开发环境。生产环境应通过受审计的一次性运维流程创建首个管理员，并立即使用独立强密码。

```bash
# 注册用户
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "Admin123"
  }'

# 需要在数据库中手动将用户角色改为admin
# 或通过pgAdmin等工具操作
```

### 2. 导入示例数据

```bash
# 下载导入模板
curl "http://localhost:8000/api/v1/bulk-import/template" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -o template.xlsx

# 填写数据后上传
# 使用 API 文档界面 http://localhost:8000/api/docs（需 DEBUG=true）
```

## 🔍 故障排查

### 前端无法连接后端

检查环境变量 `NEXT_PUBLIC_API_URL` 是否正确设置。

### 数据库连接失败

1. 确认 PostgreSQL 容器正在运行：`docker compose ps`
2. 检查数据库密码是否正确：查看 `.env` 文件

### 日志查看

Compose 日志通过 Docker 查看：

```bash
docker compose logs -f backend
```

后端文件日志保存在 `backend_logs` 命名卷并由 Promtail 只读采集，不会默认写到
宿主机 `logs/backend/`。只有直接在 `backend/` 本地运行时才使用 `LOG_DIR`
（默认 `logs`）。

## 📚 更多文档

- [项目README](README.md) - 完整项目说明
- [后端文档](backend/README.md) - 后端API文档
- [前端文档](frontend/README.md) - 前端开发指南
- [API文档](http://localhost:8000/api/docs) - Swagger UI（仅 `DEBUG=true`）

## 🎯 发布前仍需完成

- [ ] 使用生产式显式密钥与公网 URL 启动整套 Compose 服务，确认全部健康检查通过。
- [ ] 实际打开 Grafana，确认 Prometheus 指标与 Loki 日志链路正常。
- [ ] 若 Docker Hub 镜像拉取超时，先修复部署主机网络或配置可信镜像源后再继续整栈验收。
- [ ] 使用支付宝沙箱凭据验证充值与异步回调。
- [ ] 使用真实 SMTP 与百度站长平台凭据验证邮件投递和 URL 推送。
- [ ] 确认产品是否仍需要 Google Search Console / 360 自动提交；当前仅保留配置项，未实现提交服务。

本指南说明如何启动和调试项目，不代表上述生产验收已经完成。
