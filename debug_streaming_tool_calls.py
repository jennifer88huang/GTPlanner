#!/usr/bin/env python3
"""
调试流式工具调用的完整流程
"""

import asyncio
import sys
import os
from types import SimpleNamespace

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.flows.react_orchestrator_refactored.react_orchestrator_node import ReActOrchestratorNode
from agent.streaming.stream_interface import StreamingSession
from agent.streaming.stream_types import StreamCallbackType


class DebugStreamingSession(StreamingSession):
    """调试用的流式会话"""
    
    def __init__(self, session_id: str):
        super().__init__(session_id)
        self.events = []
    
    async def emit_event(self, event):
        """记录所有事件"""
        self.events.append(event)
        print(f"📡 流式事件: {event.event_type} - {getattr(event, 'data', {})}")
    
    async def start(self):
        """启动会话"""
        print(f"🚀 启动流式会话: {self.session_id}")
    
    async def close(self):
        """关闭会话"""
        print(f"🔚 关闭流式会话: {self.session_id}")


async def test_streaming_tool_calls():
    """测试流式工具调用"""
    print("🧪 测试流式工具调用")
    print("=" * 50)

    # 创建ReAct节点
    react_node = ReActOrchestratorNode()

    # 创建调试流式会话
    streaming_session = DebugStreamingSession("debug-session")
    await streaming_session.start()

    # 创建async回调函数
    async def async_llm_start(session, **kwargs):
        print("🤖 LLM开始")

    async def async_llm_chunk(session, chunk_content, **kwargs):
        print(f"📝 LLM片段: {chunk_content}")

    async def async_llm_end(session, **kwargs):
        print("✅ LLM结束")

    async def async_tool_start(session, tool_name, arguments, **kwargs):
        print(f"🔧 工具开始: {tool_name}")

    async def async_tool_end(session, **kwargs):
        print("🔧 工具结束")

    # 创建shared字典
    shared = {
        "streaming_session": streaming_session,
        "streaming_callbacks": {
            StreamCallbackType.ON_LLM_START: async_llm_start,
            StreamCallbackType.ON_LLM_CHUNK: async_llm_chunk,
            StreamCallbackType.ON_LLM_END: async_llm_end,
            StreamCallbackType.ON_TOOL_START: async_tool_start,
            StreamCallbackType.ON_TOOL_END: async_tool_end,
        }
    }

    # 创建消息
    messages = [
        {"role": "user", "content": "我想设计一个简单的任务管理系统"}
    ]

    try:
        print("🚀 开始执行ReAct节点...")
        
        # 准备阶段
        prep_result = await react_node.prep_async(shared)
        print(f"📋 准备结果: {prep_result}")

        # 执行阶段
        exec_result = await react_node.exec_async(prep_result)
        print(f"⚙️ 执行结果: {exec_result}")

        # 后处理阶段
        post_result = await react_node.post_async(shared, prep_result, exec_result)
        print(f"📊 后处理结果: {post_result}")

        # 检查shared中的错误信息
        if shared.get("errors"):
            print(f"❌ 错误信息:")
            for error in shared["errors"]:
                print(f"  - {error.get('source')}: {error.get('error')}")

        # 检查调试信息
        if shared.get("debug_tool_calls"):
            print(f"🔍 工具调用调试信息:")
            for debug in shared["debug_tool_calls"]:
                print(f"  - call_id: {debug.get('call_id')}")
                print(f"    delta_name: {debug.get('delta_name')}")
                print(f"    delta_args: {debug.get('delta_args')}")
                print(f"    current_name: {debug.get('current_name')}")
                print(f"    current_args: {debug.get('current_args')}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await streaming_session.close()


if __name__ == "__main__":
    asyncio.run(test_streaming_tool_calls())
