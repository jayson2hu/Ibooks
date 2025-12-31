# Next.js Frontend

基于 Next.js 14 的 SEO 优化资源展示网站。

## 功能特性

- ✅ Next.js 14 App Router
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
npm run dev
```

访问 http://localhost:3000

### 生产构建

```bash
npm run build
npm start
```

## 环境变量

创建 `.env.local` 文件：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

## 项目结构

```
frontend/
├── src/
│   ├── app/              # Next.js 14 App Router
│   ├── components/       # React 组件
│   ├── lib/              # 工具函数
│   ├── styles/           # 全局样式
│   └── types/            # TypeScript 类型
├── public/               # 静态文件
└── next.config.js        # Next.js 配置
```

## Docker

```bash
docker build -t ibooks-frontend .
docker run -p 3000:3000 ibooks-frontend
```
