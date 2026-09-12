# Next.js Frontend

基于 Next.js 15.5.25 App Router 的数字资源商城前端，包含公开站点与角色分层管理后台。

## 功能特性

- ✅ Next.js 15.5.25 App Router
- ✅ TypeScript 支持
- ✅ SEO 优化 (Meta tags, OpenGraph)
- ✅ 响应式设计
- ✅ 现代 UI 设计系统
- ✅ API 客户端集成

## 快速开始

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev -- --hostname 127.0.0.1
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
npm run start -- --hostname 127.0.0.1
```

显式绑定 `127.0.0.1` 可避免本地预览服务意外暴露到局域网。Docker 构建会
自动设置 `NEXT_OUTPUT_STANDALONE=true`，生成精简的 standalone 运行包。

### 测试与质量门禁

```bash
npm test
npx tsc --noEmit --incremental false
npm run lint -- --no-cache
npm run build
npm audit --audit-level=high
```

当前记录基线：Jest `33 suites / 104 tests passed`，TypeScript、ESLint 与
`npm audit` 均通过，`npm audit` 为 0 已知漏洞，完整生产构建通过。另有 10 个
公开路由分别在桌面和 375px 视口完成 20 组浏览器回归，HTTP、控制台错误、失败
响应、破损图片和横向溢出检查全部通过。这些代码与浏览器结果仍不等同于生产
Compose/Grafana 环境验收。

### 当前交互与数据契约

- 资源卡片先用 `GET /resources/{slug}/access` 检查 `has_access`；只有用户明确点击获取资源时才调用 `POST /resources/{slug}/download` 取得云盘链接并记录下载。
- API 客户端在单标签页内合并并发 refresh，并识别其他标签页已经写入的新 token；过时请求的 401 或旧 refresh 失败不会删除较新的会话凭据。
- FAQ、联系方式和分类页分别展示加载失败、真实空数据和正常内容；分类资源加载失败时可按当前筛选重试。
- 后台用户页按 `items/total/page/page_size/pages` 分页对象读取数据，不再兼容顶层用户数组。
- 匿名站点设置只消费后端白名单中的 `key/value`；SEO “全部生成”操作会等待真实结果，并能展示成功文件或部分失败明细。

## 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
# 服务端 rewrite 可单独使用内部后端地址；本机默认与公开 API 地址相同
INTERNAL_API_URL=http://localhost:8000
```

## 项目结构

```
frontend/
├── src/
│   ├── app/              # Next.js 15 App Router
│   ├── components/       # React 组件
│   ├── lib/              # 工具函数
│   ├── styles/           # 全局样式
│   └── types/            # TypeScript 类型
├── public/               # 静态文件
└── next.config.js        # Next.js 配置
```

## Docker

```bash
# 从仓库根目录运行；Compose 会传入公开构建参数和内部 rewrite 地址。
docker compose config --quiet
docker compose up -d --build frontend
docker compose logs -f frontend
```

`NEXT_PUBLIC_*` 会被 Next.js 编译进浏览器资源，因此 Dockerfile 要求在构建
时显式传入，且公网地址变更后必须重新构建镜像。Compose 已自动从根目录的
`SITE_URL` 和 `API_PUBLIC_URL` 传入这两个参数。`INTERNAL_API_URL` 是容器网络
内的服务端地址；若不使用 Compose，必须把它设置为该容器实际可访问的后端地址。
