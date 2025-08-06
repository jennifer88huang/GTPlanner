# GTPlanner Agent 模块

GTPlanner (Graph Task Planner) 是一个基于ReAct模式的智能任务规划系统，能够根据用户需求自动生成结构化的任务流程图和相关文档。

## 项目结构

```
agent/
├── __init__.py                 # 模块主入口
├── gtplanner.py               # GTPlanner主控制器
├── shared.py                  # 系统级共享状态管理
├── agent_doc.md              # 系统架构设计文档
├── README.md                 # 项目说明文档
├── nodes/                    # 原子能力节点
│   ├── __init__.py
│   ├── node_req.py          # 需求解析节点
│   ├── node_search.py       # 搜索引擎节点
│   ├── node_url.py          # URL解析节点
│   ├── node_recall.py       # 文档召回节点
│   ├── node_compress.py     # 上下文压缩节点
│   └── node_output.py       # 输出文档节点
├── subflows/                 # 专业Agent子流程
│   ├── __init__.py
│   ├── requirements_analysis_flow.py    # 需求分析Agent子流程
│   ├── short_planning_flow.py          # 短规划Agent子流程
│   ├── research_flow.py                # 研究调研Agent子流程
│   ├── architecture_flow.py            # 架构设计Agent子流程
│   └── documentation_flow.py           # 文档生成Agent子流程
├── flows/                    # 主控制流程
│   ├── __init__.py
│   └── orchestrator_react_flow.py     # Orchestrator ReAct循环流程
└── utils/                    # 工具函数
    ├── search.py            # 搜索相关工具
    └── web.py               # 网络相关工具
```

## 核心组件

### 1. 共享状态管理 (shared.py)
- 管理系统级共享变量
- 提供数据一致性保证
- 支持状态持久化和恢复

### 2. 原子能力节点 (nodes/)
每个节点实现特定的原子操作，基于pocketflow.Node：
- **NodeReq**: 从自然语言中提取结构化需求
- **NodeSearch**: 执行网络搜索并返回结果
- **NodeURL**: 解析网页内容并提取信息
- **NodeRecall**: 从知识库召回相关文档
- **NodeCompress**: 压缩长文本保留关键信息
- **NodeOutput**: 生成最终的文档文件

### 3. 专业Agent子流程 (subflows/)
每个子流程协调相关节点完成复杂业务逻辑：
- **RequirementsAnalysisFlow**: 需求分析处理流程
- **ShortPlanningFlow**: 短规划生成和确认流程
- **ResearchFlow**: 信息研究和综合流程
- **ArchitectureFlow**: 架构设计和文档生成流程（集成了文档生成功能）

### 4. 主控制流程 (flows/)
- **OrchestratorReActFlow**: 实现ReAct循环（思考-行动-观察）

## 设计原则

### 1. 原子性操作
- 每个节点只处理单一职责
- 节点内部不接收数组，所有批处理在Flow层面完成
- 确保节点的可复用性和可测试性

### 2. 数据流驱动
- 通过共享状态在组件间传递数据
- 明确的数据转换和验证机制
- 支持数据血缘追踪

### 3. 错误处理
- 多层次的错误处理和恢复机制
- 支持重试、降级和熔断
- 详细的错误日志和监控

### 4. 扩展性设计
- 模块化架构便于扩展新功能
- 支持水平扩展和性能优化
- 插件化的节点和流程设计

## 使用示例

### 基本使用
```python
from agent import GTPlanner

# 创建GTPlanner实例
planner = GTPlanner()

# 处理用户需求
result = planner.process_user_request("我需要设计一个用户管理系统")

if result["success"]:
    print("处理成功!")
    print(f"会话ID: {result['session_id']}")
else:
    print(f"处理失败: {result['error']}")
```

### 获取处理结果
```python
# 获取结构化需求
requirements = planner.get_requirements()

# 获取研究发现
research = planner.get_research_findings()

# 获取架构设计
architecture = planner.get_architecture_draft()

# 获取完整状态
state = planner.get_state()
```

### 状态管理
```python
# 保存状态
planner.save_state("session_state.json")

# 重置状态
planner.reset()
```

## 开发指南

### 添加新节点
1. 在`nodes/`目录下创建新的节点文件
2. 继承`pocketflow.Node`类
3. 实现`prep()`, `exec()`, `post()`方法
4. 在`nodes/__init__.py`中导出

### 添加新子流程
1. 在`subflows/`目录下创建新的流程文件
2. 继承`pocketflow.Flow`类
3. 组合相关节点实现业务逻辑
4. 在`subflows/__init__.py`中导出

### 扩展共享状态
1. 在`shared.py`中添加新的数据结构
2. 更新`SharedState`类
3. 确保序列化和反序列化支持

## 依赖要求

- Python 3.8+
- pocketflow
- 其他依赖见requirements.txt

## 测试

```bash
# 运行单元测试
python -m pytest tests/

# 运行集成测试
python -m pytest tests/integration/

# 运行性能测试
python -m pytest tests/performance/
```
