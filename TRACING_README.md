# GTPlanner Tracing 集成

## 概述

已成功为GTPlanner项目集成了pocketflow-tracing功能，实现了对所有主要Flow的自动追踪和监控。

## 已完成的工作

### 1. 依赖配置
- ✅ 项目已包含`pocketflow-tracing>=0.1.4`依赖
- ✅ 更新了`.env.example`文件，添加了Langfuse配置项

### 2. Flow Tracing集成

已为以下Flow添加了自动tracing功能：

#### ShortPlanningFlow
- **文件**: `agent/subflows/short_planning/flows/short_planning_flow.py`
- **功能**: 短规划生成流程
- **Tracing名称**: `ShortPlanningFlow`
- **状态**: ✅ 已集成

#### ResearchFlow
- **文件**: `agent/subflows/research/flows/research_flow.py`
- **功能**: 研究调研流程
- **Tracing名称**: `ResearchFlow`
- **状态**: ✅ 已集成

#### ArchitectureFlow
- **文件**: `agent/subflows/architecture/flows/architecture_flow.py`
- **功能**: 架构设计流程
- **Tracing名称**: `ArchitectureFlow`
- **状态**: ✅ 已集成

### 3. 示例和文档

#### 创建的文件：
1. **`examples/tracing_example.py`** - 完整的tracing使用示例
2. **`agent/tracing_guide.md`** - 详细的使用指南
3. **`test_tracing.py`** - tracing功能测试脚本
4. **`TRACING_README.md`** - 本文件，集成总结

## 技术实现

### Tracing装饰器
每个Flow都使用了`@trace_flow`装饰器：

```python
from pocketflow_tracing import trace_flow

@trace_flow(flow_name="FlowName")
class TracedFlow(AsyncFlow):
    async def prep_async(self, shared):
        # 流程级准备，记录开始时间
        shared["flow_start_time"] = asyncio.get_event_loop().time()
        return {"flow_id": "flow_name", "start_time": shared["flow_start_time"]}
    
    async def post_async(self, shared, prep_result, exec_result):
        # 流程级后处理，计算执行时长
        flow_duration = asyncio.get_event_loop().time() - prep_result["start_time"]
        shared["flow_metadata"] = {
            "flow_id": prep_result["flow_id"],
            "duration": flow_duration,
            "status": "completed"
        }
        return exec_result
```

### 自动追踪的信息
- ✅ Flow执行开始和结束时间
- ✅ 每个Node的prep、exec、post阶段
- ✅ 输入和输出数据
- ✅ 错误和异常信息
- ✅ 执行时长统计
- ✅ 流程元数据

## 配置要求

### 环境变量
需要在`.env`文件中配置以下变量：

```bash
# Langfuse配置（必需）
LANGFUSE_SECRET_KEY=your-secret-key-here
LANGFUSE_PUBLIC_KEY=your-public-key-here
LANGFUSE_HOST=https://your-langfuse-host.com

# PocketFlow Tracing配置（可选）
POCKETFLOW_TRACING_DEBUG=true
POCKETFLOW_TRACE_INPUTS=true
POCKETFLOW_TRACE_OUTPUTS=true
POCKETFLOW_TRACE_PREP=true
POCKETFLOW_TRACE_EXEC=true
POCKETFLOW_TRACE_POST=true
POCKETFLOW_TRACE_ERRORS=true

# 会话配置（可选）
POCKETFLOW_SESSION_ID=gtplanner-session
POCKETFLOW_USER_ID=gtplanner-user
```

### Langfuse设置
1. 注册Langfuse账号：https://langfuse.com
2. 创建新项目
3. 获取Secret Key、Public Key和Host URL
4. 将信息填入`.env`文件

## 使用方式

### 1. 运行示例
```bash
python examples/tracing_example.py
```

### 2. 测试tracing功能
```bash
python test_tracing.py
```

### 3. 在现有代码中使用
所有已集成的Flow会自动进行tracing，无需额外代码：

```python
from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow

# 创建Flow实例
flow = ShortPlanningFlow()

# 准备数据
shared = {"structured_requirements": {...}}

# 运行Flow（自动进行tracing）
result = await flow.run_async(shared)
```

## 查看Trace结果

1. 运行任何带tracing的Flow后
2. 登录Langfuse仪表板
3. 在项目中查看最新的trace
4. 可以看到完整的执行轨迹，包括：
   - Flow级别的执行时间
   - 每个Node的详细执行信息
   - 输入输出数据
   - 错误信息（如果有）

## 性能影响

- ✅ Tracing开销很小，不会显著影响性能
- ✅ 可以通过环境变量控制tracing级别
- ✅ 生产环境可以选择性启用tracing功能

## 扩展性

### 为新Flow添加Tracing
参考`agent/tracing_guide.md`中的详细说明，可以轻松为新的Flow添加tracing功能。

### 自定义Tracing
可以通过TracingConfig类自定义tracing行为：
- 控制追踪的数据类型
- 设置会话和用户ID
- 调整调试级别

## 故障排除

### 常见问题
1. **Tracing不工作** - 检查Langfuse配置
2. **数据不显示** - 确认Flow使用了正确的装饰器
3. **性能问题** - 调整tracing配置级别

详细的故障排除指南请参考`agent/tracing_guide.md`。

## 下一步

### 建议的改进
1. 为更多的Node添加自定义tracing信息
2. 集成性能监控和告警
3. 添加tracing数据的分析和可视化
4. 考虑集成其他observability工具

### 维护
- 定期检查tracing配置
- 监控Langfuse存储使用情况
- 根据需要调整tracing级别

## 相关文档

- [PocketFlow Tracing文档](https://redreamality.com/blog/pocketflow-tracing)
- [Langfuse文档](https://langfuse.com/docs)
- [GTPlanner架构文档](docs/system-architecture.md)
- [详细使用指南](agent/tracing_guide.md)
