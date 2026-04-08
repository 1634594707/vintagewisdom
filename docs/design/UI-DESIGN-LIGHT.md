# VintageWisdom UI 设计文档（浅色系）

## 1. 文档目标

本文档用于统一 VintageWisdom 前端界面的视觉方向、组件语言、页面布局和交互约束，采用浅色系设计风格。

## 2. 产品定位与界面气质

VintageWisdom 是一个面向"历史案例复用与个人决策支持"的工作台。界面应传达以下感受：

- 浅色、清晰、专业，像一个高效的知识管理系统
- 信息密度较高，但必须有明确层级，不能做成拥挤的数据墙
- 重点是帮助用户快速进入"查看案例 -> 发起查询 -> 理解图谱 -> 调整 AI 配置"的工作流
- 视觉语言要兼顾"知识工具"与"推理系统"气质

关键词：

- `Decision workspace`
- `Historical intelligence`
- `Dense but readable`
- `Light & clean`
- `Local-first AI`

## 3. 当前设计方向总览

采用现代浅色工作台风格，核心特征如下：

- 整体采用浅灰到白色的渐变背景
- 使用蓝紫色作为主要强调色，承担 CTA、焦点和关键状态提示
- 面板采用白色或浅灰背景，配合细腻阴影形成层次
- 卡片、侧边栏、顶部标题区都采用适中圆角，形成"专业工作台"视觉
- 通过字重、字号、留白、细边框来管理层级
- 保持清晰的视觉层次和良好的可读性

**定义为：浅色、高密度、知识分析型决策工作台。**

## 4. 视觉主题与氛围

### 4.1 整体基调

- 主背景使用浅色底，营造清爽专业感
- 页面追求清晰对比和良好可读性
- 主要视觉重心集中在面板、图谱画布、查询区、案例卡片
- 背景允许有少量微妙纹理，但只能作为氛围

### 4.2 风格参考落点

从参考库中，VintageWisdom 更接近以下混合方向：

- 借鉴 `Linear` 的清晰层级与高密度信息组织
- 借鉴 `Notion` 的文档式清晰结构与可读性优先原则
- 借鉴 `Airtable` 的工作台组件分区思路
- 借鉴现代 SaaS 产品的浅色专业风格

## 5. 色彩系统

### 5.1 背景与表面

```css
--bg-primary: #ffffff;
--bg-secondary: #f8f9fa;
--bg-tertiary: #f1f3f5;
--bg-elevated: #ffffff;
--panel-strong: rgba(255, 255, 255, 0.95);
--panel-soft: rgba(255, 255, 255, 0.85);
--panel-muted: rgba(248, 249, 250, 0.9);
```

### 5.2 文本

```css
--text-primary: #1a1a1a;
--text-secondary: #4a4a4a;
--text-muted: #6b7280;
--text-disabled: #9ca3af;
```

### 5.3 强调色

```css
--accent-primary: #6366f1;
--accent-secondary: #818cf8;
--accent-hover: #4f46e5;
--accent-glow: rgba(99, 102, 241, 0.15);
--accent-light: #eef2ff;
```

### 5.4 语义状态

```css
--success: #10b981;
--success-light: #d1fae5;
--warning: #f59e0b;
--warning-light: #fef3c7;
--error: #ef4444;
--error-light: #fee2e2;
--info: #3b82f6;
--info-light: #dbeafe;
```

### 5.5 边框与阴影

```css
--border-subtle: rgba(0, 0, 0, 0.08);
--border-medium: rgba(0, 0, 0, 0.12);
--border-strong: rgba(0, 0, 0, 0.18);
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.12);
```

### 5.6 用色原则

- 蓝紫强调色只用于主按钮、焦点、激活导航、关键数据高亮
- 成功/警告/错误只用于状态反馈，配合浅色背景使用
- 文本层级优先依赖明度差，而不是增加颜色数量
- 背景层级应通过白色、浅灰、阴影区分

## 6. 字体系统

### 6.1 字体角色

- 正文：现代无衬线，适合长时间阅读（Inter, SF Pro, -apple-system）
- 标题：比正文更有辨识度，字重更大
- 等宽：用于 case id、API 地址、快捷键信息（JetBrains Mono, Fira Code）

### 6.2 字体层级建议

