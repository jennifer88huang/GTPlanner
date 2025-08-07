"""
Agent Function Calling工具包装器

将现有的子Agent节点直接包装为OpenAI Function Calling工具，
保持现有流程逻辑不变，只是提供Function Calling接口。
"""


from typing import Dict, List, Any, Optional

# 导入现有的子Agent流程
from agent.subflows.requirements_analysis.flows.requirements_analysis_flow import RequirementsAnalysisFlow
from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow
from agent.subflows.research.flows.research_flow import ResearchFlow
from agent.subflows.architecture.flows.architecture_flow import ArchitectureFlow


def get_agent_function_definitions() -> List[Dict[str, Any]]:
    """
    获取所有Agent工具的Function Calling定义
    
    Returns:
        OpenAI Function Calling格式的工具定义列表
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "requirements_analysis",
                "description": "分析用户需求并生成结构化的需求文档，包括项目概述、功能需求、非功能需求等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_input": {
                            "type": "string",
                            "description": "用户的原始需求描述，可以是自然语言的项目描述、功能要求或业务需求"
                        }
                    },
                    "required": ["user_input"]
                }
            }
        },
        {
            "type": "function", 
            "function": {
                "name": "short_planning",
                "description": "基于需求分析结果生成项目的短期规划，包括开发阶段、里程碑、任务分解和时间估算",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "structured_requirements": {
                            "type": "object",
                            "description": "结构化的需求分析结果，通常来自requirements_analysis工具的输出"
                        }
                    },
                    "required": ["structured_requirements"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "research", 
                "description": "进行技术调研和解决方案研究，包括技术选型、架构模式、最佳实践等",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "research_requirements": {
                            "type": "string",
                            "description": "需要调研的技术需求和问题描述"
                        }
                    },
                    "required": ["research_requirements"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "architecture_design",
                "description": "生成详细的系统架构设计方案，包括技术架构、部署架构、数据架构等",
                "parameters": {
                    "type": "object", 
                    "properties": {
                        "structured_requirements": {
                            "type": "object",
                            "description": "项目需求信息，通常来自requirements_analysis工具的输出"
                        },
                        "confirmation_document": {
                            "type": "object",
                            "description": "项目规划信息，可以来自short_planning工具的输出",
                            "required": False
                        },
                        "research_findings": {
                            "type": "object", 
                            "description": "技术调研结果，可以来自research工具的输出",
                            "required": False
                        }
                    },
                    "required": ["structured_requirements"]
                }
            }
        }
    ]


async def execute_agent_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行Agent工具
    
    Args:
        tool_name: 工具名称
        arguments: 工具参数
        
    Returns:
        工具执行结果
    """
    try:
        if tool_name == "requirements_analysis":
            return await _execute_requirements_analysis(arguments)
        elif tool_name == "short_planning":
            return await _execute_short_planning(arguments)
        elif tool_name == "research":
            return await _execute_research(arguments)
        elif tool_name == "architecture_design":
            return await _execute_architecture_design(arguments)
        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Tool execution failed: {str(e)}"
        }


