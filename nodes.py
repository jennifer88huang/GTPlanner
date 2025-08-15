"""
Node definitions for the GTPlanner application.

This module contains various node implementations for different planning tasks.
"""

# from typing import Dict, Any, List  # Unused imports
from pocketflow import AsyncNode
from utils.multilingual_utils import determine_language, get_localized_prompt
from utils.openai_client import get_openai_client


class AsyncInputProcessingNode(AsyncNode):
    """Node that processes user input asynchronously."""

    async def prep_async(self, shared):
        """Prepare data for input processing."""
        return shared.get("user_input", {})

    async def exec_async(self, input_data):
        """Process user input."""
        # Simple input processing - just pass through for now
        return input_data

    async def post_async(self, shared, prep_res, exec_res):
        """Store processed input in shared store."""
        shared["processed_input"] = exec_res
        return "default"


class AsyncDocumentationGenerationNode(AsyncNode):
    """Node that generates documentation asynchronously."""

    async def prep_async(self, shared):
        """Prepare data for documentation generation."""
        language = shared.get("language", "zh")
        return {
            "requirements": shared.get("requirements", ""),
            "design_optimization": shared.get("documentation", ""),
            "language": language
        }

    async def exec_async(self, input_data):
        """Generate documentation using LLM."""
        language = input_data["language"]

        # Get localized prompt template for documentation generation
        prompt = get_localized_prompt(
            "documentation_generation",
            language,
            requirements=input_data["requirements"],
            design_optimization=input_data["design_optimization"]
        )

        # Call LLM to generate documentation
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""
        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """Store generated documentation in shared store."""
        shared["final_documentation"] = exec_res
        return "default"


class AsyncFeedbackProcessingNode(AsyncNode):
    """Node that processes user feedback asynchronously."""

    async def prep_async(self, shared):
        """Prepare data for feedback processing."""
        return {
            "feedback": shared.get("user_feedback", ""),
            "current_documentation": shared.get("final_documentation", ""),
            "language": shared.get("language", "zh")
        }

    async def exec_async(self, input_data):
        """Process user feedback."""
        feedback = input_data["feedback"]

        if not feedback or feedback.strip() == "":
            return "complete"

        # Process feedback and determine next action
        if "修改" in feedback or "优化" in feedback or "改进" in feedback:
            return "new_iteration"
        else:
            return "complete"

    async def post_async(self, shared, prep_res, exec_res):
        """Store feedback processing result."""
        shared["feedback_result"] = exec_res
        return exec_res


class AsyncRequirementsAnalysisNode(AsyncNode):
    """Node that analyzes requirements asynchronously."""

    async def prep_async(self, shared):
        """Prepare data for requirements analysis."""
        # Extract user input
        natural_language = shared["user_input"]["processed_natural_language"]
        short_flow_steps = shared.get("short_flow_steps", "")
        parsed_documents = shared["user_input"]["processed_documents"]

        # Determine language for the analysis
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")
        language = determine_language(natural_language, user_preference, request_language)

        return {
            "natural_language": natural_language,
            "short_flow_steps": short_flow_steps,
            "parsed_documents": parsed_documents,
            "language": language,
        }

    async def exec_async(self, input_data):
        """Analyze requirements using LLM."""
        language = input_data["language"]

        # Get localized prompt template for requirements analysis
        prompt = get_localized_prompt(
            "requirements_analysis",
            language,
            natural_language=input_data["natural_language"],
            short_flow_steps=input_data["short_flow_steps"],
            parsed_documents=input_data["parsed_documents"],
        )

        # Call LLM to analyze requirements
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""

        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """Store analyzed requirements in shared store."""
        shared["requirements"] = exec_res
        # Store the detected language for future use
        shared["language"] = prep_res["language"]
        # Add to conversation history

        return "default"


class AsyncDesignOptimizationNode(AsyncNode):
    """Node that suggests design optimizations asynchronously."""

    async def prep_async(self, shared):
        """Prepare data for design optimization."""
        # Get stored language or detect from user input
        stored_language = shared.get("language")
        if not stored_language:
            # Fallback: detect from user input if language not stored
            user_input = shared["user_input"]["processed_natural_language"]
            user_preference = shared.get("user_language_preference")
            request_language = shared.get("request_language")
            stored_language = determine_language(user_input, user_preference, request_language)
            shared["language"] = stored_language  # Store for future use

        return {
            "requirements": shared["requirements"],
            "conversation_history": shared.get("conversation_history", []),
            "parsed_documents": shared["user_input"]["processed_documents"],
            "user_instructions": shared["user_input"]["processed_natural_language"],
            "short_flow_steps": shared.get("short_flow_steps", ""),
            "language": stored_language,
        }

    async def exec_async(self, input_data):
        """Generate optimization suggestions using LLM."""
        language = input_data["language"]

        # Get localized prompt template for design optimization
        prompt = get_localized_prompt(
            "design_optimization",
            language,
            requirements=input_data["requirements"],
            conversation_history=input_data["conversation_history"],
            parsed_documents=input_data["parsed_documents"],
            user_instructions=input_data["user_instructions"],
            short_flow_steps=input_data["short_flow_steps"],
        )

        # Call LLM to generate optimizations
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""

        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """Store optimization suggestions in shared store."""
        shared["user_input"]["processed_documents"] = exec_res
        shared["documentation"] = exec_res
        # Add to conversation history

        return "default"


