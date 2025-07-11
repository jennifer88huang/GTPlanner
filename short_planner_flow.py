import asyncio
import sys

from pocketflow import AsyncFlow, AsyncNode

from utils.call_llm import call_llm_async
from utils.multilingual_utils import determine_language, get_localized_prompt


class InputRequirementNode(AsyncNode):
    async def exec_async(self, _):
        pass
        # print("请输入你的简短需求描述：")
        # user_req = input().strip()
        # return user_req

    async def post_async(self, shared, prep_res, exec_res):
        # shared["requirement"] = shared["user_input"]["natural_language"]
        # 记录用户需求到history
        shared.setdefault("history", []).append(
            {"type": "requirement", "content": exec_res}
        )
        return "default"


class GenerateStepsNode(AsyncNode):
    async def prep_async(self, shared):
        # Determine language from user input and preferences
        user_input = shared.get("requirement", "")
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")

        language = determine_language(user_input, user_preference, request_language)

        return {"requirement": user_input, "language": language}

    async def exec_async(self, prep_data):
        req = prep_data["requirement"]
        language = prep_data["language"]

        # Get localized prompt template
        prompt = get_localized_prompt("generate_steps", language, req=req)

        return await call_llm_async(prompt)

    async def post_async(self, shared, prep_res, exec_res):
        shared["steps"] = exec_res
        # Store the detected language for future use
        shared["language"] = prep_res["language"]
        # 记录初始步骤到history，标记为V1
        shared.setdefault("history", []).append(
            {"type": "steps", "version": 1, "content": exec_res}
        )
        return "default"


class ReviewNode(AsyncNode):
    async def prep_async(self, shared):
        print("\n===== 当前步骤化流程 =====\n")
        print(shared["steps"])
        print(
            "\n请审查上面的流程，如需修改请描述你的修改意见（直接回车表示满意并结束）："
        )
        return None

    async def exec_async(self, _):
        feedback = input().strip()
        return feedback

    async def post_async(self, shared, prep_res, exec_res):
        shared["feedback"] = exec_res
        # 记录用户反馈到history
        shared.setdefault("history", []).append(
            {
                "type": "feedback",
                "version": shared.get("version", 1),
                "content": exec_res,
            }
        )
        if exec_res:
            return "optimize"
        else:
            return "finalize"


class OptimizeNode(AsyncNode):
    async def prep_async(self, shared):
        # Get current version and determine language
        version = shared.get("version", 1)

        # Determine language from feedback or use stored language
        feedback = shared.get("feedback", "")
        stored_language = shared.get("language")
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")

        # Use stored language if available, otherwise detect from feedback
        if stored_language:
            language = stored_language
        else:
            language = determine_language(feedback, user_preference, request_language)
            shared["language"] = language  # Store for future use

        return {
            "steps": shared["steps"],
            "feedback": feedback,
            "version": version,
            "language": language,
        }

    async def exec_async(self, prep_data):
        steps = prep_data["steps"]
        feedback = prep_data["feedback"]
        version = prep_data["version"]
        language = prep_data["language"]

        prev_version = version

        # Get localized prompt template
        prompt = get_localized_prompt(
            "optimize_steps",
            language,
            steps=steps,
            feedback=feedback,
            prev_version=prev_version,
        )

        return await call_llm_async(prompt)

    async def post_async(self, shared, prep_res, exec_res):
        # 递增版本号
        shared["version"] = shared.get("version", 1) + 1
        # 记录优化后的流程到history，标记新版本号
        shared.setdefault("history", []).append(
            {"type": "steps", "version": shared["version"], "content": exec_res}
        )
        shared["steps"] = exec_res
        return "review"


