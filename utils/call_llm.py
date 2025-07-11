import asyncio
import json
import os
from typing import Any

import aiohttp
from dynaconf import Dynaconf
from json_repair import repair_json
from openai import AsyncOpenAI

# Initialize Dynaconf with environment variable support
settings = Dynaconf(
    settings_files=["settings.toml", "settings.local.toml", ".secrets.toml"],
    environments=True,
    env_switcher="ENV_FOR_DYNACONF",
    load_dotenv=True,  # 自动加载 .env 文件
)


async def _request_llm_async(
    prompt,
    model="doubao-pro-32k",
    # model="qwen2.5-72b-instruct",
    is_json=False,
):
    url = f"{settings.llm.base_url}/chat/completions"
    # print(url)
    payload = json.dumps(
        {
            "messages": [{"role": "user", "content": prompt}],
            "model": model,
            "stream": False,
            "temperature": 0,
            "top_p": 1,
        }
    )
    headers = {
        "Authorization": f"Bearer {settings.llm.api_key}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        timeout = aiohttp.ClientTimeout(total=100000)
        async with session.post(
            url, headers=headers, data=payload, timeout=timeout
        ) as response:
            response_json = await response.json()
            #  print(response)
            response_text = response_json["choices"][0]["message"]["content"]

            if is_json:
                json_data = repair_json(response_text, return_objects=True)
                return json_data
            else:
                return response_text


async def call_llm_async(prompt, is_json=False):
    return await _request_llm_async(prompt, model=settings.llm.model, is_json=is_json)


async def _request_llm_stream_async(
    prompt,
    model="doubao-pro-32k",
):
    """流式LLM请求"""
    url = f"{settings.llm.base_url}/chat/completions"
    payload = json.dumps(
        {
            "messages": [{"role": "user", "content": prompt}],
            "model": model,
            "stream": True,
            "temperature": 0,
            "top_p": 1,
        },
        ensure_ascii=False
    )
    headers = {
        "Authorization": f"Bearer {settings.llm.api_key}",
        "Content-Type": "application/json; charset=utf-8",
    }

    async with aiohttp.ClientSession() as session:
        timeout = aiohttp.ClientTimeout(total=100000)
        async with session.post(
            url, headers=headers, data=payload.encode('utf-8'), timeout=timeout
        ) as response:
            buffer = b""
            async for chunk in response.content.iter_chunked(1024):
                buffer += chunk
                while b'\n' in buffer:
                    line_bytes, buffer = buffer.split(b'\n', 1)
                    try:
                        line_str = line_bytes.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # 移除 "data: " 前缀
                            if data_str == '[DONE]':
                                return
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and len(data['choices']) > 0:
                                    delta = data['choices'][0].get('delta', {})
                                    if 'content' in delta:
                                        content = delta['content']
                                        # 确保换行符被正确传递
                                        yield content
                            except json.JSONDecodeError:
                                continue
                    except UnicodeDecodeError:
                        continue


async def call_llm_stream_async(prompt):
    """流式调用LLM"""
    async for chunk in _request_llm_stream_async(prompt, model=settings.llm.model):
        yield chunk


# Synchronous version for backward compatibility
def call_llm(prompt, conversation_history=None, is_json=False):
    """Synchronous wrapper for call_llm_async"""
    return asyncio.run(call_llm_async(prompt, conversation_history, is_json))


# Example usage
if __name__ == "__main__":

    async def test():
        response = await call_llm_async("What is the purpose of async programming?")
        print(response)

    asyncio.run(test())
