"""
GTPlanner Agent 模块

GTPlanner (Graph Task Planner) 是一个基于ReAct模式的智能任务规划系统，
能够根据用户需求自动生成结构化的任务流程图和相关文档。

主要组件：
- shared: 系统级共享状态管理
- nodes: 原子能力节点
- subflows: 专业Agent子流程  
- flows: 主控制流程
- utils: 工具函数

使用示例：
```python
from agent import GTPlanner
from agent.shared import get_shared_state

# 创建GTPlanner实例
planner = GTPlanner()

# 处理用户需求
result = planner.process_user_request("我需要设计一个用户管理系统")

# 获取共享状态
state = get_shared_state()
print(state.to_dict())
```
"""

from .shared import SharedState, get_shared_state, reset_shared_state
from .gtplanner import GTPlanner


__all__ = [
    'SharedState',
    'get_shared_state',
    'reset_shared_state',
    'GTPlanner',
]

__version__ = "1.0.0"
