# VintageWisdom - UI 设计规范

> 基于 ux-kit 生成的专业设计系统

---

## 1. 设计概览

### 产品定位
- **类型**: 个人知识管理 + 决策支持系统
- **风格**: 专业、深色主题、数据密集型仪表板
- **氛围**: 沉稳、专注、高效

### 设计原则
1. **深色优先** - 长时间使用的工具，深色模式减少眼疲劳
2. **信息密度** - 类似 BI 仪表板，最大化信息展示
3. **即时反馈** - 所有操作有清晰的视觉反馈
4. **键盘友好** - 支持快捷键，极客用户友好

---

## 2. 色彩系统

### 主色调（深色主题）

```css
/* 背景层级 */
--bg-primary: #0F172A;      /* 主背景 - slate-900 */
--bg-secondary: #1E293B;    /* 卡片背景 - slate-800 */
--bg-tertiary: #334155;     /* 悬浮背景 - slate-700 */
--bg-elevated: #475569;     /* 高亮背景 - slate-600 */

/* 文字颜色 */
--text-primary: #F8FAFC;    /* 主文字 - slate-50 */
--text-secondary: #94A3B8;  /* 次要文字 - slate-400 */
--text-muted: #64748B;      /* 辅助文字 - slate-500 */
--text-disabled: #475569;   /* 禁用文字 - slate-600 */

/* 强调色 */
--accent-primary: #6366F1;   /* 主强调 - indigo-500 */
--accent-secondary: #818CF8; /* 次强调 - indigo-400 */
--accent-hover: #4F46E5;     /* 悬浮 - indigo-600 */

/* 功能色 */
--success: #22C55E;          /* 成功 - green-500 */
--warning: #F59E0B;          /* 警告 - amber-500 */
--error: #EF4444;            /* 错误 - red-500 */
--info: #3B82F6;             /* 信息 - blue-500 */
```

### 语义化颜色

| 用途 | 颜色 | 说明 |
|------|------|------|
| 成功案例 | `#22C55E` | 决策成功标记 |
| 失败案例 | `#EF4444` | 决策失败标记 |
| 警告/风险 | `#F59E0B` | 风险提醒 |
| 中性/混合 | `#64748B` | 混合结果 |
| AI 生成内容 | `#A855F7` | 紫色标识 AI 内容 |
| 用户输入 | `#3B82F6` | 蓝色标识用户内容 |

---

## 3. 字体系统

### 字体选择

```css
/* 主字体 */
--font-heading: 'Poppins', sans-serif;    /* 标题 */
--font-body: 'Inter', -apple-system, sans-serif;  /* 正文 */
--font-mono: 'JetBrains Mono', monospace; /* 代码/数据 */

/* Google Fonts 导入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Poppins:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
```

### 字号规范

| 层级 | 大小 | 字重 | 用途 |
|------|------|------|------|
| H1 | 32px | 600 | 页面标题 |
| H2 | 24px | 600 | 区块标题 |
| H3 | 20px | 500 | 卡片标题 |
| H4 | 16px | 500 | 小标题 |
| Body | 14px | 400 | 正文内容 |
| Small | 12px | 400 | 辅助信息 |
| Mono | 13px | 500 | 代码/数据 |

### 行高

```css
--leading-tight: 1.25;   /* 标题 */
--leading-normal: 1.5;   /* 正文 */
--leading-relaxed: 1.75; /* 长文本 */
```

---

## 4. 布局系统

### 整体布局

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (240px)    │  Main Content Area                 │
│                     │                                    │
│  ┌───────────────┐  │  ┌─────────────────────────────┐   │
│  │ Logo          │  │  │ Header (56px)               │   │
│  ├───────────────┤  │  ├─────────────────────────────┤   │
│  │ Navigation    │  │  │                             │   │
│  │ - Dashboard   │  │  │  Content Area               │   │
│  │ - Cases       │  │  │  (scrollable)               │   │
│  │ - Search      │  │  │                             │   │
│  │ - Analytics   │  │  │                             │   │
│  │ - Settings    │  │  │                             │   │
│  ├───────────────┤  │  │                             │   │
│  │ Plugin Panel  │  │  │                             │   │
│  │ (collapsible) │  │  │                             │   │
│  └───────────────┘  │  └─────────────────────────────┘   │
│                     │                                    │
└─────────────────────┴────────────────────────────────────┘
```

### 间距规范

```css
/* 基础间距 */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;

