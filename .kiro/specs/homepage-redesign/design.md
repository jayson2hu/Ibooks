# 设计文档

## 概述

本设计文档描述了资源市场主页重新设计的技术实现方案。重新设计将采用现代化的UI/UX设计原则，使用React、Next.js和Tailwind CSS构建响应式、高性能的用户界面。设计重点包括：

- 视觉吸引力的英雄区，采用动态渐变和动画效果
- 增强的搜索体验，包含实时反馈和流畅的交互
- 精美的资源卡片设计，支持悬停效果和图片优化
- 交互式分类筛选系统，提供即时的视觉反馈
- 优雅的加载状态，使用骨架屏提升感知性能
- 响应式布局，完美适配桌面、平板和移动设备
- 流畅的动画系统，提升整体交互体验

## 架构

### 技术栈

- **前端框架**: Next.js 14 (App Router)
- **UI库**: React 18
- **样式方案**: Tailwind CSS 3.x
- **动画库**: Framer Motion (用于复杂动画)
- **图标**: Heroicons / Lucide React
- **类型系统**: TypeScript

### 组件架构

```
HomePage (page.tsx)
├── HeroSection
│   ├── AnimatedBackground
│   ├── HeroContent
│   │   ├── Title (with fade-in animation)
│   │   ├── Subtitle
│   │   └── EnhancedSearchBar
│   │       ├── SearchInput
│   │       ├── CategoryDropdown
│   │       └── SearchButton
├── FeaturedResourcesSection
│   ├── SectionHeader
│   │   ├── Title (with decorative bar)
│   │   └── CategoryTabs
│   ├── ResourceGrid
│   │   └── ResourceCard[] (with hover effects)
│   └── LoadMoreButton
└── FeaturesSection
    └── FeatureCard[] (with scroll animations)
```

### 状态管理

使用React Hooks进行本地状态管理：
- `useState`: 管理搜索查询、活动标签、加载状态
- `useEffect`: 处理数据获取和副作用
- `useRouter`: Next.js路由导航
- 自定义Hook: `useIntersectionObserver` (滚动动画触发)

## 组件和接口

### HeroSection 组件

**职责**: 展示主页顶部的英雄区，包含标题、副标题和搜索功能

**Props**:
```typescript
interface HeroSectionProps {
  title?: string;
  subtitle?: string;
  onSearch?: (query: string, scope: string) => void;
}
```

**特性**:
- 动态渐变背景（使用CSS渐变或SVG）
- 淡入动画（使用Framer Motion或CSS动画）
- 响应式布局（移动端调整间距和字体大小）

### EnhancedSearchBar 组件

**职责**: 提供增强的搜索输入体验

**Props**:
```typescript
interface EnhancedSearchBarProps {
  placeholder?: string;
  onSubmit: (query: string, scope: string) => void;
  categories: Array<{ value: string; label: string; icon?: React.ReactNode }>;
}
```

**状态**:
```typescript
interface SearchBarState {
  query: string;
  scope: string;
  isFocused: boolean;
  isLoading: boolean;
}
```

**交互**:
- 焦点状态：边框颜色变化、轻微放大（transform: scale(1.02)）
- 悬停状态：阴影增强
- 加载状态：按钮显示旋转图标

### ResourceCard 组件

**职责**: 展示单个资源的信息卡片

**Props**:
```typescript
interface ResourceCardProps {
  resource: {
    id: number;
    title: string;
    description: string;
    slug: string;
    resource_type: string;
    price: number;
    is_free: boolean;
    thumbnail_url?: string;
    created_at?: string;
  };
  onHover?: (id: number) => void;
}
```

**样式特性**:
- 基础样式：圆角(rounded-xl)、阴影(shadow-md)、白色背景
- 悬停效果：
  - 卡片上浮：`transform: translateY(-8px)`
  - 阴影增强：`shadow-md → shadow-2xl`
  - 图片放大：`transform: scale(1.05)`
- 过渡时间：300ms，缓动函数：cubic-bezier(0.4, 0, 0.2, 1)

### CategoryTabs 组件

**职责**: 提供分类筛选标签

**Props**:
```typescript
interface CategoryTabsProps {
  tabs: Array<{ id: string; label: string; icon?: React.ReactNode }>;
  activeTab: string;
  onChange: (tabId: string) => void;
}
```

**交互**:
- 活动标签：蓝色背景、白色文字
- 非活动标签：白色背景、灰色文字
- 悬停效果：背景颜色轻微变化
- 切换动画：颜色过渡200ms

### SkeletonLoader 组件

