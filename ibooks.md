### 资源售卖网站 · 需求总览

## 1. 项目定位

一个提供电子书、视频课程、文档资料等数字资源售卖的网站，通过 **云盘链接** 进行交付。系统包含：

- 用户前台网站（SEO 强化）
- 管理后台（资源 / 用户 / 联系方式管理）
- 后端 API（FastAPI）
- 性能监控 + 日志分析系统
- 可配置的审计机制（IP、行为记录）
- 未来可扩展能力（AI、订阅、分销等）

## 2. 整体架构组成（前端 / 后端 / 管理后台）

### （1）前端展示站（SEO 优化核心）

- SSR / SSG（提升 SEO 抓取）
- 支持资源列表 / 搜索 / 分类 / 详情
- 商品可展示云盘链接（购买后）
- 微信二维码、微信号复制、QQ 号展示
- 静态化页面（收录更快）
- 自动处理 Meta / Keywords
- 页面性能优化：预渲染、预抓取

### 2）管理后台系统

支持以下功能：

- 用户管理（注册、禁用、角色权限）
- 资源管理（标题、分类、标签、云盘链接、封面）
- 批量导入（Excel / CSV）
- 联系方式管理（微信二维码、微信号、QQ）
- 审计日志查看（登录 IP、访问记录）
- SEO 管理（sitemap、推送）
- 性能看板入口（Grafana）
- 系统配置（日志开关、监控开关）

### （3）后端（FastAPI）

使用企业级规范架构：

- 使用 JWT 登录
- 邮箱注册登录（预留社交账号扩展）
- 审计日志中间件（可开关）
- 性能追踪中间件（接口耗时）
- 静态化接口（生成 HTML 供前端展示）
- 所有开关通过环境变量控制

## 3. SEO 系统设计（最高优先级）

### 核心 SEO 功能

- 资源详情页自动静态化（实时写入）

- 分类、搜索结果可静态化

- 自动生成：

  - sitemap.xml
  - rss.xml
  - robots.txt

- URL 采用 SEO 友好的风格：

  ```
  /resource/python-web-scraping-guide
  ```

- 自动生成 Meta + Description

- 自动生成 JSON-LD（结构化产品数据）

- 自动提交到百度、360、Google（可配置）

------

## 4. 性能追踪与监控体系（增强版）

### （1）性能指标采集

FastAPI 中间件自动采集：

- 接口耗时（avg、P95、P99）
- QPS
- 状态码统计
- 异常日志统计
- SQL 耗时
- Redis 耗时
- 慢请求追踪（阈值可设定）

### （2）性能监控看板（Grafana）

监控内容：

- 请求耗时趋势
- 系统 CPU/MEM/磁盘/网络
- Nginx 访问量 / 状态码异常
- 数据库状态与慢查询
- Redis 命中率与连接数

### （3）监控开关配置（环境变量）

```
MONITOR_PERFORMANCE=true
MONITOR_AUDIT=true
MONITOR_API_LOG=true
MONITOR_SYSTEM_METRICS=true
```

------

## 5. 审计系统（安全合规）

### 审计内容：

- 登录真实 IP
- 访问商品记录（时间 / 商品 ID）
- 管理员操作行为（新增/修改/删除）
- 异常登录（可扩展邮件通知）

### 开关控制

```
AUDIT_LOG_ENABLE=true
```

------

## 6. 日志系统（结构化可控）

### 日志分类

- access.log（访问日志）
- error.log（系统错误）
- audit.log（审计日志）
- performance.log（性能日志）

### 日志输出方式

- 控制台输出（开发）
- 文件输出（生产）
- 支持接入：
  - ELK（Elasticsearch + Kibana）
  - Loki + Promtail

### 日志开关配置

```
LOG_ACCESS=true
LOG_ERROR=true
LOG_PERFORMANCE=true
LOG_AUDIT=true
```

------

## 7. 联系方式模块（可配置）

后台可配置并在前端展示：

- 微信二维码（上传或自动生成）
- 可复制微信号
- 可跳转 QQ
- Telegram、邮箱等渠道（预留扩展）
- 展示样式可配置（卡片 / 侧边栏 / 弹窗）

------

## 8. 部署架构（容器化）

使用 Docker Compose / Kubernetes 部署：

```
frontend (SSR)
admin-dashboard
fastapi-backend
mysql/postgres
redis
nginx
prometheus
grafana
elasticsearch / loki / kibana
```

支持：

- 自动 HTTPS（Let's Encrypt）
- 容器健康检查
- 滚动更新
- 自动备份数据库

------

## 9. 未来扩展能力（面向未来）

- AI 自动生成商品介绍 / SEO 信息
- AI 标签 & 分类自动化
- 私有资源托管（不依赖云盘）
- 向量搜索（相似资源推荐）
- 多商家入驻
- 订阅制（每月会员）
- 推广返佣体系
- 移动端 APP