/* 布局间距 */
--sidebar-width: 240px;
--header-height: 56px;
--content-padding: 24px;
--card-gap: 16px;
```

### 网格系统

```css
/* 12列网格 */
--grid-columns: 12;
--grid-gap: 16px;

/* 响应式断点 */
--breakpoint-sm: 640px;   /* 移动端 */
--breakpoint-md: 768px;   /* 平板 */
--breakpoint-lg: 1024px;  /* 桌面 */
--breakpoint-xl: 1280px;  /* 大屏 */
```

---

## 5. 组件规范

### 5.1 按钮

```css
/* 主按钮 */
.btn-primary {
  background: var(--accent-primary);
  color: white;
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 150ms ease;
}
.btn-primary:hover {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

/* 次按钮 */
.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
  border: 1px solid var(--bg-elevated);
}

/* 幽灵按钮 */
.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
}
.btn-ghost:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

/* 图标按钮 */
.btn-icon {
  width: 36px;
  height: 36px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
}
```

### 5.2 卡片

```css
/* 基础卡片 */
.card {
  background: var(--bg-secondary);
  border: 1px solid var(--bg-tertiary);
  border-radius: 8px;
  padding: 16px;
}

/* 可悬浮卡片 */
.card-hover {
  transition: all 200ms ease;
  cursor: pointer;
}
.card-hover:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

/* 案例卡片 */
.case-card {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
}

/* 数据卡片 */
.stat-card {
  text-align: center;
  padding: 20px;
}
.stat-card .value {
  font-size: 32px;
  font-weight: 600;
  color: var(--accent-primary);
}
.stat-card .label {
  font-size: 12px;
  color: var(--text-muted);
  text-transform: uppercase;
}
```

### 5.3 输入框

```css
/* 文本输入 */
.input {
  background: var(--bg-primary);
  border: 1px solid var(--bg-tertiary);
  border-radius: 6px;
  padding: 8px 12px;
  color: var(--text-primary);
  transition: border-color 150ms ease;
}
.input:focus {
  outline: none;
  border-color: var(--accent-primary);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}
.input::placeholder {
  color: var(--text-muted);
}

/* 搜索框 */
.search-input {
  padding-left: 40px;
  background-image: url('search-icon.svg');
  background-repeat: no-repeat;
  background-position: 12px center;
}
```

### 5.4 标签/徽章

```css
/* 基础标签 */
.badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

