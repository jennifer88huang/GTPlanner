"""
Agent Function Calling工具包装器

将现有的子Agent节点直接包装为OpenAI Function Calling工具，
保持现有流程逻辑不变，只是提供Function Calling接口。
"""


from typing import Dict, List, Any, Optional

# 导入现有的子Agent流程
from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow
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
                "name": "short_planning",
                "description": "基于结构化的项目需求，生成一份精炼的、用于和用户确认项目核心范围与颗粒度的短文档",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "structured_requirements": {
                            "type": "object",
                            "description": "结构化的项目需求数据",
                            "properties": {
                                "project_overview": {
                                    "type": "object",
                                    "description": "项目概览信息",
                                    "properties": {
                                        "title": {"type": "string", "description": "项目标题"},
                                        "description": {"type": "string", "description": "项目描述"},
                                        "objectives": {"type": "array", "description": "项目目标"},
                                        "target_users": {"type": "array", "description": "目标用户"},
                                        "success_criteria": {"type": "array", "description": "成功标准"}
                                    },
                                    "required": ["title", "description"]
                                },
                                "functional_requirements": {
                                    "type": "object",
                                    "description": "功能需求",
                                    "properties": {
                                        "core_features": {
                                            "type": "array",
                                            "description": "核心功能列表",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {"type": "string", "description": "功能名称"},
                                                    "description": {"type": "string", "description": "功能描述"},
                                                    "priority": {"type": "string", "description": "优先级"}
                                                }
                                            }
                                        }
                                    }
                                }
                            },
                            "required": ["project_overview", "functional_requirements"]
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
                "description": "基于关键词列表进行技术调研和解决方案研究，职责专一，只负责搜索和分析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要调研的关键词列表，例如：['React框架', 'Node.js后端', '数据库设计']"
                        },
                        "focus_areas": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "调研关注点，例如：['技术选型', '性能优化', '最佳实践', '架构设计']"
                        },
                        "project_context": {
                            "type": "string",
                            "description": "项目背景信息，帮助调研更有针对性"
                        }
                    },
                    "required": ["keywords", "focus_areas"]
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
                            "description": "项目需求信息，包含项目概览和功能需求等结构化数据"
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
        if tool_name == "short_planning":
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



async def _execute_short_planning(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行短期规划"""
    user_input = arguments.get("user_input", "")
    structured_requirements = arguments.get("structured_requirements")

    if not user_input and not structured_requirements:
        return {
            "success": False,
            "error": "user_input or structured_requirements is required"
        }

    from agent.shared import shared_state

    # 创建pocketflow字典格式的数据
    flow_data = {
        "user_input": user_input,
        "structured_requirements": structured_requirements or {}
    }

    # 创建并执行异步流程（使用pocketflow字典）
    flow = ShortPlanningFlow()
    success = await flow.run_async(flow_data)

    if success:
        # 从flow_data中获取结果
        confirmation_document = flow_data.get("confirmation_document", {})

        # 更新shared_state
        shared_state.set_value("confirmation_document", confirmation_document)

        return {
            "success": True,
            "result": confirmation_document,
            "tool_name": "short_planning"
        }
    else:
        error_msg = flow_data.get('last_error', {}).get('error_message', "短期规划执行失败")
        return {
            "success": False,
            "error": error_msg
        }


async def _execute_research(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """执行技术调研 - 使用ProcessResearch节点"""
    keywords = arguments.get("keywords", [])
    focus_areas = arguments.get("focus_areas", [])
    project_context = arguments.get("project_context", "")

    # 参数验证
    if not keywords:
        return {
            "success": False,
            "error": "keywords is required and cannot be empty"
        }

    if not focus_areas:
        return {
            "success": False,
            "error": "focus_areas is required and cannot be empty"
        }

    try:
        print(f"🔍 开始技术调研")
        print(f"📋 关键词: {keywords}")
        print(f"🎯 关注点: {focus_areas}")
        print(f"📝 项目背景: {project_context}")

        # 创建pocketflow字典格式的数据
        flow_data = {
            "research_keywords": keywords,
            "focus_areas": focus_areas,
            "project_context": project_context
        }

        # 创建并执行ProcessResearch节点
        from agent.subflows.research.nodes.process_research_node import ProcessResearch

        process_node = ProcessResearch()

        # 执行prep阶段
        prep_result = await process_node.prep_async(flow_data)

        # 执行exec阶段
        exec_result = await process_node.exec_async(prep_result)

        # 执行post阶段
        await process_node.post_async(flow_data, prep_result, exec_result)

        # 检查执行结果
        if exec_result.get("processing_success", False):
            return {
                "success": True,
                "result": exec_result.get("result"),  # 直接从exec_result获取研究结果
                "tool_name": "research",
                "keywords_processed": len(keywords),
                "focus_areas": focus_areas
            }
        else:
            error_msg = exec_result.get("error", "研究处理失败")
            return {
                "success": False,
                "error": error_msg
            }

    except Exception as e:
        print(f"❌ 技术调研执行失败: {e}")
        return {
            "success": False,
            "error": f"Research execution failed: {str(e)}"
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

    # 创建pocketflow字典格式的数据
    flow_data = {
        "structured_requirements": structured_requirements
    }

    if confirmation_document:
        flow_data["confirmation_document"] = confirmation_document
    if research_findings:
        flow_data["research_findings"] = research_findings

    # 创建并执行异步流程（使用pocketflow字典）
    flow = ArchitectureFlow()
    success = await flow.run_async(flow_data)

    if success:
        # 从flow_data中获取结果
        agent_design_document = flow_data.get("agent_design_document", {})

        # 更新shared_state
        shared_state.set_value("agent_design_document", agent_design_document)

        return {
            "success": True,
            "result": agent_design_document,
            "tool_name": "architecture_design"
        }
    else:
        error_msg = flow_data.get('last_error', {}).get('error_message', "架构设计执行失败")
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
async def call_short_planning(structured_requirements: Dict[str, Any]) -> Dict[str, Any]:
    """便捷的短期规划调用"""
    return await execute_agent_tool("short_planning", {"structured_requirements": structured_requirements})


async def call_research(keywords: List[str], focus_areas: List[str], project_context: str = "") -> Dict[str, Any]:
    """便捷的技术调研调用 - 基于关键词和关注点"""
    return await execute_agent_tool("research", {
        "keywords": keywords,
        "focus_areas": focus_areas,
        "project_context": project_context
    })


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
