# Requirements Analysis Agent

GTPlanner 的需求分析专业 Agent，负责将用户对话和意图转换为结构化的项目需求。

**🚧 状态**: 开发完成，待测试验证  
**📅 创建时间**: 2024年12月1日

## 概述

Requirements Analysis Agent 基于 pocketflow 框架实现，采用4步流程将用户的自然语言描述转换为标准化的项目需求文档。

## 核心功能

### 🔍 需求提取
- 使用 NodeReq 从对话历史中提取关键信息
- 识别功能需求、非功能需求、约束条件
- 提取项目目标和用户群体

### 🤖 LLM结构化
- 使用大语言模型将提取的信息进行结构化
- 生成标准化的项目需求文档格式
- 补充缺失的需求细节

### ✅ 格式验证
- 验证需求文档的格式完整性
- 检查必需字段和数据类型
- 生成质量评估报告

### 📊 质量评估
- 评估需求的完整性、清晰度、一致性、可行性
- 生成质量评分和改进建议
- 提供详细的验证报告

## 架构设计

### 流程架构

```
NodeReq → LLMStructureNode → ValidationNode → ProcessRequirementsNode
```

### 主要组件

```
Requirements Analysis Agent
├── ProcessRequirementsNode     # 主节点，协调整个流程
├── RequirementsAnalysisFlow   # 内部工作流程
│   ├── NodeReq               # 需求提取节点（复用）
│   ├── LLMStructureNode      # LLM结构化节点
│   └── ValidationNode        # 验证节点
└── 输出: structured_requirements
```

### 数据流

```
dialogue_history + user_intent → 需求提取 → LLM结构化 → 格式验证 → 质量评估 → structured_requirements
```

## 使用方式

### 1. 作为 GTPlanner 主流程的一部分

```python
# 在主流程中使用
shared = {
    "dialogue_history": "用户希望开发一个项目管理系统...",
    "user_intent": {"original_request": "..."}
}

process_requirements = ProcessRequirementsNode()
result = process_requirements.run(shared)
```

### 2. 独立使用需求分析流程

```python
from agent.subflows.requirements_analysis import RequirementsAnalysisFlow

requirements_flow = RequirementsAnalysisFlow()
shared = {
    "dialogue_history": "用户对话历史",
    "user_intent": {"original_request": "用户原始请求"}
}

result = requirements_flow.run(shared)
structured_requirements = shared["structured_requirements"]
```

## 输出格式

### 结构化需求

```python
{
    "project_overview": {
        "title": "项目标题",
        "description": "项目描述",
        "objectives": ["目标1", "目标2"],
        "target_users": ["用户群体1", "用户群体2"],
        "success_criteria": ["成功标准1", "成功标准2"]
    },
    "functional_requirements": {
        "core_features": [
            {
                "name": "功能名称",
                "description": "功能描述",
                "priority": "high/medium/low",
                "acceptance_criteria": ["验收标准1", "验收标准2"]
            }
        ],
        "user_stories": [
            {
                "role": "用户角色",
                "goal": "用户目标", 
                "benefit": "用户收益"
            }
        ]
    },
    "non_functional_requirements": {
        "performance": {
            "response_time": "响应时间要求",
            "throughput": "吞吐量要求",
            "concurrent_users": "并发用户数"
        },
        "security": {
            "authentication": "认证要求",
            "authorization": "授权要求",
            "data_protection": "数据保护要求"
        },
        "scalability": {
            "horizontal_scaling": "水平扩展要求",
            "vertical_scaling": "垂直扩展要求"
        }
    },
    "technical_requirements": {
        "programming_languages": ["编程语言"],
        "frameworks": ["框架"],
        "databases": ["数据库"],
        "deployment": ["部署方式"],
        "monitoring": ["监控工具"]
    },
    "constraints": {
        "budget": "预算约束",
        "timeline": "时间约束",
        "resources": "资源约束",
        "compliance": ["合规要求"]
    }
}
```

### 验证报告

```python
{
    "format_validation": {
        "is_valid": true,
        "missing_fields": [],
        "invalid_fields": [],
        "warnings": []
    },
    "quality_assessment": {
        "score": 0.85,
        "metrics": {
            "completeness": 0.9,
            "clarity": 0.8,
            "consistency": 0.85,
            "feasibility": 0.85
        },
        "grade": "良好"
    },
    "overall_score": 0.85,
    "recommendations": ["改进建议"]
}
```

## 配置要求

### 依赖包

```bash
pip install pocketflow
```

### LLM配置

需要配置LLM API用于结构化处理（当前使用模拟数据）。

## 错误处理

- **输入验证失败**: 使用默认对话历史继续处理
- **LLM调用失败**: 抛出异常，终止流程
- **验证失败**: 提供详细的错误报告和改进建议
- **流程异常**: 返回错误信息，由上层处理

## 质量保证

### 验证机制
- 格式完整性检查
- 必需字段验证
- 数据类型验证
- 优先级值验证

### 质量评估
- **完整性**: 检查所有必需字段是否填充
- **清晰度**: 评估描述的详细程度和关键词使用
- **一致性**: 检查技术栈和功能的匹配度
- **可行性**: 评估约束条件的合理性

## 文件结构

```
agent/subflows/requirements_analysis/
├── __init__.py                     # 主包导入
├── README.md                       # 使用文档
├── nodes/                          # 节点文件夹
│   ├── __init__.py                # 节点包导入
│   ├── llm_structure_node.py      # LLM结构化节点
│   ├── validation_node.py         # 验证节点
│   └── process_requirements_node.py # 主处理节点
├── flows/                          # 流程文件夹
│   ├── __init__.py                # 流程包导入
│   └── requirements_analysis_flow.py # 主流程
├── utils/                          # 工具文件夹
│   └── __init__.py                # 工具包导入
├── test/                           # 测试文件夹
│   └── __init__.py                # 测试包导入
└── docs/                           # 文档文件夹
    └── __init__.py                # 文档包导入
```

## 开发团队

Requirements Analysis Agent 基于 pocketflow 框架的最佳实践开发，遵循 GTPlanner 的架构设计原则。

---

*Requirements Analysis Agent - 将用户想法转化为结构化需求*
