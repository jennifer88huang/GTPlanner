"""
LLM调用工具

提供简化的LLM调用接口，直接使用OpenAI客户端。
"""

import json
import re
from typing import AsyncIterator, Dict, List, Any, Optional
from utils.openai_client import get_openai_client


def _clean_json_response(content: str) -> str:
    """
    清理和修复JSON响应

    Args:
        content: 原始响应内容

    Returns:
        清理后的JSON字符串

    Raises:
        ValueError: 如果无法修复为有效JSON
    """
    try:
        # 验证是否为有效JSON
        json.loads(content)
        return content
    except json.JSONDecodeError as e:
        # 尝试清理代码块包裹的JSON
        try:
            # 移除markdown代码块
            cleaned_content = re.sub(r'^```json\s*', '', content.strip())
            cleaned_content = re.sub(r'\s*```$', '', cleaned_content)

            # 尝试解析清理后的内容
            json.loads(cleaned_content)
            return cleaned_content
        except json.JSONDecodeError:
            # 尝试修复常见的JSON问题
            try:
                # 尝试添加缺失的结束括号
                if cleaned_content.count('{') > cleaned_content.count('}'):
                    cleaned_content += '}' * (cleaned_content.count('{') - cleaned_content.count('}'))
                if cleaned_content.count('[') > cleaned_content.count(']'):
                    cleaned_content += ']' * (cleaned_content.count('[') - cleaned_content.count(']'))

                # 再次尝试解析
                json.loads(cleaned_content)
                return cleaned_content
            except json.JSONDecodeError:
                # 如果仍然无法解析，返回错误信息
                raise ValueError(f"LLM返回的不是有效JSON: {str(e)}, 内容: {content[:500]}...")


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
            return _clean_json_response(content)
        
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





# 导出主要函数
__all__ = [
    "call_llm_async",
    "call_llm_stream_async",
    "call_llm_with_messages",
    "call_llm_with_function_calling",
    "ask_llm"
]
