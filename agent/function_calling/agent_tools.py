"""
Agent Function Calling工具包装器

将现有的子Agent节点直接包装为OpenAI Function Calling工具，
保持现有流程逻辑不变，只是提供Function Calling接口。
"""


from typing import Dict, List, Any, Optional

# 导入现有的子Agent流程
from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow
from agent.subflows.architecture.flows.architecture_flow import ArchitectureFlow
from agent.subflows.research.flows.research_flow import ResearchFlow

# 导入新的工具节点
from agent.nodes.node_tool_index import NodeToolIndex
from agent.nodes.node_tool_recommend import NodeToolRecommend



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
                "description": "基于用户需求和推荐工具生成精炼的短规划文档，用于确认项目核心范围与颗粒度。工具会自动获取项目状态中的相关信息（如推荐工具、之前的规划等），可以多次调用来逐步细化和完善项目范围。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_requirements": {
                            "type": "string",
                            "description": "用户的原始需求描述或新的需求补充"
                        },
                        "improvement_points": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要改进的点或新的需求（可选）"
                        }
                    },
                    "required": ["user_requirements"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "tool_recommend",
                "description": "基于查询文本推荐相关的API、第三方库等技术工具。在进行技术调研和项目规划时使用，确保推荐的技术栈在平台支持范围内。应该在调用research工具之前使用，为下游AI coding服务选择合适的技术栈。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "查询文本，描述需要的工具功能或技术需求"
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "返回的推荐工具数量，默认5个",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20
                        },
                        "tool_types": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["PYTHON_PACKAGE", "APIS"]
                            },
                            "description": "工具类型过滤列表，可选值：PYTHON_PACKAGE（Python包）、APIS（API服务）"
                        },
                        "use_llm_filter": {
                            "type": "boolean",
                            "description": "是否使用大模型筛选，默认true",
                            "default": True
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "research",
                "description": "基于关键词列表进行技术调研和解决方案研究，职责专一，只负责搜索和分析。这是一个可选工具，仅在需要技术调研时使用。建议在调用此工具前先使用tool_recommend工具获取平台支持的技术栈。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "需要调研的关键词列表，例如：['rag', '数据库设计']"
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
                "description": "基于之前工具的执行结果（short_planning、research、tool_recommend）生成详细的系统架构设计方案。此工具会自动获取项目状态中的所有必要信息，同时支持用户直接传入项目需求描述。生成的完整设计文档会自动输出到文件中，调用后只需提示用户查看生成的文档即可。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_requirements": {
                            "type": "string",
                            "description": "用户的项目需求描述，用于指导架构设计。如果不提供，将使用之前short_planning工具的结果。"
                        }
                    },
                    "required": [
                        "user_requirements"
                    ]
                }
            }
        }
    ]


