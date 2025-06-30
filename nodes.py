"""
Node definitions for the GTPlanner application.

This module contains various node implementations for different planning tasks.
"""

# from typing import Dict, Any, List  # Unused imports
from pocketflow import AsyncNode
from utils.multilingual_utils import determine_language, get_localized_prompt
from utils.call_llm import call_llm_async


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
        llm_response = await call_llm_async(prompt, False)

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
        llm_response = await call_llm_async(prompt, False)

        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """Store optimization suggestions in shared store."""
        shared["user_input"]["processed_documents"] = exec_res
        shared["documentation"] = exec_res
        # Add to conversation history

        return "default"