async def _execute_requirements_analysis(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行需求分析"""
    user_input = arguments.get("user_input", "")

    if not user_input:
        return {
            "success": False,
            "error": "user_input is required"
        }

    from agent.shared import shared_state

    # 利用pocketflow设计：提前在字典中写入数据，格式化为流程期望的格式
    shared_state.data["dialogue_history"] = {
        "messages": [
            {"role": "user", "content": user_input}
        ]
    }
    shared_state.data["user_intent"] = {
        "primary_goal": "用户需求分析"
    }

    # 创建并执行异步流程（使用pocketflow字典）
    flow = RequirementsAnalysisFlow()
    success = await flow.run_async(shared_state.data)

    if success:
        return {
            "success": True,
            "result": shared_state.structured_requirements,
            "tool_name": "requirements_analysis"
        }
    else:
        error_msg = shared_state.data.get('last_error', {}).get('error_message', "需求分析执行失败")
        return {
            "success": False,
            "error": error_msg
        }


async def _execute_short_planning(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行短期规划"""
    structured_requirements = arguments.get("structured_requirements")

    if not structured_requirements:
        return {
            "success": False,
            "error": "structured_requirements is required"
        }

    from agent.shared import shared_state

    # 利用pocketflow设计：提前在字典中写入数据
    shared_state.data["structured_requirements"] = structured_requirements

    # 创建并执行异步流程（使用pocketflow字典）
    flow = ShortPlanningFlow()
    success = await flow.run_async(shared_state.data)

    if success:
        return {
            "success": True,
            "result": shared_state.data.get("confirmation_document"),
            "tool_name": "short_planning"
        }
    else:
        error_msg = shared_state.data.get('last_error', {}).get('error_message', "短期规划执行失败")
        return {
            "success": False,
            "error": error_msg
        }


async def _execute_research(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行技术调研"""
    research_requirements = arguments.get("research_requirements", "")

    if not research_requirements:
        return {
            "success": False,
            "error": "research_requirements is required"
        }

    from agent.shared import shared_state

    # 利用pocketflow设计：提前在字典中写入数据，格式化为流程期望的格式
    shared_state.data["research_requirements"] = research_requirements
    # ResearchFlow期望structured_requirements，所以我们创建一个基础结构
    shared_state.data["structured_requirements"] = {
        "project_overview": {
            "title": "技术调研项目",
            "description": research_requirements
        },
        "functional_requirements": {
            "core_features": []
        }
    }

    # 创建并执行异步流程（使用pocketflow字典）
    flow = ResearchFlow()
    success = await flow.run_async(shared_state.data)

    if success:
        return {
            "success": True,
            "result": shared_state.research_findings,
            "tool_name": "research"
        }
    else:
        error_msg = shared_state.data.get('last_error', {}).get('error_message', "技术调研执行失败")
        return {
            "success": False,
            "error": error_msg
        }


async def _execute_architecture_design(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行架构设计"""
    structured_requirements = arguments.get("structured_requirements")
    confirmation_document = arguments.get("confirmation_document")
    research_findings = arguments.get("research_findings")

    if not structured_requirements:
        return {
            "success": False,
            "error": "structured_requirements is required"
        }

    from agent.shared import shared_state

    # 利用pocketflow设计：提前在字典中写入数据
    shared_state.data["structured_requirements"] = structured_requirements
    if confirmation_document:
        shared_state.data["confirmation_document"] = confirmation_document
    if research_findings:
        shared_state.data["research_findings"] = research_findings

    # 创建并执行异步流程（使用pocketflow字典）
    flow = ArchitectureFlow()
    success = await flow.run_async(shared_state.data)

    if success:
        return {
            "success": True,
            "result": shared_state.data.get("agent_design_document"),
            "tool_name": "architecture_design"
        }
    else:
        error_msg = shared_state.data.get('last_error', {}).get('error_message', "架构设计执行失败")
        return {
            "success": False,
            "error": error_msg
        }


def get_tool_by_name(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    根据名称获取工具定义
    
    Args:
        tool_name: 工具名称
        
    Returns:
        工具定义或None
    """
    tools = get_agent_function_definitions()
    for tool in tools:
        if tool["function"]["name"] == tool_name:
            return tool
    return None


def validate_tool_arguments(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证工具参数
    
    Args:
        tool_name: 工具名称
        arguments: 参数字典
        
    Returns:
        验证结果 {"valid": bool, "errors": List[str]}
    """
    tool_def = get_tool_by_name(tool_name)
    if not tool_def:
        return {"valid": False, "errors": [f"Unknown tool: {tool_name}"]}
    
    errors = []
    required_params = tool_def["function"]["parameters"].get("required", [])
    
    # 检查必需参数
    for param in required_params:
        if param not in arguments:
            errors.append(f"Missing required parameter: {param}")
    
    return {"valid": len(errors) == 0, "errors": errors}


# 便捷函数
async def call_requirements_analysis(user_input: str) -> Dict[str, Any]:
    """便捷的需求分析调用"""
    return await execute_agent_tool("requirements_analysis", {"user_input": user_input})


async def call_short_planning(structured_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """便捷的短期规划调用"""
    return await execute_agent_tool("short_planning", {"structured_requirements": structured_requirements})


async def call_research(research_requirements: str) -> Dict[str, Any]:
    """便捷的技术调研调用"""
    return await execute_agent_tool("research", {"research_requirements": research_requirements})


async def call_architecture_design(
    structured_requirements: Dict[str, Any],
    confirmation_document: Optional[Dict[str, Any]] = None,
    research_findings: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """便捷的架构设计调用"""
    arguments = {"structured_requirements": structured_requirements}
    if confirmation_document:
        arguments["confirmation_document"] = confirmation_document
    if research_findings:
        arguments["research_findings"] = research_findings

    return await execute_agent_tool("architecture_design", arguments)
