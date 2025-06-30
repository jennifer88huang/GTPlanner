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
    model="deepseek-v3",
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
