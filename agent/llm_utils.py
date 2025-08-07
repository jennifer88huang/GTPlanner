"""
LLM调用工具

提供简化的LLM调用接口，直接使用OpenAI客户端。
"""

import json
from typing import AsyncIterator, Dict, List, Any, Optional
from utils.openai_client import get_openai_client


async def call_llm_async(
    prompt: str,
    is_json: bool = False,
    system_prompt: Optional[str] = None,
    **kwargs
) -> str:
    """
    异步LLM调用

    Args:
        prompt: 用户提示词
        is_json: 是否需要JSON格式响应
        system_prompt: 系统提示词
        **kwargs: 其他OpenAI参数

    Returns:
        LLM响应文本
    """
    client = get_openai_client()

    # 构建消息
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 处理JSON格式要求
    if is_json:
        if system_prompt:
            messages[0]["content"] += "\n\n请确保回复是有效的JSON格式。"
        else:
            messages.append({
                "role": "system", 
                "content": "请以JSON格式回复，确保输出是有效的JSON。"
            })
        kwargs["response_format"] = {"type": "json_object"}
    
    messages.append({"role": "user", "content": prompt})

    # 执行调用
    response = await client.chat_completion_async(messages, **kwargs)

    # 提取内容
    if response.choices and response.choices[0].message.content:
        content = response.choices[0].message.content
        
        # 如果需要JSON格式，尝试解析验证
        if is_json:
            try:
                # 验证是否为有效JSON
                json.loads(content)
                return content
            except json.JSONDecodeError as e:
                # 尝试修复常见的JSON问题
                try:
                    # 尝试添加缺失的结束括号
                    if content.count('{') > content.count('}'):
                        content += '}' * (content.count('{') - content.count('}'))
                    if content.count('[') > content.count(']'):
                        content += ']' * (content.count('[') - content.count(']'))

                    # 再次尝试解析
                    json.loads(content)
                    return content
                except json.JSONDecodeError:
                    # 如果仍然无法解析，返回错误信息
                    raise ValueError(f"LLM返回的不是有效JSON: {str(e)}, 内容: {content[:500]}...")
        
        return content

    return ""


async def call_llm_stream_async(
    prompt: str,
    is_json: bool = False,
    system_prompt: Optional[str] = None,
    **kwargs
) -> AsyncIterator[str]:
    """
    异步流式LLM调用

    Args:
        prompt: 用户提示词
        is_json: 是否需要JSON格式响应
        system_prompt: 系统提示词
        **kwargs: 其他OpenAI参数

    Yields:
        LLM响应文本块
    """
    client = get_openai_client()

    # 构建消息
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    # 处理JSON格式要求
    if is_json:
        if system_prompt:
            messages[0]["content"] += "\n\n请确保回复是有效的JSON格式。"
        else:
            messages.append({
                "role": "system", 
                "content": "请以JSON格式回复，确保输出是有效的JSON。"
            })
        kwargs["response_format"] = {"type": "json_object"}
    
    messages.append({"role": "user", "content": prompt})

    # 执行流式调用
    async for chunk in client.chat_completion_stream_async(messages, **kwargs):
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


async def call_llm_with_messages(
    messages: List[Dict[str, str]],
    **kwargs
) -> str:
    """
    使用消息列表调用LLM

    Args:
        messages: 消息列表，格式为 [{"role": "user/system/assistant", "content": "..."}]
        **kwargs: 其他OpenAI参数

    Returns:
        LLM响应文本
    """
    client = get_openai_client()
    
    response = await client.chat_completion_async(messages, **kwargs)
    
    if response.choices and response.choices[0].message.content:
        return response.choices[0].message.content
    
    return ""


async def call_llm_with_function_calling(
    messages: List[Dict[str, str]],
    tools: List[Dict[str, Any]],
    tool_choice: str = "auto",
    **kwargs
) -> Any:
    """
    使用Function Calling调用LLM

    Args:
        messages: 消息列表
        tools: 工具定义列表
        tool_choice: 工具选择策略
        **kwargs: 其他OpenAI参数

    Returns:
        OpenAI响应对象
    """
    client = get_openai_client()
    
    return await client.chat_completion_async(
        messages=messages,
        tools=tools,
        tool_choice=tool_choice,
        **kwargs
    )


# 便捷函数
async def ask_llm(question: str, context: Optional[str] = None) -> str:
    """
    简单的问答调用

    Args:
        question: 问题
        context: 上下文信息

    Returns:
        回答
    """
    if context:
        prompt = f"上下文信息：\n{context}\n\n问题：{question}"
    else:
        prompt = question
    
    return await call_llm_async(prompt)


async def generate_json(prompt: str, schema_description: Optional[str] = None) -> Dict[str, Any]:
    """
    生成JSON格式的回复

    Args:
        prompt: 提示词
        schema_description: JSON结构描述

    Returns:
        解析后的JSON对象
    """
    if schema_description:
        full_prompt = f"{prompt}\n\n请按照以下JSON结构回复：\n{schema_description}"
    else:
        full_prompt = prompt
    
    response = await call_llm_async(full_prompt, is_json=True)
    
    try:
        return json.loads(response)
    except json.JSONDecodeError as e:
        raise ValueError(f"无法解析LLM返回的JSON: {e}")


async def analyze_requirements(user_input: str) -> Dict[str, Any]:
    """
    分析用户需求的便捷函数

    Args:
        user_input: 用户输入

    Returns:
        结构化的需求分析结果
    """
    system_prompt = """你是一个专业的需求分析师。请分析用户的需求并返回结构化的JSON格式结果。

JSON格式应包含：
- project_overview: 项目概述
- functional_requirements: 功能需求列表
- non_functional_requirements: 非功能需求
- target_users: 目标用户
- constraints: 约束条件"""

    return await generate_json(
        f"请分析以下用户需求：\n{user_input}",
        schema_description="按照上述格式返回JSON"
    )


# 导出主要函数
__all__ = [
    "call_llm_async",
    "call_llm_stream_async", 
    "call_llm_with_messages",
    "call_llm_with_function_calling",
    "ask_llm",
    "generate_json",
    "analyze_requirements"
]