| 角色 | 建议字号 | 字重 | 行高 | 用途 |
|------|----------|------|------|------|
| Hero Title | 36px-42px | 700 | 1.1 | 首页/核心页主标题 |
| Section Title | 24px-28px | 600 | 1.2 | 页面一级区块标题 |
| Card Title | 18px-20px | 600 | 1.3 | 卡片标题 |
| Body | 14px-16px | 400 | 1.6 | 常规正文 |
| Meta | 12px-13px | 500 | 1.5 | 次级说明、标签 |
| Eyebrow | 11px | 600 | 1.4 | 分区标签 |
| Mono Meta | 12px | 400 | 1.4 | id、路径 |

## 7. 间距、圆角与布局系统

### 7.1 间距基线

采用 8px 基础网格，并允许 4px 微调。

推荐节奏：

- 4px：微调、图标与文字间距
- 8px：最小内容间距
- 12px：紧凑组件内边距
- 16px：标准间距
- 20px：舒适卡片内间距
- 24px：模块分组间距
- 32px+：页面级留白

### 7.2 圆角体系

- `8px`：主按钮、输入框、小卡片
- `12px`：普通卡片、内容容器
- `16px`：页面级面板
- `999px`：徽标、状态 badge

### 7.3 页面骨架

桌面端推荐采用"三层工作台"结构：

1. 左侧主导航（可选）
2. 顶部标题与快捷操作区
3. 主内容区

## 8. 组件设计规范

### 8.1 按钮

#### 主按钮 `vw-btn-primary`

```css
background: linear-gradient(135deg, #6366f1, #818cf8);
color: #ffffff;
padding: 10px 20px;
border-radius: 8px;
font-weight: 600;
box-shadow: 0 2px 4px rgba(99, 102, 241, 0.2);
transition: all 0.2s;

&:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
}
```

#### 次按钮 `vw-btn-secondary`

```css
background: #ffffff;
color: #4a4a4a;
padding: 10px 20px;
border: 1px solid var(--border-medium);
border-radius: 8px;
font-weight: 500;
transition: all 0.2s;

&:hover {
  border-color: var(--accent-primary);
  color: var(--accent-primary);
}
```

### 8.2 卡片

#### 面板卡片 `vw-panel`

```css
background: #ffffff;
border: 1px solid var(--border-subtle);
border-radius: 16px;
padding: 24px;
box-shadow: var(--shadow-md);
```

#### 普通卡片 `vw-card`

```css
background: #ffffff;
border: 1px solid var(--border-subtle);
border-radius: 12px;
padding: 16px;
box-shadow: var(--shadow-sm);
transition: all 0.2s;

&:hover {
  border-color: var(--accent-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}
```

### 8.3 输入类组件

```css
.vw-input {
  background: #ffffff;
  border: 1px solid var(--border-medium);
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text-primary);
  transition: all 0.2s;
  
  &:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  
  &::placeholder {
    color: var(--text-muted);
  }
}

.vw-textarea {
  background: #ffffff;
  border: 1px solid var(--border-medium);
  border-radius: 12px;
  padding: 14px;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  resize: vertical;
  min-height: 120px;
  
  &:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
}
```

### 8.4 Badge / 标签

```css
.vw-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

.vw-badge-accent {
  background: var(--accent-light);
  color: var(--accent-primary);
}

.vw-badge-success {
  background: var(--success-light);
  color: var(--success);
}

.vw-badge-warning {
  background: var(--warning-light);
  color: var(--warning);
}

.vw-badge-error {
  background: var(--error-light);
  color: var(--error);
}
```

### 8.5 导航

```css
.vw-nav-item {
  display: flex;
  align-items: center;
  padding: 10px 16px;
  border-radius: 8px;
  color: var(--text-secondary);
  font-weight: 500;
  transition: all 0.2s;
  
  &:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  &.active {
    background: var(--accent-light);
    color: var(--accent-primary);
  }
}
```

## 9. 页面级设计要求

### 9.1 Dashboard 首页

- 清晰的欢迎区域
- KPI 指标卡片（白色背景，细边框）
- 最近案例列表
- 领域分布可视化
- 快速操作入口

### 9.2 Cases 页面

- 顶部搜索和筛选栏
- 案例卡片网格或列表
- 每个卡片包含：领域标签、标题、摘要、元数据
- hover 效果：边框高亮、轻微上浮

