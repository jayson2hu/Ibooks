# 数字资源售卖平台 - 快速启动指南

## 🚀 一键启动完整系统

### 前置要求

- Docker & Docker Compose
- Node.js 18+ (本地开发)
- Python 3.11+ (本地开发)

### 方式一：Docker Compose (推荐)

```bash
# 1. 进入项目目录
cd d:/vscodefile/ibooks

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 设置数据库密码、JWT密钥和可选支付宝充值参数

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化数据库
docker-compose exec backend alembic upgrade head

# 5. 访问服务
# 前端网站: http://localhost:3000
# 后端API文档: http://localhost:8000/api/docs
# Grafana监控: http://localhost:3001 (admin/admin)
```

### 方式二：本地开发

#### 后端

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 运行数据库迁移
alembic upgrade head

# 启动后端
uvicorn app.main:app --reload
```

#### 前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 启动前端
npm run dev
```

## 📊 服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 (Next.js) | 3000 | 用户访问的网站 |
| 后端 (FastAPI) | 8000 | API服务 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| Prometheus | 9090 | 指标收集 |
| Grafana | 3001 | 监控仪表板 |
| Loki | 3100 | 日志聚合 |

## 🔧 常用命令

### Docker 管理

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 重启服务
docker-compose restart backend

# 停止所有服务
docker-compose down

# 完全清理（包括数据卷）
docker-compose down -v
```

### 数据库迁移

```bash
# 创建新迁移
docker-compose exec backend alembic revision --autogenerate -m "描述"

# 执行迁移
docker-compose exec backend alembic upgrade head

# 回滚迁移
docker-compose exec backend alembic downgrade -1
```

### SEO 生成

```bash
# 生成所有SEO文件（需要管理员Token）
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
# 使用API文档界面 http://localhost:8000/api/docs
```

## 🔍 故障排查

### 前端无法连接后端

检查环境变量 `NEXT_PUBLIC_API_URL` 是否正确设置。

### 数据库连接失败

1. 确认 PostgreSQL 容器正在运行：`docker-compose ps`
2. 检查数据库密码是否正确：查看 `.env` 文件

### 日志查看

所有日志保存在本地 `logs/` 目录：

```bash
# 后端日志
tail -f logs/backend/access.log
tail -f logs/backend/audit.log
tail -f logs/backend/performance.log
```

## 📚 更多文档

- [项目README](README.md) - 完整项目说明
- [后端文档](backend/README.md) - 后端API文档
- [前端文档](frontend/README.md) - 前端开发指南
- [API文档](http://localhost:8000/api/docs) - Swagger UI

## 🎯 下一步

1. ✅ 创建管理员账户
2. ✅ 添加分类和资源
3. ✅ 生成SEO文件
4. ✅ 配置监控告警
5. ✅ 部署到生产环境
