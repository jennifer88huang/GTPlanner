#!/usr/bin/env python3
"""
Function Calling测试运行器

快速测试Function Calling功能的脚本。
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from agent.function_calling import (
    get_agent_function_definitions,
    execute_agent_tool,
    call_requirements_analysis
)
from utils.openai_client import get_openai_client


async def test_tool_definitions():
    """测试工具定义"""
    print("🔧 测试工具定义...")
    
    tools = get_agent_function_definitions()
    print(f"发现 {len(tools)} 个工具:")
    
    for tool in tools:
        name = tool["function"]["name"]
        desc = tool["function"]["description"]
        params = list(tool["function"]["parameters"]["properties"].keys())
        print(f"  - {name}: {desc}")
        print(f"    参数: {params}")
    
    print("✅ 工具定义测试完成\n")


async def test_simple_llm_call():
    """测试简单的LLM Function Calling"""
    print("🤖 测试LLM Function Calling...")
    
    try:
        client = get_openai_client()
        tools = get_agent_function_definitions()
        
        messages = [
            {
                "role": "system",
                "content": "你是GTPlanner助手。当用户提出项目需求时，使用requirements_analysis工具来分析需求。"
            },
            {
                "role": "user",
                "content": "我想开发一个简单的待办事项应用"
            }
        ]
        
        print("发送请求到OpenAI...")
        response = await client.chat_completion_async(
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
        
        choice = response.choices[0]
        message = choice.message
        
        print(f"LLM回复: {message.content}")
        
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"🔧 LLM调用了 {len(message.tool_calls)} 个工具:")
            
            for i, tool_call in enumerate(message.tool_calls, 1):
                print(f"  {i}. 工具: {tool_call.function.name}")
                print(f"     参数: {tool_call.function.arguments}")
                
                # 尝试执行工具
                try:
                    import json
                    arguments = json.loads(tool_call.function.arguments)
                    
                    print(f"     执行工具...")
                    result = await execute_agent_tool(
                        tool_call.function.name,
                        arguments
                    )
                    
                    if result["success"]:
                        print(f"     ✅ 工具执行成功")
                        print(f"     结果类型: {type(result['result'])}")
                    else:
                        print(f"     ❌ 工具执行失败: {result['error']}")
                        
                except Exception as e:
                    print(f"     ❌ 工具执行异常: {e}")
        else:
            print("ℹ️ LLM没有调用工具，直接回复了文本")
        
        print("✅ LLM Function Calling测试完成\n")
        
    except Exception as e:
        print(f"❌ LLM测试失败: {e}\n")


async def test_direct_tool_call():
    """测试直接工具调用"""
    print("🛠️ 测试直接工具调用...")
    
    try:
        result = await call_requirements_analysis(
            "我想开发一个在线图书管理系统，包括图书借阅、归还、搜索等功能"
        )
        
        print(f"工具调用结果:")
        print(f"  成功: {result['success']}")
        
        if result["success"]:
            print(f"  工具名: {result['tool_name']}")
            print(f"  结果类型: {type(result['result'])}")
            
            # 如果结果是字典，显示一些关键信息
            if isinstance(result['result'], dict):
                keys = list(result['result'].keys())[:5]  # 只显示前5个键
                print(f"  结果键: {keys}")
        else:
            print(f"  错误: {result['error']}")
        
        print("✅ 直接工具调用测试完成\n")
        
    except Exception as e:
        print(f"❌ 直接工具调用测试失败: {e}\n")


async def test_config():
    """测试配置"""
    print("⚙️ 测试配置...")
    
    try:
        from config.openai_config import get_openai_config
        
        config = get_openai_config()
        print(f"OpenAI配置:")
        print(f"  模型: {config.model}")
        print(f"  Function Calling启用: {config.function_calling_enabled}")
        print(f"  工具选择: {config.tool_choice}")
        print(f"  并行工具调用: {config.parallel_tool_calls}")
        print(f"  最大重试: {config.max_retries}")
        print(f"  超时: {config.timeout}")
        
        print("✅ 配置测试完成\n")
        
    except Exception as e:
        print(f"❌ 配置测试失败: {e}\n")


async def main():
    """主测试函数"""
    print("🚀 GTPlanner Function Calling 测试\n")
    
    # 运行所有测试
    await test_config()
    await test_tool_definitions()
    await test_simple_llm_call()
    await test_direct_tool_call()
    
    print("🎉 所有测试完成!")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        
        if test_type == "config":
            asyncio.run(test_config())
        elif test_type == "tools":
            asyncio.run(test_tool_definitions())
        elif test_type == "llm":
            asyncio.run(test_simple_llm_call())
        elif test_type == "direct":
            asyncio.run(test_direct_tool_call())
        else:
            print("可用的测试类型: config, tools, llm, direct")
    else:
        # 运行所有测试
        asyncio.run(main())
