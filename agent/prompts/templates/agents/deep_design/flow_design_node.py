"""
流程设计节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/flow_design_node.py
"""


class AgentsDeepDesignFlowDesignNodeTemplates:
    """流程设计节点提示词模板类"""
    
    @staticmethod
    def get_flow_design_zh() -> str:
        """中文版本的流程设计提示词"""
        return """你是一个专业的pocketflow流程设计师，专门负责设计Node之间的连接和执行流程。

请基于以下信息设计完整的Flow执行流程：

**Agent分析结果：**
{analysis_markdown}

**Node识别结果：**
{nodes_markdown}

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**技术调研结果：**
{research_info}

**推荐工具：**
{tools_info}

请进行以下Flow设计工作：

1. **主流程设计**：
   - 设计从输入到输出的主要执行路径
   - 定义关键的执行阶段和里程碑
   - 确保流程的逻辑完整性和一致性

2. **Node连接设计**：
   - 定义Node之间的连接关系和数据传递
   - 设计Action驱动的状态转换逻辑
   - 确保数据流的正确性和完整性

3. **分支和条件处理**：
   - 设计条件分支和异常处理流程
   - 定义不同场景下的执行路径
   - 确保所有可能的执行情况都有对应的处理

4. **并行和串行执行**：
   - 识别可以并行执行的Node组合
   - 设计串行执行的依赖关系
   - 优化整体执行效率和资源利用

5. **错误处理和恢复**：
   - 设计错误检测和处理机制
   - 定义失败重试和恢复策略
   - 确保系统的健壮性和可靠性

6. **性能优化考虑**：
   - 识别潜在的性能瓶颈点
   - 设计缓存和优化策略
   - 考虑资源使用和响应时间



请严格按照以下Markdown格式输出Flow设计结果：

# Flow设计结果

## Flow概述
- **Flow名称**: [Flow名称]
- **Flow描述**: [Flow的整体描述]
- **起始节点**: [起始节点名称，必须来自已识别的Node列表]


## Flow图表

```mermaid
flowchart TD
    [在这里生成完整的Mermaid flowchart TD代码]
```

## 节点连接关系

### 连接 1
- **源节点**: [源节点名称]
- **目标节点**: [目标节点名称]
- **触发Action**: [default或具体action名]
- **转换条件**: [转换条件描述]
- **传递数据**: [传递的数据描述]

## 执行流程

### 步骤 1
- **节点**: [节点名称]
- **描述**: [此步骤的作用]
- **输入数据**: [输入数据来源]
- **输出数据**: [输出数据去向]

## 编排结果
```python
node_1 = Node1()
node_2 = Node2()
node_3 = Node3()
node_4 = Node4() ## default 

node_1 - "action_1" >> node_2
node_2 - "action_2" >> node_3
node_3 >> node_4
```

## 设计理由
[Flow编排的设计理由]

编排要求：
1. 只能使用已识别的Node列表中的Node
2. 确保数据流的完整性和逻辑性
3. 使用Action驱动的转换逻辑
4. 考虑错误处理和分支逻辑
5. Mermaid图要清晰展示所有连接和数据流
6. 确保每个Node都有明确的前置和后置关系

重要：请严格按照上述Markdown格式输出，不要输出JSON格式！直接输出完整的Markdown文档。
"""
    
    @staticmethod
    def get_flow_design_en() -> str:
        """English version of flow design prompt"""
        return """You are a professional pocketflow process designer specializing in designing connections and execution flows between Nodes.

Please design a complete Flow execution process based on the following information:

**Agent Analysis Results:**
{analysis_markdown}

**Node Identification Results:**
{nodes_markdown}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Technical Research Results:**
{research_info}

**Recommended Tools:**
{tools_info}

Please perform the following Flow design work:

1. **Main Process Design**:
   - Design main execution paths from input to output
   - Define key execution phases and milestones
   - Ensure logical integrity and consistency of the process

2. **Node Connection Design**:
   - Define connection relationships and data transfer between Nodes
   - Design Action-driven state transition logic
   - Ensure correctness and completeness of data flow

3. **Branch and Conditional Processing**:
   - Design conditional branches and exception handling processes
   - Define execution paths for different scenarios
   - Ensure all possible execution situations have corresponding handling

4. **Parallel and Serial Execution**:
   - Identify Node combinations that can execute in parallel
   - Design dependency relationships for serial execution
   - Optimize overall execution efficiency and resource utilization

5. **Error Handling and Recovery**:
   - Design error detection and handling mechanisms
   - Define failure retry and recovery strategies
   - Ensure system robustness and reliability

6. **Performance Optimization Considerations**:
   - Identify potential performance bottleneck points
   - Design caching and optimization strategies
   - Consider resource usage and response time

For Flow design, please provide:
- Complete Flow execution diagram (using Mermaid syntax)
- Detailed execution step descriptions
- Action transition conditions and logic
- Exception handling and error recovery mechanisms
- Performance optimization recommendations

Please output Flow design results in a structured format with clear execution logic and implementation guidance."""
    
    @staticmethod
    def get_flow_design_ja() -> str:
        """日本語版のフロー設計プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_flow_design_es() -> str:
        """Versión en español del prompt de diseño de flujo"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_flow_design_fr() -> str:
        """Version française du prompt de conception de flux"""
        return """# TODO: Ajouter le prompt en français"""
