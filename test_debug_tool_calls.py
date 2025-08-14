#!/usr/bin/env python3
"""
测试工具调用调试信息
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.stateless_planner import StatelessGTPlanner
from agent.context_types import AgentContext, ProjectStage, create_user_message


async def test_debug_tool_calls():
    """测试工具调用调试信息"""
    print("🧪 测试工具调用调试信息")
    print("=" * 50)

    # 创建GTPlanner实例
    planner = StatelessGTPlanner()

    # 创建上下文
    context = AgentContext(
        session_id="debug-test",
        dialogue_history=[create_user_message("我想设计一个简单的任务管理系统")],
        current_stage=ProjectStage.REQUIREMENTS,
        project_state={},
        tool_execution_history=[],
        session_metadata={}
    )

    try:
        print("🚀 开始处理请求...")
        result = await planner.process("我想设计一个简单的任务管理系统", context)

        print(f"✅ 处理结果: success={result.success}")
        
        if not result.success:
            print(f"❌ 错误: {result.error}")
            
        # 检查调试信息
        if hasattr(result, 'metadata') and result.metadata:
            debug_info = result.metadata.get("debug_tool_calls")
            if debug_info:
                print(f"🔍 工具调用调试信息:")
                for i, debug in enumerate(debug_info):
                    print(f"  {i+1}. call_id: {debug.get('call_id')}")
                    print(f"     delta_name: {debug.get('delta_name')}")
                    print(f"     delta_args: {debug.get('delta_args')}")
                    print(f"     current_name: {debug.get('current_name')}")
                    print(f"     current_args: {debug.get('current_args')}")
            else:
                print("⚠️ 没有找到工具调用调试信息")
                
            errors = result.metadata.get("errors")
            if errors:
                print(f"❌ 错误信息:")
                for error in errors:
                    print(f"  - {error.get('source')}: {error.get('error')}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_debug_tool_calls())
