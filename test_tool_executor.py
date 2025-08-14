#!/usr/bin/env python3
"""
测试工具执行器的直接调用
"""

import asyncio
import sys
import os
from types import SimpleNamespace

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.flows.react_orchestrator_refactored.tool_executor import ToolExecutor


async def test_tool_executor():
    """测试工具执行器"""
    print("🧪 测试工具执行器")
    print("=" * 50)

    # 创建工具执行器
    executor = ToolExecutor()

    # 创建模拟的工具调用
    tool_call = SimpleNamespace()
    tool_call.id = "test_call_1"
    tool_call.function = SimpleNamespace()
    tool_call.function.name = "short_planning"
    tool_call.function.arguments = '{"user_requirements": "设计一个简单的计算器"}'

    # 创建shared字典
    shared = {}

    try:
        print(f"🔧 测试工具调用: {tool_call.function.name}")
        print(f"📋 参数: {tool_call.function.arguments}")

        # 执行工具调用
        results = await executor.execute_tools_parallel([tool_call], shared, None)

        print(f"✅ 执行结果: {results}")
        
        if shared.get("errors"):
            print(f"❌ 错误信息: {shared['errors']}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_tool_executor())