### 9.3 Query 页面

三段式布局：

1. **输入区**：大文本框，示例提示
2. **结果区**：双栏布局
   - 左：相关案例列表
   - 右：AI 推理和建议

### 9.4 Import 页面

- 文件上传区（虚线边框）
- 导入选项配置
- 进度条和状态反馈
- 结果摘要

### 9.5 Graph 页面

- 大画布区域（浅灰背景）
- 侧边控制面板
- 节点和边使用清晰的颜色区分
- 工具栏：缩放、筛选、布局切换

### 9.6 Settings 页面

- 分组表单布局
- AI 配置区
- 状态指示器
- 保存按钮

## 10. 图谱可视化规范

### 10.1 视觉原则

- 背景：浅灰色 (#f8f9fa)
- 节点：白色背景，彩色边框
- 边：浅灰色细线
- 标签：深色文字，白色背景

### 10.2 节点设计

```css
.graph-node {
  background: #ffffff;
  border: 2px solid var(--accent-primary);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  
  &.domain {
    border-color: var(--accent-primary);
  }
  
  &.case {
    border-color: var(--info);
  }
  
  &.cluster {
    border-color: var(--success);
  }
  
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: scale(1.05);
  }
}
```

### 10.3 边与关系

```css
.graph-edge {
  stroke: rgba(0, 0, 0, 0.15);
  stroke-width: 1.5px;
  
  &.similar {
    stroke: var(--accent-primary);
    stroke-dasharray: 4 2;
  }
  
  &:hover {
    stroke: var(--accent-primary);
    stroke-width: 2px;
  }
}
```

## 11. 动效原则

允许：

- hover 渐变（150ms）
- 面板轻微浮起（200ms）
- modal / drawer 滑入（250ms）
- 加载旋转反馈
- 结果区渐进显现（300ms）

禁止：

- 连续抖动
- 大范围元素飞入
- 高频闪烁

## 12. 响应式规范

### 12.1 断点建议

- Mobile: `< 768px`
- Tablet: `768px - 1279px`
- Desktop: `>= 1280px`

### 12.2 响应式策略

桌面端：
- 保持左侧导航 + 顶部头部 + 多栏内容

平板端：
- 缩窄侧边栏
- 双栏转为上下堆叠

移动端：
- 导航隐藏为顶部横向导航
- 所有点击区域高度 ≥ 44px
- 单列流式布局

## 13. 可访问性要求

- 所有交互元素要有清晰 focus 状态
- 文本与背景对比度 ≥ 4.5:1
- 不能只用颜色表达状态
- 图标按钮必须有文字或 aria 标签
- 加载状态要有文案提示
- 错误信息要清晰友好

## 14. 给 AI 的页面生成提示词

```text
为 VintageWisdom 设计一个浅色、清晰、专业的 Next.js 决策工作台界面。产品是一个"历史案例复用与个人决策支持系统"。

请遵循以下要求：

1. 整体风格是浅色知识分析工作台，专业清爽。
2. 主背景使用白色到浅灰渐变。
3. 主视觉 token：
   - 背景：#ffffff, #f8f9fa, #f1f3f5
   - 文字：#1a1a1a, #4a4a4a, #6b7280
   - 强调色：#6366f1, #818cf8
   - 边框：rgba(0,0,0,0.08)
4. 页面结构采用顶部导航 + 主内容区的工作台布局。
5. 卡片使用 12px-16px 圆角、白色背景、细边框和柔和阴影。
6. 主按钮使用蓝紫渐变，次按钮使用白色背景和细边框。
7. 组件重点包括：
   - 案例列表卡片
   - 查询输入区与结果区
   - KPI 统计卡片
   - 导入任务状态卡片
   - AI 设置面板
   - 知识图谱画布容器
8. 查询结果页使用双栏：左侧相关案例，右侧 AI reasoning。
9. 图谱区域使用浅灰背景，白色节点，彩色边框。
10. 动效仅限轻微 hover、淡入、滑入。
11. 设计需兼容桌面、平板和移动端。
12. 保持清晰的视觉层次和良好的可读性。
```

---

文档版本：`3.0 (Light Theme)`  
最后更新：`2026-04-08`