**职责**: 在内容加载时显示占位符

**Props**:
```typescript
interface SkeletonLoaderProps {
  type: 'card' | 'text' | 'image';
  count?: number;
}
```

**动画**:
- 脉动效果：使用CSS关键帧动画
```css
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

### FeatureCard 组件

**职责**: 展示网站特色功能

**Props**:
```typescript
interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
}
```

**动画**:
- 滚动触发：使用Intersection Observer API
- 淡入效果：opacity 0 → 1，translateY(20px) → 0
- 悬停效果：轻微放大(scale: 1.05)

## 数据模型

### Resource 接口

```typescript
interface Resource {
  id: number;
  title: string;
  description: string;
  slug: string;
  resource_type: string;
  price: number;
  is_free: boolean;
  thumbnail_url?: string;
  created_at?: string;
  updated_at?: string;
  is_featured?: boolean;
  likes_count?: number;
}
```

### SearchParams 接口

```typescript
interface SearchParams {
  query: string;
  scope: 'all' | 'course' | 'product' | 'cert' | 'resource';
  page?: number;
  page_size?: number;
}
```

### CategoryTab 接口

```typescript
interface CategoryTab {
  id: string;
  label: string;
  icon?: React.ReactNode;
  color?: string;
}
```

## 正确性
属性

*属性是指在系统的所有有效执行中都应该成立的特征或行为——本质上是关于系统应该做什么的形式化陈述。属性充当人类可读规范和机器可验证正确性保证之间的桥梁。*

### 属性 1: 资源卡片样式一致性

*对于任意*资源卡片，当它在页面上渲染时，都应该应用圆角、阴影和边框样式
**验证: 需求 3.1**

### 属性 2: 资源卡片悬停效果

*对于任意*资源卡片，当用户悬停时，都应该显示上浮动画和阴影增强效果
**验证: 需求 3.2**

### 属性 3: 缩略图悬停放大

*对于任意*包含缩略图的资源卡片，当用户悬停时，图片都应该显示放大效果
**验证: 需求 3.3**

### 属性 4: 价格显示样式

*对于任意*包含价格信息的资源卡片，价格都应该使用醒目的颜色和样式显示
**验证: 需求 3.4**

### 属性 5: 卡片网格间距

*对于任意*数量的资源卡片，当它们在网格中排列时，卡片之间都应该有适当的间距和对齐
**验证: 需求 3.5**

### 属性 6: 分类标签状态样式

*对于任意*分类标签集合，活动标签和非活动标签都应该有明显不同的视觉样式
**验证: 需求 4.1**

### 属性 7: 标签点击过渡

*对于任意*分类标签，当用户点击时，都应该显示平滑的颜色过渡动画
**验证: 需求 4.2**

### 属性 8: 标签切换动画

*对于任意*分类标签切换操作，资源列表都应该使用淡入淡出动画更新
**验证: 需求 4.3**

### 属性 9: 非活动标签悬停

*对于任意*非活动的分类标签，当用户悬停时，都应该显示背景颜色变化
**验证: 需求 4.5**

### 属性 10: 区块标题装饰

*对于任意*内容区块标题，都应该包含装饰性元素（如彩色竖线或图标）
**验证: 需求 6.2**

### 属性 11: 区块间距

*对于任意*相邻的内容区块，它们之间都应该有适当的间距
**验证: 需求 6.4**

### 属性 12: 交互动画时长

*对于任意*交互元素，当用户与其互动时，过渡动画的持续时间都应该在150-300毫秒之间
**验证: 需求 7.1**

### 属性 13: 元素入场动画

*对于任意*首次出现的页面元素，都应该使用淡入或滑入动画
**验证: 需求 7.2**

### 属性 14: 可点击元素反馈

*对于任意*可点击元素，当用户悬停时，都应该显示即时的视觉反馈
**验证: 需求 7.3**

### 属性 15: 动画缓动函数

*对于任意*动画效果，都应该使用缓动函数确保动画自然流畅
**验证: 需求 7.4**

### 属性 16: 交互元素对比度

*对于任意*交互元素，都应该使用高对比度的颜色确保可访问性
**验证: 需求 8.2**

### 属性 17: 文本对比度标准

*对于任意*显示在彩色背景上的文本，对比度都应该符合WCAG AA标准（至少4.5:1）
**验证: 需求 8.4**

### 属性 18: 状态颜色差异

*对于任意*具有多个状态的元素，不同状态都应该使用不同的颜色清晰表示
**验证: 需求 8.5**

### 属性 19: 触摸目标尺寸

*对于任意*可交互元素，在触摸设备上的尺寸都应该至少为44x44像素
**验证: 需求 9.2**

### 属性 20: 移动端图片优化

*对于任意*图片，在移动设备上都应该使用适当的尺寸优化加载速度
**验证: 需求 9.5**

### 属性 21: 特色功能元素完整性

*对于任意*特色功能项，都应该包含图标、标题和描述三个元素
**验证: 需求 10.1**

### 属性 22: 特色功能悬停效果

*对于任意*特色功能项，当用户悬停时，都应该显示轻微的放大或高亮效果
**验证: 需求 10.3**

### 属性 23: 特色图标一致性

*对于任意*特色功能图标，都应该使用一致的视觉风格和尺寸
**验证: 需求 10.5**

## 错误处理

### 数据加载失败

- 当API请求失败时，显示友好的错误消息
- 提供重试按钮
- 保持页面布局稳定，不出现布局偏移

### 图片加载失败

- 使用占位符图标替代失败的缩略图
- 保持卡片布局完整性
- 不影响其他卡片的显示

### 搜索错误

- 验证搜索输入，防止空查询
- 处理特殊字符和长查询
- 在导航失败时显示错误提示

### 响应式断点处理

- 优雅降级：在不支持的浏览器中提供基础功能
- 使用CSS媒体查询处理不同屏幕尺寸
- 确保在极小屏幕上内容仍然可访问

## 测试策略

### 单元测试

使用Jest和React Testing Library进行组件单元测试：

1. **组件渲染测试**
   - 验证组件正确渲染
   - 检查必需的props
   - 测试条件渲染逻辑

2. **交互测试**
   - 测试按钮点击事件
   - 验证表单提交
   - 测试悬停和焦点状态

3. **状态管理测试**
   - 测试useState hooks
   - 验证状态更新逻辑
   - 测试副作用（useEffect）

### 属性测试

使用fast-check库进行属性测试，验证通用属性：

1. **样式属性测试**
   - 生成随机资源数据，验证所有卡片都有必需的样式类
   - 测试不同数量的卡片，验证网格间距一致性
   - 生成随机标签数据，验证活动/非活动状态样式差异

2. **可访问性属性测试**
   - 生成随机颜色组合，验证对比度符合WCAG标准
   - 测试所有交互元素，验证触摸目标尺寸
   - 验证所有动画时长在规定范围内

3. **响应式属性测试**
   - 在不同视口尺寸下测试布局
   - 验证移动端图片优化
   - 测试触摸目标尺寸

**配置要求**:
- 每个属性测试至少运行100次迭代
- 使用明确的注释标记每个属性测试对应的设计文档属性编号
- 格式: `// Feature: homepage-redesign, Property X: [property description]`

