import asyncio
from typing import Any, Optional

from fastapi import APIRouter
from pocketflow import AsyncFlow
from pydantic import BaseModel

from nodes import AsyncDesignOptimizationNode, AsyncRequirementsAnalysisNode
from short_planner_flow import (
    GenerateStepsNode,
    OptimizeNode,
    create_short_planner_flow,
)

planning_router = APIRouter(prefix="/planning", tags=["planning"])


class ShortPlanningRequest(BaseModel):
    requirement: str
    previous_flow: Optional[Any] = None
    language: Optional[str] = None  # User's preferred language (e.g., 'en', 'zh', 'es')
    user_id: Optional[str] = None  # Optional user identifier for language preferences


class LongPlanningRequest(BaseModel):
    requirement: str
    previous_flow: Optional[Any] = None
    design_doc: Optional[Any] = None
    language: Optional[str] = None  # User's preferred language
    user_id: Optional[str] = None  # Optional user identifier for language preferences


@planning_router.post("/short")
async def short_planning(body: ShortPlanningRequest):
    requirement = body.requirement
    previous_flow = body.previous_flow
    language = body.language
    user_id = body.user_id

    if not requirement:
        return {"error": "Missing 'requirement' in request body."}

    # Prepare shared context with multilingual support
    shared_base = {
        "requirement": requirement,
        "request_language": language,
        "user_id": user_id,
        "history": [],
        "version": 1,
    }

    # Add user language preference if available
    if user_id:
        from utils.config_manager import get_language_preference

        user_preference = get_language_preference(user_id)
        if user_preference:
            shared_base["user_language_preference"] = user_preference

    if previous_flow and previous_flow != "":
        # User provided previous flow, go directly to optimization node
        shared = shared_base.copy()
        shared["steps"] = previous_flow
        shared["feedback"] = requirement  # Use new requirement as optimization feedback

        optimize = OptimizeNode()
        await AsyncFlow(start=optimize).run_async(shared)

        # Determine the language used for response
        response_language = shared.get("language", language or "en")

        return {
            "flow": shared.get("steps", "No flow generated."),
            "language": response_language,
            "user_id": user_id,
        }
    else:
        # Generate new flow
        shared = shared_base.copy()

        generateStepsNode = GenerateStepsNode()
        await AsyncFlow(start=generateStepsNode).run_async(shared)

        # Determine the language used for response
        # Use detected language from shared context, fallback to request language only if not empty, otherwise default to "en"
        response_language = shared.get("language", language if language else "en")

        return {
            "flow": shared.get("steps", "No flow generated."),
            "language": response_language,
            "user_id": user_id,
        }


@planning_router.post("/long")
async def long_planning(body: LongPlanningRequest):
    requirement = body.requirement
    previous_flow = body.previous_flow
    design_doc = body.design_doc
    language = body.language
    user_id = body.user_id

    if not requirement:
        return {"error": "Missing 'requirement' in request body."}

    # Prepare shared context with multilingual support
    shared = {
        "user_input": {
            "processed_natural_language": requirement,
            "processed_documents": design_doc,
        },
        "short_flow_steps": previous_flow,
        "conversation_history": [],
        "request_language": language,
        "user_id": user_id,
    }

    # Add user language preference if available
    if user_id:
        from utils.config_manager import get_language_preference

        user_preference = get_language_preference(user_id)
        if user_preference:
            shared["user_language_preference"] = user_preference

    requirement_node = AsyncRequirementsAnalysisNode()
    design_doc_node = AsyncDesignOptimizationNode()
    requirement_node >> design_doc_node
    await AsyncFlow(start=requirement_node).run_async(shared)

    # Determine the language used for response
    # Use detected language from shared context, fallback to request language only if not empty, otherwise default to "en"
    response_language = shared.get("language", language if language else "en")

    print(shared.get("user_input", {}).get("processed_documents", "No flow generated."))
    return {
        "flow": shared.get("user_input", {}).get(
            "processed_documents", "No flow generated."
        ),
        "language": response_language,
        "user_id": user_id,
    }


# 测试函数
async def test_short_planning():
    """测试 short_planning 函数"""
    print("开始测试 short_planning 函数...")

    # 测试用例1: 基本需求测试
    print("\n测试用例1: 基本需求")
    test_request1 = ShortPlanningRequest(requirement="创建一个简单的待办事项应用")
    try:
        result1 = await short_planning(test_request1)
        print(f"结果1: {result1}")
    except Exception as e:
        print(f"测试1出错: {e}")

    # 测试用例2: 空需求测试
    print("\n测试用例2: 空需求")
    test_request2 = ShortPlanningRequest(requirement="")
    try:
        result2 = await short_planning(test_request2)
        print(f"结果2: {result2}")
    except Exception as e:
        print(f"测试2出错: {e}")

    # 测试用例3: 带有之前流程的优化测试
    print("\n测试用例3: 优化现有流程")
    previous_flow = ["步骤1: 设计界面", "步骤2: 实现功能", "步骤3: 测试"]
    test_request3 = ShortPlanningRequest(
        requirement="增加用户登录功能", previous_flow=previous_flow
    )
    try:
        result3 = await short_planning(test_request3)
        print(f"结果3: {result3}")
    except Exception as e:
        print(f"测试3出错: {e}")

    print("\n测试完成!")


# 如果直接运行此文件，执行测试
if __name__ == "__main__":
    asyncio.run(test_short_planning())