class AsyncRequirementsAnalysisStreamNode(AsyncNode):
    """Node that analyzes requirements asynchronously with streaming support."""

    async def prep_async(self, shared):
        """Prepare data for requirements analysis."""
        # 完全按照非流式版本的字段设计
        # Extract user input
        natural_language = shared["user_input"]["processed_natural_language"]
        short_flow_steps = shared.get("short_flow_steps", "")
        parsed_documents = shared["user_input"]["processed_documents"]

        # Determine language for the analysis
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")
        language = determine_language(natural_language, user_preference, request_language)

        return {
            "natural_language": natural_language,
            "short_flow_steps": short_flow_steps,
            "parsed_documents": parsed_documents,
            "language": language,
        }

    async def exec_async_stream(self, input_data):
        """Analyze requirements using streaming LLM."""
        client = get_openai_client()

        language = input_data["language"]

        # Get localized prompt template for requirements analysis
        # 完全按照非流式版本的参数名
        prompt = get_localized_prompt(
            "requirements_analysis",
            language,
            natural_language=input_data["natural_language"],
            short_flow_steps=input_data["short_flow_steps"],
            parsed_documents=input_data["parsed_documents"],
        )

        # Call streaming LLM to analyze requirements
        async for chunk in client.chat_completion_stream(
            messages=[{"role": "user", "content": prompt}]
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def exec_async(self, input_data):
        """Analyze requirements using LLM (non-streaming fallback)."""
        language = input_data["language"]

        # Get localized prompt template for requirements analysis
        # 完全按照非流式版本的参数名
        prompt = get_localized_prompt(
            "requirements_analysis",
            language,
            natural_language=input_data["natural_language"],
            short_flow_steps=input_data["short_flow_steps"],
            parsed_documents=input_data["parsed_documents"],
        )

        # Call LLM to analyze requirements
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""
        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """Store analyzed requirements in shared store."""
        shared["requirements"] = exec_res
        # 保持语言设置，但不覆盖明确的request_language
        # 只有在没有明确request_language时才更新语言设置
        if not shared.get("request_language"):
            shared["language"] = prep_res["language"]
        # Add to conversation history

        return "default"


class AsyncDesignOptimizationStreamNode(AsyncNode):
    """Node that suggests design optimizations asynchronously with streaming support."""

    async def prep_async(self, shared):
        """Prepare data for design optimization."""
        # 优先使用明确的request_language，而不是之前检测存储的语言
        user_input = shared["user_input"]["processed_natural_language"]
        user_preference = shared.get("user_language_preference")
        request_language = shared.get("request_language")

        # 重新确定语言，确保request_language优先级最高
        language = determine_language(user_input, user_preference, request_language)
        shared["language"] = language  # 更新存储的语言

        return {
            "requirements": shared["requirements"],
            "conversation_history": shared.get("conversation_history", []),
            "parsed_documents": shared["user_input"]["processed_documents"],
            "user_instructions": shared["user_input"]["processed_natural_language"],
            "short_flow_steps": shared.get("short_flow_steps", ""),
            "language": language,
        }

    async def exec_async_stream(self, input_data):
        """Generate optimization suggestions using streaming LLM."""
        client = get_openai_client()

        language = input_data["language"]

        # Get localized prompt template for design optimization
        prompt = get_localized_prompt(
            "design_optimization",
            language,
            requirements=input_data["requirements"],
            conversation_history=input_data["conversation_history"],
            parsed_documents=input_data["parsed_documents"],
            user_instructions=input_data["user_instructions"],
            short_flow_steps=input_data["short_flow_steps"],
        )

        # Call streaming LLM to generate optimizations
        async for chunk in client.chat_completion_stream(
            messages=[{"role": "user", "content": prompt}]
        ):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def exec_async(self, input_data):
        """Generate optimization suggestions using LLM (non-streaming fallback)."""
        language = input_data["language"]

        # Get localized prompt template for design optimization
        prompt = get_localized_prompt(
            "design_optimization",
            language,
            requirements=input_data["requirements"],
            conversation_history=input_data["conversation_history"],
            parsed_documents=input_data["parsed_documents"],
            user_instructions=input_data["user_instructions"],
            short_flow_steps=input_data["short_flow_steps"],
        )

        # Call LLM to generate optimizations
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""

        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """Store optimization suggestions in shared store."""
        shared["user_input"]["processed_documents"] = exec_res
        shared["documentation"] = exec_res
        # Add to conversation history

        return "default"