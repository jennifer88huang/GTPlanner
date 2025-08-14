#!/usr/bin/env python3
"""
测试简化回调调用的可行性
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.stateless_planner import StatelessGTPlanner
from agent.streaming.stream_types import StreamCallbackType
from agent.streaming.stream_interface import StreamingSession


class MockStreamingSession(StreamingSession):
    """模拟流式会话"""
    
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.events = []
    
    async def emit_event(self, event):
        """记录事件"""
        self.events.append(event)
        print(f"📡 事件: {event.event_type}")


async def test_direct_await():
    """测试直接await回调函数"""
    print("🧪 测试直接await回调函数")
    print("=" * 50)

    # 创建模拟会话
    session = MockStreamingSession("test-session")
    
    # 获取StatelessGTPlanner的回调函数
    planner = StatelessGTPlanner()
    callbacks = {
        StreamCallbackType.ON_LLM_START: planner._on_llm_start,
        StreamCallbackType.ON_LLM_CHUNK: planner._on_llm_chunk,
        StreamCallbackType.ON_LLM_END: planner._on_llm_end,
        StreamCallbackType.ON_TOOL_START: planner._on_tool_start,
        StreamCallbackType.ON_TOOL_END: planner._on_tool_end
    }

    try:
        print("🔄 测试LLM开始回调...")
        # 直接await，不进行协程检查
        await callbacks[StreamCallbackType.ON_LLM_START](session)
        print("✅ LLM开始回调成功")

        print("🔄 测试LLM片段回调...")
        await callbacks[StreamCallbackType.ON_LLM_CHUNK](
            session, 
            chunk_content="测试内容", 
            chunk_index=0
        )
        print("✅ LLM片段回调成功")

        print("🔄 测试LLM结束回调...")
        await callbacks[StreamCallbackType.ON_LLM_END](
            session, 
            complete_message="完整消息"
        )
        print("✅ LLM结束回调成功")

        print("🔄 测试工具开始回调...")
        await callbacks[StreamCallbackType.ON_TOOL_START](
            session, 
            tool_name="test_tool", 
            arguments={"param": "value"}
        )
        print("✅ 工具开始回调成功")

        print("🔄 测试工具结束回调...")
        await callbacks[StreamCallbackType.ON_TOOL_END](
            session, 
            tool_name="test_tool", 
            result={"success": True}, 
            execution_time=1.0,
            success=True
        )
        print("✅ 工具结束回调成功")

        print(f"\n📊 总共触发了 {len(session.events)} 个事件")
        
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance_comparison():
    """测试性能对比"""
    print("\n🏃 性能对比测试")
    print("=" * 50)

    session = MockStreamingSession("perf-test")
    planner = StatelessGTPlanner()
    callback = planner._on_llm_start

    # 测试直接await的性能
    import time
    
    print("🔄 测试直接await性能...")
    start_time = time.time()
    for _ in range(1000):
        await callback(session)
    direct_time = time.time() - start_time
    print(f"✅ 直接await: {direct_time:.4f}s (1000次调用)")

    # 测试带协程检查的性能
    print("🔄 测试带协程检查性能...")
    start_time = time.time()
    for _ in range(1000):
        callback_result = callback(session)
        if asyncio.iscoroutine(callback_result):
            await callback_result
    check_time = time.time() - start_time
    print(f"✅ 协程检查: {check_time:.4f}s (1000次调用)")

    performance_gain = ((check_time - direct_time) / check_time) * 100
    print(f"📈 性能提升: {performance_gain:.2f}%")


if __name__ == "__main__":
    async def main():
        success = await test_direct_await()
        if success:
            await test_performance_comparison()
        else:
            print("❌ 基础测试失败，跳过性能测试")
    
    asyncio.run(main())