/* 领域标签 */
.badge-domain-tech { background: rgba(59, 130, 246, 0.2); color: #60A5FA; }
.badge-domain-business { background: rgba(245, 158, 11, 0.2); color: #FBBF24; }
.badge-domain-political { background: rgba(239, 68, 68, 0.2); color: #F87171; }

/* 结果标签 */
.badge-success { background: rgba(34, 197, 94, 0.2); color: #4ADE80; }
.badge-failure { background: rgba(239, 68, 68, 0.2); color: #F87171; }
.badge-mixed { background: rgba(100, 116, 139, 0.2); color: #94A3B8; }
```

### 5.5 导航

```css
/* 侧边栏导航 */
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  border-radius: 6px;
  color: var(--text-secondary);
  transition: all 150ms ease;
}
.nav-item:hover {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}
.nav-item.active {
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-primary);
}

/* 标签页 */
.tab {
  padding: 8px 16px;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  transition: all 150ms ease;
}
.tab:hover {
  color: var(--text-primary);
}
.tab.active {
  color: var(--accent-primary);
  border-bottom-color: var(--accent-primary);
}
```

---

## 6. 特效与动画

### 过渡效果

```css
/* 标准过渡 */
--transition-fast: 150ms ease;
--transition-normal: 200ms ease;
--transition-slow: 300ms ease;

/* 常用过渡 */
.transition-colors { transition: color, background-color, border-color var(--transition-fast); }
.transition-transform { transition: transform var(--transition-normal); }
.transition-shadow { transition: box-shadow var(--transition-normal); }
.transition-all { transition: all var(--transition-normal); }
```

### 悬浮效果

```css
/* 卡片悬浮 */
.hover-lift:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

/* 按钮悬浮 */
.btn:hover {
  transform: translateY(-1px);
}

/* 链接悬浮 */
a:hover {
  color: var(--accent-primary);
}
```

### 焦点状态

```css
/* 焦点环 */
.focus-ring:focus {
  outline: none;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.3);
}

/* 键盘导航焦点 */
.focus-visible:focus-visible {
  outline: 2px solid var(--accent-primary);
  outline-offset: 2px;
}
```

### 加载状态

```css
/* 骨架屏 */
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-tertiary) 25%,
    var(--bg-elevated) 50%,
    var(--bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}
@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* 脉冲指示器 */
.pulse {
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
```

---

## 7. 页面设计

### 7.1 主仪表板 (Dashboard)

```
┌────────────────────────────────────────────────────────────┐
│  VintageWisdom              [Search...]    [+]    [⚙️]     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ 总案例数    │ │ 本月新增    │ │ 待评估决策  │          │
│  │   128       │ │    12       │ │     3       │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
│                                                            │
│  最近活动                                    [查看全部]    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [决策] 是否接受新工作 offer                         │   │
│  │ 2小时前  •  匹配 3 个相似案例                       │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ [案例] 添加了 "某SaaS公司重构失败"                  │   │
│  │ 昨天  •  Tech 领域                                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  领域分布                              决策成功率趋势      │
│  ┌─────────────────┐                  ┌──────────────┐    │
│  │   [饼图]        │                  │  [折线图]    │    │
│  │                 │                  │              │    │
│  │  Tech 45%       │                  │   趋势上升   │    │
│  │  Business 35%   │                  │              │    │
│  │  Political 20%  │                  │              │    │
│  └─────────────────┘                  └──────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.2 案例库页面 (Cases)

```
┌────────────────────────────────────────────────────────────┐
│  案例库                                          [+ 添加]  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  [全部] [Tech] [Business] [Political]    [🔍 搜索案例...]  │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📌 柯达数字化转型失败                    [Tech] [失败]│   │
│  │ 技术颠覆期，保护现金牛=慢性自杀                      │   │
│  │ 2012  •  影响度: 9/10  •  3 个相关案例              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📌 某SaaS公司重构成功                    [Tech] [成功]│   │
│  │ 采用绞杀者模式，渐进式替换旧系统                     │   │
│  │ 2019  •  影响度: 7/10  •  5 个相关案例              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📌 王安石变法                            [Political] │   │
│  │ 理想主义改革 vs 既得利益集团阻力                     │   │
│  │ 1069  •  影响度: 10/10  •  2 个相关案例             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.3 决策查询页面 (Query)

```
┌────────────────────────────────────────────────────────────┐
│  决策助手                                                  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  描述你当前的决策情境：                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 我是一个A轮公司CTO，技术债很重，想重构但业务压力大  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  [开始分析]  [🎤 语音输入]                                 │
│                                                            │
│  ═══════════════════════════════════════════════════════   │
│                                                            │
│  🎯 分析结果                                               │
│                                                            │
│  【高度匹配案例】                                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. 某SaaS公司重构失败 (2021)              相似度 92%│   │
│  │    关键差异: 你处于A轮，案例为B轮                    │   │
│  │    [查看详情] [对比分析]                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  【风险推演】                                              │
│  若立即全面重构：                                          │
│  • 3个月内：开发停滞，客户投诉上升    ████████░░ 80%      │
│  • 6个月内：核心员工流失，融资受阻    ██████░░░░ 60%      │
│  • 12个月内：竞品超越，市场份额下降   █████░░░░░ 50%      │
│                                                            │
│  【建议路径】                                              │
│  方案A: 绞杀者策略（推荐）                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☐ 划定"冻结区"，旧代码只修不增                      │   │
│  │ ☐ 新业务在新架构上跑通MVP                           │   │
│  │ ☐ 团队有20%资源可投入重构                           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  [🎯 启动红队对抗]  [🔮 未来你对话]  [📊 压力测试]        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 7.4 案例详情页 (Case Detail)

```
┌────────────────────────────────────────────────────────────┐
│  ← 返回案例库                                              │
│                                                            │
│  📌 柯达数字化转型失败                          [编辑] [⋮] │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                            │
│  [Tech] [Business] [失败] [影响度: 9/10]                   │
│                                                            │
│  2012年  •  美国  •  影像/胶卷行业                         │
│                                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 决策节点                                             │   │
│  │ 是否全力投入数码技术                                 │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 采取行动                                             │   │
│  │ 犹豫不决，试图保护胶卷利润                           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 结果                                                 │   │
│  │ 破产重组  •  历时10年  •  市值从300亿跌至0           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  因果链                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                                                     │   │
│  │  依赖高利润传统业务                                 │   │
│  │       ↓                                             │   │
│  │  低估新技术威胁                                     │   │
│  │       ↓                                             │   │
│  │  转型投入不足且时机过晚                             │   │
│  │       ↓                                             │   │
│  │  组织惯性阻碍变革                                   │   │
│  │       ↓                                             │   │
│  │  现金流断裂 ─────────────────→ 破产重组             │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  核心教训                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ "技术颠覆期，保护现金牛=慢性自杀"                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  检查清单                                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ☑ 传统业务占比是否>60%?                             │   │
│  │ ☐ 是否制定了3年内降至<40%的计划?                    │   │
│  │ ☐ 新技术增长率连续4季度>50%?                        │   │
│  │ ☐ 是否投入>30%研发资源?                             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                            │
│  相似案例                              跨领域类比          │
│  ┌─────────────────┐                  ┌─────────────────┐  │
│  │ 诺基亚智能手机  │                  │ 某国休克疗法    │  │
│  │ Blockbuster    │                  │ 改革            │  │
│  └─────────────────┘                  └─────────────────┘  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 8. 交互设计

### 8.1 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl/Cmd + K` | 打开搜索 |
| `Ctrl/Cmd + N` | 新建案例 |
| `Ctrl/Cmd + Q` | 快速决策查询 |
| `Ctrl/Cmd + 1-9` | 切换导航项 |
| `Esc` | 关闭弹窗/返回 |
| `?` | 显示快捷键帮助 |

### 8.2 状态反馈

```
操作成功: 绿色 toast，2秒自动消失
操作失败: 红色 toast，需手动关闭或5秒后消失
加载中:   骨架屏 + 加载指示器
空状态:   插画 + 说明文字 + 操作按钮
```

### 8.3 数据可视化

```css
/* 图表颜色 */
--chart-primary: #6366F1;
--chart-secondary: #818CF8;
--chart-success: #22C55E;
--chart-warning: #F59E0B;
--chart-error: #EF4444;
--chart-neutral: #64748B;

/* 图表网格 */
--chart-grid: rgba(148, 163, 184, 0.1);
--chart-text: var(--text-secondary);
```

---

## 9. 响应式设计

### 断点适配

| 断点 | 布局调整 |
|------|----------|
| < 768px | 侧边栏收起为图标，单列布局 |
| 768px - 1024px | 侧边栏收起，双列布局 |
| > 1024px | 完整侧边栏，多列布局 |

### 移动端适配

```css
/* 移动端侧边栏 */
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 60px;
    width: 100%;
    flex-direction: row;
  }
}
```

---

## 10. 无障碍设计

### 基础要求

- [ ] 所有交互元素支持键盘导航
- [ ] 焦点状态清晰可见
- [ ] 图片有 alt 文本
- [ ] 表单有关联 label
- [ ] 颜色不是唯一信息载体
- [ ] 支持 `prefers-reduced-motion`

### ARIA 标签

```html
<!-- 导航 -->
<nav aria-label="主导航">
  <a href="/" aria-current="page">首页</a>
</nav>

<!-- 按钮 -->
<button aria-label="关闭" aria-pressed="false">
  <svg><!-- 图标 --></svg>
</button>

<!-- 状态 -->
<span role="status" aria-live="polite">保存成功</span>
```

---

## 11. 实现检查清单

### 开发前
- [ ] 确认色彩对比度符合 WCAG AA
- [ ] 确认字体已正确导入
- [ ] 确认图标库已引入 (Lucide/Heroicons)

### 开发中
- [ ] 所有按钮有 `cursor-pointer`
- [ ] 所有悬浮有平滑过渡 (150-300ms)
- [ ] 所有焦点状态可见
- [ ] 深色模式颜色正确

### 开发后
- [ ] 键盘导航测试
- [ ] 响应式布局测试
- [ ] 性能检查 (Lighthouse)
- [ ] 无障碍检查

---

*设计系统版本: 1.0*  
*基于 ux-kit 生成*  
*最后更新: 2026-03-15*