### 视觉回归测试

使用Playwright或Chromatic进行视觉测试：

1. 捕获关键页面状态的截图
2. 比较UI变更前后的差异
3. 测试不同浏览器和设备的渲染

### 端到端测试

使用Playwright测试完整用户流程：

1. 主页加载和导航
2. 搜索功能完整流程
3. 分类筛选和资源浏览
4. 响应式布局切换

### 性能测试

1. 使用Lighthouse测试页面性能指标
2. 监控首次内容绘制（FCP）和最大内容绘制（LCP）
3. 测试动画性能，确保60fps
4. 验证图片优化和懒加载

## 实现注意事项

### 性能优化

1. **图片优化**
   - 使用Next.js Image组件自动优化
   - 实现懒加载
   - 提供多种尺寸的响应式图片

2. **代码分割**
   - 使用动态导入延迟加载非关键组件
   - 分离第三方库（如Framer Motion）

3. **CSS优化**
   - 使用Tailwind的JIT模式减少CSS体积
   - 避免不必要的CSS-in-JS运行时开销

### 可访问性

1. **语义化HTML**
   - 使用正确的HTML标签（header, nav, main, section）
   - 为交互元素提供适当的ARIA标签

2. **键盘导航**
   - 确保所有交互元素可通过键盘访问
   - 提供清晰的焦点指示器

3. **屏幕阅读器支持**
   - 为图片提供alt文本
   - 使用aria-label描述复杂交互

### 浏览器兼容性

- 支持最新两个版本的主流浏览器（Chrome, Firefox, Safari, Edge）
- 使用CSS前缀处理实验性特性
- 提供polyfills支持旧版浏览器

### 开发工具

- **ESLint**: 代码质量检查
- **Prettier**: 代码格式化
- **TypeScript**: 类型安全
- **Storybook**: 组件开发和文档（可选）
