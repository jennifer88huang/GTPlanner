#!/usr/bin/env python3
"""
精确模拟CLI的调用方式来调试问题
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.stateless_planner import StatelessGTPlanner
from agent.context_types import AgentContext, ProjectStage, create_user_message
from agent.streaming import StreamingSession, CLIStreamHandler, streaming_manager


async def test_cli_exact():
    """精确模拟CLI的调用方式"""
    print("🧪 精确模拟CLI调用")
    print("=" * 50)

    # 1. 创建StatelessGTPlanner（与CLI相同）
    planner = StatelessGTPlanner()

    # 2. 创建AgentContext（与CLI相同）
    context = AgentContext(
        session_id="cli-test",
        dialogue_history=[create_user_message("我想设计一个简单的任务管理系统")],
        current_stage=ProjectStage.REQUIREMENTS,
        project_state={},
        tool_execution_history=[],
        session_metadata={}
    )

    # 3. 创建流式会话（与CLI相同）
    streaming_session = streaming_manager.create_session("cli-test")
    
    # 4. 创建CLI处理器（与CLI相同）
    cli_handler = CLIStreamHandler(
        show_timestamps=False,
        show_metadata=False
    )
    
    # 5. 添加处理器到会话（与CLI相同）
    streaming_session.add_handler(cli_handler)

    try:
        print("🚀 开始处理请求...")
        
        # 6. 调用StatelessGTPlanner.process（与CLI完全相同）
        result = await planner.process(
            "我想设计一个简单的任务管理系统", 
            context, 
            streaming_session
        )

        print(f"✅ 处理结果: success={result.success}")
        
        if not result.success:
            print(f"❌ 错误: {result.error}")
            
        # 检查元数据中的错误信息
        if hasattr(result, 'metadata') and result.metadata:
            errors = result.metadata.get("errors")
            if errors:
                print(f"❌ 元数据中的错误:")
                for error in errors:
                    print(f"  - {error.get('source')}: {error.get('error')}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理
        await streaming_session.stop()


if __name__ == "__main__":
    asyncio.run(test_cli_exact())