class GenerateStepsStreamNode(AsyncNode):
    """流式版本的步骤生成节点"""

    async def prep_async(self, shared):
        # Determine language from user input and preferences
        user_input = shared.get("requirement", "")
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")

        language = determine_language(user_input, user_preference, request_language)

        return {"requirement": user_input, "language": language}

    async def exec_async_stream(self, prep_data):
        """流式生成步骤"""
        from utils.call_llm import call_llm_stream_async

        req = prep_data["requirement"]
        language = prep_data["language"]

        # Get localized prompt template
        prompt = get_localized_prompt("generate_steps", language, req=req)

        # 流式调用LLM
        async for chunk in call_llm_stream_async(prompt):
            yield chunk

    async def exec_async(self, prep_data):
        """非流式版本作为fallback"""
        req = prep_data["requirement"]
        language = prep_data["language"]

        # Get localized prompt template
        prompt = get_localized_prompt("generate_steps", language, req=req)

        return await call_llm_async(prompt)

    async def post_async(self, shared, prep_res, exec_res):
        shared["steps"] = exec_res
        # Store the detected language for future use
        shared["language"] = prep_res["language"]
        # 记录初始步骤到history，标记为V1
        shared.setdefault("history", []).append(
            {"type": "steps", "version": 1, "content": exec_res}
        )
        return "default"


class OptimizeStreamNode(AsyncNode):
    """流式版本的优化节点"""

    async def prep_async(self, shared):
        # Get current version and determine language
        version = shared.get("version", 1)

        # Determine language from feedback or use stored language
        feedback = shared.get("feedback", "")
        stored_language = shared.get("language")
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")

        # Use stored language if available, otherwise detect from feedback
        if stored_language:
            language = stored_language
        else:
            language = determine_language(feedback, user_preference, request_language)
            shared["language"] = language  # Store for future use

        return {
            "steps": shared["steps"],
            "feedback": feedback,
            "version": version,
            "language": language,
        }

    async def exec_async_stream(self, prep_data):
        """流式优化步骤"""
        from utils.call_llm import call_llm_stream_async

        steps = prep_data["steps"]
        feedback = prep_data["feedback"]
        version = prep_data["version"]
        language = prep_data["language"]

        prev_version = version

        # Get localized prompt template
        prompt = get_localized_prompt(
            "optimize_steps",
            language,
            steps=steps,
            feedback=feedback,
            prev_version=prev_version,
        )

        # 流式调用LLM
        async for chunk in call_llm_stream_async(prompt):
            yield chunk

    async def exec_async(self, prep_data):
        """非流式版本作为fallback"""
        steps = prep_data["steps"]
        feedback = prep_data["feedback"]
        version = prep_data["version"]
        language = prep_data["language"]

        prev_version = version

        # Get localized prompt template
        prompt = get_localized_prompt(
            "optimize_steps",
            language,
            steps=steps,
            feedback=feedback,
            prev_version=prev_version,
        )

        return await call_llm_async(prompt)

    async def post_async(self, shared, prep_res, exec_res):
        # 递增版本号
        shared["version"] = shared.get("version", 1) + 1
        # 记录优化后的流程到history，标记新版本号
        shared.setdefault("history", []).append(
            {"type": "steps", "version": shared["version"], "content": exec_res}
        )
        shared["steps"] = exec_res
        return "review"


class FinalizeNode(AsyncNode):
    async def prep_async(self, shared):
        return shared["steps"]

    async def exec_async(self, steps):
        print("\n===== 最终确定的步骤化流程 =====\n")
        print(steps)
        return steps

    async def post_async(self, shared, prep_res, exec_res):
        shared["final_steps"] = exec_res
        # 记录最终确定的流程到history
        shared.setdefault("history", []).append(
            {
                "type": "final_steps",
                "version": shared.get("version", 1),
                "content": exec_res,
            }
        )
        return None


def create_short_planner_flow():
    input_node = InputRequirementNode()
    gen_node = GenerateStepsNode()
    review_node = ReviewNode()
    optimize_node = OptimizeNode()
    finalize_node = FinalizeNode()

    input_node >> gen_node >> review_node
    review_node - "optimize" >> optimize_node
    review_node - "finalize" >> finalize_node
    optimize_node - "review" >> review_node

    return AsyncFlow(start=input_node)


async def main():
    shared = {"history": [], "version": 1}
    flow = create_short_planner_flow()
    await flow.run_async(shared)


if __name__ == "__main__":
    asyncio.run(main())
