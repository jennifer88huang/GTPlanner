import asyncio
from typing import Any, Optional

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pocketflow import AsyncFlow
from pydantic import BaseModel

from nodes import AsyncDesignOptimizationNode, AsyncRequirementsAnalysisNode
from short_planner_flow import (
    GenerateStepsNode,
    OptimizeNode,
    create_short_planner_flow,
)

planning_router = APIRouter(prefix="/planning", tags=["planning"])


async def encode_stream_generator(generator):
    """确保流式输出正确编码为UTF-8"""
    async for chunk in generator:
        if isinstance(chunk, str):
            yield chunk.encode('utf-8')
        else:
            yield chunk


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


async def short_planning_stream(body: ShortPlanningRequest):
    """流式短规划生成 - 包含和非流式版本相同的所有功能"""
    requirement = body.requirement
    previous_flow = body.previous_flow
    language = body.language
    user_id = body.user_id

    if not requirement:
        yield "data: [ERROR_START]\n"
        yield "data: ❌ Missing 'requirement' in request body.\n"
        yield "data: [ERROR_END]\n\n"
        return

    try:
        # Prepare shared context with multilingual support (和非流式版本相同)
        shared_base = {
            "requirement": requirement,
            "request_language": language,
            "user_id": user_id,
            "history": [],
            "version": 1,
        }

        # Add user language preference if available (和非流式版本相同)
        if user_id:
            from utils.config_manager import get_language_preference

            user_preference = get_language_preference(user_id)
            if user_preference:
                shared_base["user_language_preference"] = user_preference

        if previous_flow and previous_flow != "":
            # User provided previous flow, go directly to optimization node (流式版本)
            shared = shared_base.copy()
            shared["steps"] = previous_flow
            shared["feedback"] = requirement  # Use new requirement as optimization feedback

            from short_planner_flow import OptimizeStreamNode
            optimize_node = OptimizeStreamNode()
            prep_result = await optimize_node.prep_async(shared)

            # 流式输出优化结果
            yield "data: [SHORT_PLAN_START]\n"

            full_response = ""
            async for chunk in optimize_node.exec_async_stream(prep_result):
                full_response += chunk
                # 使用占位符保护换行符，避免与SSE协议冲突
                protected_chunk = chunk.replace('\n', '<|newline|>')
                yield f"data: {protected_chunk}\n"

            # 保存结果到shared context
            await optimize_node.post_async(shared, prep_result, full_response)

            yield "data: [SHORT_PLAN_END]\n\n"
        else:
            # Generate new flow (流式版本)
            shared = shared_base.copy()

            from short_planner_flow import GenerateStepsStreamNode
            generate_node = GenerateStepsStreamNode()
            prep_result = await generate_node.prep_async(shared)

            # 流式输出生成结果
            yield "data: [SHORT_PLAN_START]\n"

            full_response = ""
            async for chunk in generate_node.exec_async_stream(prep_result):
                full_response += chunk
                # 使用占位符保护换行符，避免与SSE协议冲突
                protected_chunk = chunk.replace('\n', '<|newline|>')
                yield f"data: {protected_chunk}\n"

            # 保存结果到shared context
            await generate_node.post_async(shared, prep_result, full_response)

            yield "data: [SHORT_PLAN_END]\n\n"

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in short_planning_stream: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield "data: [ERROR_START]\n"
        yield "data: ❌ An internal error occurred while generating planning. Please try again later.\n"
        yield "data: [ERROR_END]\n\n"


async def long_planning_stream(body: LongPlanningRequest):
    """流式长文档生成 - 包含和非流式版本相同的所有功能"""
    requirement = body.requirement
    previous_flow = body.previous_flow
    design_doc = body.design_doc
    language = body.language
    user_id = body.user_id

    if not requirement:
        yield "data: [ERROR_START]\n"
        yield "data: ❌ Missing 'requirement' in request body.\n"
        yield "data: [ERROR_END]\n\n"
        return

    try:
        # 导入必要的模块 (AsyncFlow和nodes已在顶部导入)

        # Prepare shared context with multilingual support (和非流式版本相同)
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

        # Add user language preference if available (和非流式版本相同)
        if user_id:
            from utils.config_manager import get_language_preference

            user_preference = get_language_preference(user_id)
            if user_preference:
                shared["user_language_preference"] = user_preference

        # 流式需求分析阶段
        yield "data: [STATUS_START]\n"
        if language == "zh":
            yield "data: 🔍 正在分析需求...\n"
        else:
            yield "data: 🔍 Analyzing requirements...\n"
        yield "data: [STATUS_END]\n\n"

        # 使用流式需求分析节点
        from nodes import AsyncRequirementsAnalysisStreamNode
        requirement_node = AsyncRequirementsAnalysisStreamNode()
        prep_result = await requirement_node.prep_async(shared)

        # 流式输出需求分析过程
        yield "data: [ANALYSIS_START]\n"

        full_analysis = ""
        async for chunk in requirement_node.exec_async_stream(prep_result):
            full_analysis += chunk
            # 使用占位符保护换行符，避免与SSE协议冲突
            protected_chunk = chunk.replace('\n', '<|newline|>')
            yield f"data: {protected_chunk}\n"

        # 保存分析结果
        await requirement_node.post_async(shared, prep_result, full_analysis)

        yield "data: [ANALYSIS_END]\n\n"

        # 发送状态更新
        yield "data: [STATUS_START]\n"
        if language == "zh":
            yield "data: 📝 开始生成设计文档...\n"
        else:
            yield "data: 📝 Generating design document...\n"
        yield "data: [STATUS_END]\n\n"

        # 然后手动运行设计优化节点的流式版本
        from nodes import AsyncDesignOptimizationStreamNode
        design_doc_node = AsyncDesignOptimizationStreamNode()
        prep_result = await design_doc_node.prep_async(shared)

        # 流式输出生成的文档
        yield "data: [LONG_DOC_START]\n"

        # 流式生成并输出文档内容
        full_response = ""
        async for chunk in design_doc_node.exec_async_stream(prep_result):
            full_response += chunk
            # 使用占位符保护换行符，避免与SSE协议冲突
            protected_chunk = chunk.replace('\n', '<|newline|>')
            yield f"data: {protected_chunk}\n"

        # 保存结果到shared context
        await design_doc_node.post_async(shared, prep_result, full_response)

        yield "data: [LONG_DOC_END]\n\n"

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in long_planning_stream: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield "data: [ERROR_START]\n"
        yield "data: ❌ An internal error occurred while generating document. Please try again later.\n"
        yield "data: [ERROR_END]\n\n"


@planning_router.post("/short/stream")
async def short_planning_stream_endpoint(body: ShortPlanningRequest):
    """流式短规划接口"""
    return StreamingResponse(
        encode_stream_generator(short_planning_stream(body)),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )


@planning_router.post("/long/stream")
async def long_planning_stream_endpoint(body: LongPlanningRequest):
    """流式长文档接口"""
    return StreamingResponse(
        encode_stream_generator(long_planning_stream(body)),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )


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
