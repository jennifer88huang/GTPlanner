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
    model,
    is_json=False,
):
    import time

    # 调试信息：请求开始
    print(f"🤖 LLM调用开始")
    print(f"   📡 URL: {settings.llm.base_url}/chat/completions")
    print(f"   🎯 模型: {model}")
    print(f"   📏 提示词长度: {len(prompt)} 字符")
    print(f"   📋 JSON模式: {'是' if is_json else '否'}")

    url = f"{settings.llm.base_url}/chat/completions"
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

    request_start_time = time.time()
    print(f"   🚀 发送HTTP请求...")

    try:
        async with aiohttp.ClientSession() as session:
            # 设置更长的超时时间，适应复杂提示词
            timeout = aiohttp.ClientTimeout(total=120, connect=15, sock_read=90)
            print(f"   ⏰ 超时设置: 总计60秒, 连接10秒, 读取30秒")

            async with session.post(
                url, headers=headers, data=payload, timeout=timeout
            ) as response:
                print(f"   📨 收到HTTP响应: {response.status}")

                if response.status != 200:
                    error_text = await response.text()
                    print(f"   ❌ HTTP错误: {response.status}")
                    print(f"   📄 错误内容: {error_text}")
                    raise Exception(f"HTTP {response.status}: {error_text}")

                response_json = await response.json()
                request_duration = time.time() - request_start_time
                print(f"   ✅ HTTP请求完成 (耗时: {request_duration:.2f}秒)")

                # 检查响应结构
                if "choices" not in response_json:
                    print(f"   ❌ 响应格式错误: 缺少choices字段")
                    print(f"   📄 响应内容: {response_json}")
                    raise Exception("LLM响应格式错误")

                if not response_json["choices"]:
                    print(f"   ❌ 响应格式错误: choices为空")
                    raise Exception("LLM响应choices为空")

                response_text = response_json["choices"][0]["message"]["content"]
                print(f"   📊 LLM返回内容长度: {len(response_text)} 字符")

                if is_json:
                    print(f"   🔧 解析JSON响应...")
                    print(f"   📄 响应内容预览: {response_text[:200]}...")

                    # 先尝试直接解析JSON
                    try:
                        json_start_time = time.time()
                        json_data = json.loads(response_text)
                        json_duration = time.time() - json_start_time
                        print(f"   ✅ 直接JSON解析成功 (耗时: {json_duration:.2f}秒)")
                        return json_data
                    except json.JSONDecodeError as e:
                        print(f"   ⚠️ 直接JSON解析失败: {e}")
                        print(f"   🔧 尝试使用repair_json修复...")

                        repair_start_time = time.time()
                        json_data = repair_json(response_text, return_objects=True)
                        repair_duration = time.time() - repair_start_time
                        print(f"   ✅ JSON修复解析成功 (耗时: {repair_duration:.2f}秒)")
                        return json_data
                else:
                    print(f"   ✅ 文本响应返回")
                    return response_text

    except Exception as e:
        request_duration = time.time() - request_start_time
        print(f"   ❌ LLM调用失败 (耗时: {request_duration:.2f}秒)")
        print(f"   📄 错误信息: {str(e)}")
        raise e


async def call_llm_async(prompt, is_json=False, max_retries=3, retry_delay=2):
    import time
    import asyncio

    print(f"🎯 开始LLM调用 (最大重试: {max_retries}次)")
    print(f"   🔧 配置模型: {settings.llm.model}")
    print(f"   🌐 API地址: {settings.llm.base_url}")

    start_time = time.time()
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            if attempt > 0:
                print(f"🔄 第{attempt}次重试...")
                await asyncio.sleep(retry_delay * attempt)  # 递增延迟

            result = await _request_llm_async(prompt, model=settings.llm.model, is_json=is_json)
            total_time = time.time() - start_time

            if attempt > 0:
                print(f"🎉 LLM调用重试成功 (第{attempt}次重试, 总耗时: {total_time:.2f}秒)")
            else:
                print(f"🎉 LLM调用成功 (总耗时: {total_time:.2f}秒)")

            return result

        except Exception as e:
            last_error = e
            current_time = time.time() - start_time

            # 判断是否应该重试
            should_retry = attempt < max_retries and _should_retry_error(e)

            if should_retry:
                print(f"⚠️ 第{attempt + 1}次尝试失败 (耗时: {current_time:.2f}秒): {str(e)}")
                print(f"   🔄 将在{retry_delay * (attempt + 1)}秒后重试...")
            else:
                total_time = time.time() - start_time
                print(f"💥 LLM调用最终失败 (总耗时: {total_time:.2f}秒)")
                print(f"   📄 失败原因: {str(e)}")
                if attempt >= max_retries:
                    print(f"   🚫 已达到最大重试次数({max_retries})")
                else:
                    print(f"   🚫 错误类型不适合重试")
                break

    raise last_error


def _should_retry_error(error):
    """判断错误是否应该重试"""
    error_str = str(error).lower()

    # 网络相关错误应该重试
    retry_keywords = [
        'timeout',
        'server disconnected',
        'connection',
        'network',
        'socket',
        'read timeout',
        'connect timeout'
    ]

    # JSON解析错误通常不应该重试（除非是网络导致的不完整响应）
    no_retry_keywords = [
        'json decode',
        'invalid json',
        'expecting',
        'unterminated'
    ]

    # 检查是否包含不重试的关键词
    for keyword in no_retry_keywords:
        if keyword in error_str:
            return False

    # 检查是否包含重试的关键词
    for keyword in retry_keywords:
        if keyword in error_str:
            return True

    # 默认不重试未知错误
    return False


async def _request_llm_stream_async(
    prompt,
    model,
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