async def execute_agent_tool(tool_name: str, arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
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
            return await _execute_short_planning(arguments, shared)
        elif tool_name == "tool_recommend":
            return await _execute_tool_recommend(arguments, shared)
        elif tool_name == "research":
            return await _execute_research(arguments, shared)
        elif tool_name == "architecture_design":
            return await _execute_architecture_design(arguments, shared)
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



async def _execute_short_planning(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行短期规划 - 基于项目状态和用户需求"""
    user_requirements = arguments.get("user_requirements", "")
    improvement_points = arguments.get("improvement_points", [])

    # 从shared字典中获取之前的规划结果
    previous_planning = ""
    if shared and "short_planning" in shared:
        previous_planning_data = shared["short_planning"]
        if isinstance(previous_planning_data, str):
            previous_planning = previous_planning_data

    # 如果没有用户需求且没有改进点，但有shared上下文，则可以继续执行
    if not user_requirements and not improvement_points and not shared:
        return {
            "success": False,
            "error": "user_requirements or improvement_points is required when no project context is available"
        }

    try:
        # 直接在shared字典中添加工具参数，避免数据隔离
        if shared is None:
            shared = {}

        # 添加工具参数到shared字典
        shared["user_requirements"] = user_requirements
        shared["previous_planning"] = previous_planning
        shared["improvement_points"] = improvement_points

        # 如果没有明确的用户需求，但有推荐工具，基于现有状态进行规划优化
        if not user_requirements and shared.get("recommended_tools"):
            shared["user_requirements"] = "基于推荐工具优化项目规划"

        # 直接使用shared字典执行流程，确保状态传递
        flow = ShortPlanningFlow()
        result = await flow.run_async(shared)

        # 检查流程是否成功完成（返回"planning_complete"表示成功）
        if result == "planning_complete":
            # 从shared字典中获取结果（PocketFlow已经直接修改了shared）
            short_planning = shared.get("short_planning", {})

            return {
                "success": True,
                "result": short_planning,
                "tool_name": "short_planning"
            }
        else:
            # 流程失败或返回错误
            error_msg = shared.get('planning_error', shared.get('short_planning_flow_error', f"短期规划执行失败，返回值: {result}"))
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "short_planning"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"短期规划执行异常: {str(e)}"
        }


async def _execute_tool_recommend(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行工具推荐 - 每次都先创建索引，然后进行推荐"""
    query = arguments.get("query", "")
    top_k = arguments.get("top_k", 5)
    tool_types = arguments.get("tool_types", [])
    use_llm_filter = arguments.get("use_llm_filter", True)

    # 参数验证
    if not query:
        return {
            "success": False,
            "error": "query is required and cannot be empty"
        }

    try:
        # 1. 先创建索引
        from agent.nodes.node_tool_index import NodeToolIndex
        index_node = NodeToolIndex()

        index_shared = {
            "tools_dir": "tools",
            "index_name": "tools_index",
            "force_reindex": True
        }

        # 创建索引（异步）
        index_prep_result = await index_node.prep_async(index_shared)
        if "error" in index_prep_result:
            return {
                "success": False,
                "error": f"Failed to prepare index: {index_prep_result['error']}"
            }

        index_exec_result = await index_node.exec_async(index_prep_result)
        created_index_name = index_exec_result.get("index_name", "tools_index")

        print(f"✅ 成功创建索引: {created_index_name}")

        # 等待索引刷新
        import time
        time.sleep(2)

        # 2. 执行工具推荐
        from agent.nodes.node_tool_recommend import NodeToolRecommend
        recommend_node = NodeToolRecommend()

        # 直接在shared字典中添加工具参数，避免数据隔离
        if shared is None:
            shared = {}

        # 添加工具参数到shared字典
        shared["query"] = query
        shared["top_k"] = top_k
        shared["index_name"] = created_index_name  # 使用刚创建的索引名
        shared["tool_types"] = tool_types
        shared["min_score"] = 0.1
        shared["use_llm_filter"] = use_llm_filter

        # 执行推荐节点流程（异步），直接使用shared字典
        prep_result = await recommend_node.prep_async(shared)
        if "error" in prep_result:
            return {
                "success": False,
                "error": prep_result["error"]
            }

        exec_result = await recommend_node.exec_async(prep_result)

        # 后处理：结果会直接写入shared字典
        await recommend_node.post_async(shared, prep_result, exec_result)

        return {
            "success": True,
            "result": {
                "recommended_tools": exec_result["recommended_tools"],
                "total_found": exec_result["total_found"],
                "search_time_ms": exec_result["search_time"],
                "query_used": exec_result["query_used"],
                "index_name": created_index_name
            },
            "tool_name": "tool_recommend"
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"工具推荐执行异常: {str(e)}"
        }


async def _execute_research(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行技术调研 - 使用ResearchFlow"""
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
        # 使用完整的ResearchFlow
     

        # 直接在shared字典中添加工具参数，避免数据隔离
        if shared is None:
            shared = {}

        # 添加工具参数到shared字典
        shared["research_keywords"] = keywords
        shared["focus_areas"] = focus_areas
        shared["project_context"] = project_context

        # 直接使用shared字典执行流程，确保状态传递
        flow = ResearchFlow()
        success = await flow.run_async(shared)

        if success:
            # 从shared字典中获取结果（PocketFlow已经直接修改了shared）
            research_findings = shared.get("research_findings", {})

            return {
                "success": True,
                "result": research_findings,
                "tool_name": "research",
                "keywords_processed": len(keywords),
                "focus_areas": focus_areas
            }
        else:
            error_msg = shared.get('research_error', "研究流程执行失败")
            return {
                "success": False,
                "error": error_msg,
                "tool_name": "research"
            }

    except Exception as e:
        print(f"❌ 技术调研执行失败: {e}")
        return {
            "success": False,
            "error": f"Research execution failed: {str(e)}"
        }





async def _execute_architecture_design(arguments: Dict[str, Any], shared: Dict[str, Any] = None) -> Dict[str, Any]:
    """执行架构设计 - 基于shared字典中的状态数据和用户需求参数"""

    # 验证shared字典是否可用
    if not shared:
        return {
            "success": False,
            "error": "shared context is required for architecture design"
        }

    # 验证必需的状态数据是否存在
    if not shared.get("short_planning"):
        return {
            "success": False,
            "error": "short_planning results are required for architecture design"
        }

    # 从参数中获取用户需求，如果没有则使用short_planning结果
    user_requirements = arguments.get("user_requirements", shared.get("short_planning", ""))
    if user_requirements:
        shared["user_requirements"] = user_requirements

    try:
        # 直接使用shared字典执行流程，确保状态传递
        flow = ArchitectureFlow()
        result = await flow.run_async(shared)

        # 从shared字典中获取结果（PocketFlow已经直接修改了shared）
        agent_design_document = shared.get("agent_design_document", {})

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
            error_msg = shared.get('last_error', {}).get('error_message') or \
                       shared.get('architecture_flow_error') or \
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
    user_requirements: str = "",
    improvement_points: List[str] = None
) -> Dict[str, Any]:
    """便捷的短期规划调用 - 自动使用项目状态中的数据"""
    arguments = {}
    if user_requirements:
        arguments["user_requirements"] = user_requirements
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


async def call_tool_recommend(
    query: str,
    top_k: int = 5,
    tool_types: List[str] = None,
    use_llm_filter: bool = True
) -> Dict[str, Any]:
    """便捷的工具推荐调用"""
    arguments = {
        "query": query,
        "top_k": top_k,
        "use_llm_filter": use_llm_filter
    }
    if tool_types:
        arguments["tool_types"] = tool_types

    return await execute_agent_tool("tool_recommend", arguments)


async def call_architecture_design(user_requirements: str = None) -> Dict[str, Any]:
    """便捷的架构设计调用 - 支持传入用户需求或自动使用项目状态中的数据"""
    arguments = {}
    if user_requirements:
        arguments["user_requirements"] = user_requirements
    return await execute_agent_tool("architecture_design", arguments)
