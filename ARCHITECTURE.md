# VintageWisdom - 可扩展架构设计

## 核心设计思想

```
┌─────────────────────────────────────────┐
│           核心框架 (Core)                │  ← 稳定，少变动
│  - 事件总线                              │
│  - 配置管理                              │
│  - 数据访问层                            │
│  - 插件管理器                            │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
┌─────────┐   ┌─────────┐   ┌─────────┐
│ 内置模块 │   │ 插件目录 │   │ 用户扩展 │
│(检索/存储)│   │(AI/可视化)│   │(自定义) │
└─────────┘   └─────────┘   └─────────┘
```

**关键原则：**
1. **核心框架保持精简** - 只包含最基础的功能
2. **功能以插件形式存在** - 每个功能一个目录，独立开发
3. **约定优于配置** - 插件按约定自动注册
4. **渐进式开发** - 先实现基础，再逐步添加高级功能

---

## 推荐的项目结构

```
vintagewisdom/
├── README.md
├── DESIGN.md
├── STRUCTURE.md
├── ARCHITECTURE.md          # 本文档
│
├── pyproject.toml
├── requirements/
│   ├── base.txt            # 核心依赖
│   ├── dev.txt             # 开发依赖
│   └── plugins/            # 各插件依赖
│       ├── ai.txt
│       ├── viz.txt
│       └── web.txt
│
├── src/
│   └── vintagewisdom/
│       ├── __init__.py
│       ├── __main__.py
│       │
│       ├── core/           # ========== 核心框架 ==========
│       │   ├── __init__.py
│       │   ├── app.py      # 应用主类，协调各组件
│       │   ├── config.py   # 配置管理
│       │   ├── events.py   # 事件总线（关键！）
│       │   ├── registry.py # 插件注册表
│       │   └── storage.py  # 统一数据访问接口
│       │
│       ├── models/         # ========== 数据模型 ==========
│       │   ├── __init__.py
│       │   ├── base.py     # 基础模型
│       │   ├── case.py     # 案例模型
│       │   └── decision.py # 决策模型
│       │
│       ├── builtin/        # ========== 内置模块 ==========
│       │   ├── __init__.py
│       │   ├── base.py     # 内置模块基类
│       │   ├── cli/        # 命令行界面（必须）
│       │   ├── storage/    # 数据存储（必须）
│       │   ├── search/     # 基础检索（必须）
│       │   └── nlp/        # 基础NLP（必须）
│       │
│       ├── plugins/        # ========== 插件目录 ==========
│       │   ├── __init__.py
│       │   ├── base.py     # 插件基类
│       │   ├── ai/         # AI增强插件
│       │   ├── bias/       # 偏见检测插件
│       │   ├── viz/        # 可视化插件
│       │   ├── knowledge/  # 知识管理插件
│       │   └── web/        # Web界面插件
│       │
│       └── utils/          # 工具函数
│           ├── __init__.py
│           └── helpers.py
│
├── plugins/                # ========== 用户自定义插件 ==========
│   └── (用户自己的插件)
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── plugins/            # 插件测试
│
├── data/                   # 用户数据
├── config/
│   ├── default.yaml
│   └── plugins/            # 插件配置
│
└── docs/
```

---

## 核心机制详解

### 1. 事件总线 (Event Bus)

**作用：** 解耦各模块，让插件间可以通信

```python
# core/events.py
from typing import Callable, Dict, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Event:
    name: str
    data: dict
    timestamp: datetime = datetime.now()

class EventBus:
    """简单的事件总线实现"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
    
    def on(self, event_name: str, handler: Callable):
        """订阅事件"""
        if event_name not in self._handlers:
            self._handlers[event_name] = []
        self._handlers[event_name].append(handler)
    
    def emit(self, event_name: str, data: dict = None):
        """触发事件"""
        event = Event(name=event_name, data=data or {})
        for handler in self._handlers.get(event_name, []):
            try:
                handler(event)
            except Exception as e:
                print(f"事件处理错误: {e}")
    
    def off(self, event_name: str, handler: Callable):
        """取消订阅"""
        if event_name in self._handlers:
            self._handlers[event_name].remove(handler)

# 全局事件总线实例
events = EventBus()
```

**使用示例：**

```python
# 在插件中监听事件
from vintagewisdom.core.events import events

def on_case_added(event):
    case = event.data.get('case')
    print(f"新案例添加: {case.title}")

events.on('case.added', on_case_added)

# 在其他地方触发事件
from vintagewisdom.core.events import events

events.emit('case.added', {'case': new_case})
```

### 2. 插件基类与注册机制

