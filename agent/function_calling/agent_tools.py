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
                "description": "生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_requirements": {
                            "type": "string",
                            "description": "用户的原始需求描述"
                        },
                        "previous_planning": {
                            "type": "string",
                            "description": "上一版本的短规划文档"
                        },
                        "improvement_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要改进的点或新的需求"
                        }
                    },
                    "required": ["user_requirements"]
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
                            "description": "结构化的项目需求信息",
                            "properties": {
                                "project_name": {"type": "string", "description": "项目名称"},
                                "main_functionality": {"type": "string", "description": "主要功能描述"},
                                "input_format": {"type": "string", "description": "输入格式"},
                                "output_format": {"type": "string", "description": "输出格式"},
                                "technical_requirements": {"type": "array", "items": {"type": "string"}, "description": "技术要求列表"}
                            },
                            "required": ["project_name", "main_functionality"]
                        },
                        "confirmation_document": {
                            "type": "string",
                            "description": "项目规划确认文档，通常来自short_planning工具的输出结果",
                            "required": False
                        },
                        "research_findings": {
                            "type": "object",
                            "description": "技术调研结果",
                            "properties": {
                                "topics": {"type": "array", "items": {"type": "string"}, "description": "调研主题列表"},
                                "results": {"type": "array", "description": "调研结果列表"},
                                "summary": {"type": "string", "description": "调研总结"}
                            },
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
    user_requirements = arguments.get("user_requirements", "")
    previous_planning = arguments.get("previous_planning", "")
    improvement_points = arguments.get("improvement_points", [])

    if not user_requirements:
        return {
            "success": False,
            "error": "user_requirements is required"
        }

    # 🔧 方案B：通过state_manager更新状态，工具只返回结果

    # 创建pocketflow字典格式的数据
    flow_data = {
        "user_requirements": user_requirements,
        "previous_planning": previous_planning,
        "improvement_points": improvement_points
    }

    try:
        # 创建并执行异步流程（使用pocketflow字典）
        flow = ShortPlanningFlow()
        success = await flow.run_async(flow_data)

        if success:
            # 从flow_data中获取结果
            planning_document = flow_data.get("planning_document", {})

            # 🔧 方案B：只返回结果，状态更新由state_manager处理
            return {
                "success": True,
                "result": planning_document,
                "tool_name": "short_planning"
            }
        else:
            error_msg = flow_data.get('last_error', {}).get('error_message', "短期规划执行失败")
            return {
                "success": False,
                "error": error_msg
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"短期规划执行异常: {str(e)}"
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

        # 🔧 修复：使用完整的ResearchFlow而不是直接调用节点
        from agent.subflows.research.flows.research_flow import ResearchFlow

        # 创建pocketflow字典格式的数据（使用新的参数格式）
        flow_data = {
            "research_keywords": keywords,
            "focus_areas": focus_areas,
            "project_context": project_context
        }

        # 创建并执行完整的研究流程（带tracing）
        flow = ResearchFlow()
        success = await flow.run_async(flow_data)

        if success:
            # 从flow_data中获取结果
            research_findings = flow_data.get("research_findings", {})

            return {
                "success": True,
                "result": research_findings,
                "tool_name": "research",
                "keywords_processed": len(keywords),
                "focus_areas": focus_areas
            }
        else:
            error_msg = flow_data.get('research_error', "研究流程执行失败")
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

    # 🔧 方案B：通过state_manager更新状态，工具只返回结果

    # 创建pocketflow字典格式的数据
    flow_data = {
        "structured_requirements": structured_requirements
    }

    if confirmation_document:
        flow_data["confirmation_document"] = confirmation_document
    if research_findings:
        flow_data["research_findings"] = research_findings

    try:
        # 创建并执行异步流程（使用pocketflow字典）
        flow = ArchitectureFlow()
        result = await flow.run_async(flow_data)

        # 🔧 修复：检查流程是否成功执行，以及是否有结果数据
        agent_design_document = flow_data.get("agent_design_document", {})

        # 判断成功的条件：流程执行完成且有设计文档结果
        if result and agent_design_document:
            # 🔧 方案B：只返回结果，状态更新由state_manager处理
            return {
                "success": True,
                "result": agent_design_document,
                "tool_name": "architecture_design"
            }
        else:
            # 检查是否有错误信息
            error_msg = flow_data.get('last_error', {}).get('error_message') or \
                       flow_data.get('architecture_flow_error') or \
                       "架构设计执行失败：未生成设计文档"
            return {
                "success": False,
                "error": error_msg
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"架构设计执行异常: {str(e)}"
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
async def call_short_planning(
    user_requirements: str,
    previous_planning: str = "",
    improvement_points: List[str] = None
) -> Dict[str, Any]:
    """便捷的短期规划调用"""
    arguments = {"user_requirements": user_requirements}
    if previous_planning:
        arguments["previous_planning"] = previous_planning
    if improvement_points:
        arguments["improvement_points"] = improvement_points

    return await execute_agent_tool("short_planning", arguments)


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