```python
# plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    dependencies: list = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class Plugin(ABC):
    """所有插件的基类"""
    
    # 插件信息，子类必须定义
    INFO: PluginInfo = None
    
    def __init__(self, app, config: Dict[str, Any] = None):
        self.app = app
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def initialize(self):
        """初始化插件，注册功能"""
        pass
    
    def activate(self):
        """激活插件"""
        self.enabled = True
        self.on_activate()
    
    def deactivate(self):
        """停用插件"""
        self.enabled = False
        self.on_deactivate()
    
    def on_activate(self):
        """激活时的回调，子类可重写"""
        pass
    
    def on_deactivate(self):
        """停用时的回调，子类可重写"""
        pass
    
    def get_config(self, key: str, default=None):
        """获取配置项"""
        return self.config.get(key, default)


# 功能扩展点装饰器

def register_command(name: str, help_text: str = ""):
    """注册CLI命令"""
    def decorator(func):
        func._is_command = True
        func._command_name = name
        func._help_text = help_text
        return func
    return decorator

def register_hook(event_name: str, priority: int = 10):
    """注册事件钩子"""
    def decorator(func):
        func._is_hook = True
        func._hook_event = event_name
        func._hook_priority = priority
        return func
    return decorator

def register_retriever(name: str):
    """注册检索器"""
    def decorator(cls):
        cls._is_retriever = True
        cls._retriever_name = name
        return cls
    return decorator
```

### 3. 插件管理器

```python
# core/registry.py
import importlib
import pkgutil
from pathlib import Path
from typing import Dict, Type, List
from .plugins.base import Plugin, PluginInfo

class PluginRegistry:
    """插件注册与管理"""
    
    def __init__(self, app):
        self.app = app
        self._plugins: Dict[str, Plugin] = {}
        self._plugin_classes: Dict[str, Type[Plugin]] = {}
    
    def discover_builtin(self):
        """发现内置插件"""
        from .. import plugins as builtin_plugins
        self._discover_from_package(builtin_plugins, "vintagewisdom.plugins")
    
    def discover_user_plugins(self, plugin_dir: Path):
        """发现用户自定义插件"""
        if not plugin_dir.exists():
            return
        
        # 将用户插件目录加入Python路径
        import sys
        sys.path.insert(0, str(plugin_dir.parent))
        
        for item in plugin_dir.iterdir():
            if item.is_dir() and (item / "__init__.py").exists():
                try:
                    module = importlib.import_module(f"{plugin_dir.name}.{item.name}")
                    self._load_from_module(module)
                except Exception as e:
                    print(f"加载用户插件失败 {item.name}: {e}")
    
    def _discover_from_package(self, package, package_name: str):
        """从包中发现插件"""
        for _, name, is_pkg in pkgutil.iter_modules(package.__path__):
            if is_pkg:
                try:
                    module = importlib.import_module(f"{package_name}.{name}")
                    self._load_from_module(module)
                except Exception as e:
                    print(f"加载插件失败 {name}: {e}")
    
    def _load_from_module(self, module):
        """从模块中加载插件类"""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and 
                issubclass(attr, Plugin) and 
                attr is not Plugin and
                attr.INFO is not None):
                self._plugin_classes[attr.INFO.name] = attr
    
    def load(self, name: str, config: dict = None) -> Plugin:
        """加载并初始化插件"""
        if name not in self._plugin_classes:
            raise ValueError(f"未知插件: {name}")
        
        if name in self._plugins:
            return self._plugins[name]
        
        plugin_class = self._plugin_classes[name]
        plugin = plugin_class(self.app, config)
        plugin.initialize()
        self._plugins[name] = plugin
        
        return plugin
    
    def unload(self, name: str):
        """卸载插件"""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.deactivate()
            del self._plugins[name]
    
    def get(self, name: str) -> Optional[Plugin]:
        """获取已加载的插件"""
        return self._plugins.get(name)
    
    def list_available(self) -> List[PluginInfo]:
        """列出所有可用插件"""
        return [cls.INFO for cls in self._plugin_classes.values()]
    
    def list_loaded(self) -> List[str]:
        """列出已加载的插件"""
        return list(self._plugins.keys())
```

---

## 实际插件示例

### 示例1：AI红队插件

```python
# plugins/ai/redteam.py
from ..base import Plugin, PluginInfo, register_command, register_hook
from ...core.events import events

class RedTeamPlugin(Plugin):
    """AI红队对抗插件"""
    
    INFO = PluginInfo(
        name="ai.redteam",
        version="1.0.0",
        description="AI红队对抗，挑战决策假设",
        author="VintageWisdom",
        dependencies=["ai.base"]  # 依赖基础AI模块
    )
    
    def initialize(self):
        """初始化"""
        # 注册命令
        self.app.cli.register_command(
            "redteam", 
            self.cmd_redteam,
            "启动红队对抗分析"
        )
        
        # 监听事件
        events.on('decision.before', self.on_decision_before)
    
    def cmd_redteam(self, query: str):
        """红队命令实现"""
        print(f"🎯 红队对抗分析: {query}")
        
        # 1. 事实基础攻击
        self._fact_attack(query)
        
        # 2. 逻辑结构攻击
        self._logic_attack(query)
        
        # 3. 隐含假设攻击
        self._assumption_attack(query)
    
    def _fact_attack(self, query: str):
        """事实基础攻击"""
        print("\n📊 [Layer 1: 事实基础攻击]")
        # 实现...
    
    def _logic_attack(self, query: str):
        """逻辑结构攻击"""
        print("\n🔗 [Layer 2: 逻辑结构攻击]")
        # 实现...
    
    def _assumption_attack(self, query: str):
        """隐含假设攻击"""
        print("\n💭 [Layer 3: 隐含假设攻击]")
        # 实现...
    
    def on_decision_before(self, event):
        """决策前自动触发"""
        if self.get_config('auto_trigger', False):
            query = event.data.get('query')
            self.cmd_redteam(query)


# plugins/ai/__init__.py
from .redteam import RedTeamPlugin
from .future_self import FutureSelfPlugin
from .pressure_test import PressureTestPlugin

__all__ = ['RedTeamPlugin', 'FutureSelfPlugin', 'PressureTestPlugin']
```

### 示例2：可视化插件

```python
# plugins/viz/graph.py
from ..base import Plugin, PluginInfo

class GraphVizPlugin(Plugin):
    """知识图谱可视化插件"""
    
    INFO = PluginInfo(
        name="viz.graph",
        version="1.0.0",
        description="知识图谱可视化",
        author="VintageWisdom",
        dependencies=["viz.base"]
    )
    
    def initialize(self):
        self.app.cli.register_command(
            "viz graph",
            self.cmd_viz_graph,
            "可视化知识图谱"
        )
    
    def cmd_viz_graph(self, case_id: str = None):
        """生成图谱可视化"""
        try:
            from pyvis.network import Network
        except ImportError:
            print("请先安装: pip install pyvis")
            return
        
        # 生成可视化
        net = Network(notebook=True)
        # ... 添加节点和边
        net.show("graph.html")
        print("图谱已生成: graph.html")
```

### 示例3：偏见检测插件

```python
# plugins/bias/detector.py
from ..base import Plugin, PluginInfo, register_hook
from ...core.events import events

class BiasDetectorPlugin(Plugin):
    """认知偏见检测插件"""
    
    INFO = PluginInfo(
        name="bias.detector",
        version="1.0.0",
        description="检测认知偏见",
        author="VintageWisdom"
    )
    
    # 检测的偏见类型
    BIAS_TYPES = {
        'confirmation': '确认偏误',
        'planning_fallacy': '计划谬误',
        'sunk_cost': '沉没成本',
        'recency': '近因效应'
    }
    
    def initialize(self):
        events.on('search.before', self.on_search_before)
        events.on('decision.before', self.on_decision_before)
    
    def on_search_before(self, event):
        """搜索前检测"""
        query = event.data.get('query')
        biases = self._detect_biases(query)
        
        if biases:
            print(f"\n⚠️  检测到潜在偏见: {', '.join(biases)}")
            event.data['bias_warnings'] = biases
    
    def on_decision_before(self, event):
        """决策前检测"""
        context = event.data.get('context')
        # 分析决策情境中的偏见信号
        pass
    
    def _detect_biases(self, query: str) -> list:
        """检测查询中的偏见信号"""
        biases = []
        
        # 确认偏误：关键词匹配
        if any(word in query for word in ['肯定', '一定', '绝对']):
            biases.append('confirmation')
        
        # 计划谬误：时间相关
        if any(word in query for word in ['只需要', '很快', '简单']):
            biases.append('planning_fallacy')
        
        return [self.BIAS_TYPES[b] for b in biases]
```

---

## 应用主类

```python
# core/app.py
from typing import Dict, Any
from pathlib import Path
from .config import Config
from .events import events
from .registry import PluginRegistry
from .storage import Storage

class VintageWisdomApp:
    """应用主类"""
    
    def __init__(self, config_path: Path = None):
        # 配置
        self.config = Config(config_path)
        
        # 存储
        self.storage = Storage(self.config.get('storage'))
        
        # 插件注册表
        self.plugins = PluginRegistry(self)
        
        # CLI（延后初始化）
        self._cli = None
        
        # 状态
        self._initialized = False
    
    def initialize(self):
        """初始化应用"""
        if self._initialized:
            return
        
        # 1. 初始化存储
        self.storage.initialize()
        
        # 2. 发现插件
        self.plugins.discover_builtin()
        
        user_plugin_dir = self.config.get('plugins.user_dir')
        if user_plugin_dir:
            self.plugins.discover_user_plugins(Path(user_plugin_dir))
        
        # 3. 加载启用的插件
        enabled_plugins = self.config.get('plugins.enabled', [])
        for plugin_name in enabled_plugins:
            try:
                plugin_config = self.config.get(f'plugins.config.{plugin_name}', {})
                self.plugins.load(plugin_name, plugin_config)
                print(f"✅ 插件已加载: {plugin_name}")
            except Exception as e:
                print(f"❌ 插件加载失败 {plugin_name}: {e}")
        
        # 4. 触发初始化完成事件
        events.emit('app.initialized', {'app': self})
        
        self._initialized = True
    
    @property
    def cli(self):
        """获取CLI接口（懒加载）"""
        if self._cli is None:
            from ..builtin.cli import CLI
            self._cli = CLI(self)
        return self._cli
    
    def run(self):
        """运行应用"""
        self.initialize()
        self.cli.run()
    
    def shutdown(self):
        """关闭应用"""
        events.emit('app.shutdown')
        self.storage.close()
```

---

## 配置文件

```yaml
# config/default.yaml

app:
  name: "VintageWisdom"
  version: "0.1.0"

# 存储配置
storage:
  type: "sqlite"
  path: "data/vintagewisdom.db"

# 插件配置
plugins:
  # 用户自定义插件目录
  user_dir: "./plugins"
  
  # 启用的插件列表
  enabled:
    - storage.sqlite      # 内置：SQLite存储
    - search.basic        # 内置：基础检索
    - nlp.basic           # 内置：基础NLP
    - cli.tui             # 内置：TUI界面
    - ai.redteam          # AI红队（可选）
    - ai.future_self      # 未来你对话（可选）
    - bias.detector       # 偏见检测（可选）
    - viz.graph           # 图谱可视化（可选）
  
  # 各插件配置
  config:
    ai.redteam:
      auto_trigger: false
      intensity: "medium"
    
    bias.detector:
      check_on_search: true
      check_on_decision: true
    
    viz.graph:
      default_layout: "force_atlas"

# 其他配置...
```

---

## 添加新功能的步骤

### 步骤1：创建插件目录

```bash
mkdir -p src/vintagewisdom/plugins/myfeature
```

### 步骤2：实现插件类

```python
# src/vintagewisdom/plugins/myfeature/__init__.py
from ..base import Plugin, PluginInfo

class MyFeaturePlugin(Plugin):
    INFO = PluginInfo(
        name="myfeature",
        version="1.0.0",
        description="我的新功能",
        author="Your Name"
    )
    
    def initialize(self):
        # 注册命令
        self.app.cli.register_command(
            "myfeature",
            self.run,
            "运行我的功能"
        )
        
        # 或监听事件
        from ...core.events import events
        events.on('some.event', self.handler)
    
    def run(self, *args):
        print("我的功能运行了！")
    
    def handler(self, event):
        pass
```

### 步骤3：启用插件

```yaml
# config/user.yaml
plugins:
  enabled:
    - ...
    - myfeature  # 添加到这里
```

### 步骤4：运行测试

```bash
python -m vintagewisdom myfeature
```

---

## 开发建议

### 1. 功能优先级

```
第一阶段（核心，必须）：
├── 基础存储 (storage.sqlite)
├── 基础检索 (search.basic)
├── 基础NLP (nlp.basic)
└── CLI界面 (cli.tui)

第二阶段（增强，推荐）：
├── AI红队 (ai.redteam)
├── 偏见检测 (bias.detector)
└── 因果推演 (ai.reasoning)

第三阶段（高级，可选）：
├── 图谱可视化 (viz.graph)
├── 跨领域映射 (knowledge.mapping)
├── Web界面 (web.ui)
└── 语音输入 (cli.voice)
```

### 2. 开发流程

```
1. 确定功能范围
   ↓
2. 创建插件目录
   ↓
3. 实现最小可用版本（MVP）
   ↓
4. 注册命令/事件
   ↓
5. 配置文件中启用
   ↓
6. 测试集成
   ↓
7. 迭代完善
```

### 3. 最佳实践

- **一个插件一个功能** - 保持单一职责
- **优先使用事件** - 减少模块间直接依赖
- **配置外部化** - 不要硬编码参数
- **优雅降级** - 插件失败不影响核心功能
- **文档注释** - 写清楚插件的用途和用法

---

*这种架构让你可以：*
- ✅ 逐个添加功能，不影响现有代码
- ✅ 随时启用/禁用某个功能
- ✅ 用户可以自己开发插件扩展
- ✅ 核心框架稳定，功能独立演进
