"""
GTPlanner SSE API 测试文件

用于验证API的基本功能和与CLI层的一致性。
"""

import asyncio
import json
import sys
import os
from typing import List
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agent.api.agent_api import SSEGTPlannerAPI, create_sse_response


class MockSSEResponseWriter:
    """模拟SSE响应写入器，用于测试"""
    
    def __init__(self):
        self.events: List[str] = []
        self.closed = False
    
    async def write(self, data: str) -> None:
        """写入SSE数据"""
        if not self.closed:
            self.events.append(data)
            print(f"[SSE] {data.strip()}")
    
    def close(self):
        """关闭写入器"""
        self.closed = True
    
    def get_events(self) -> List[str]:
        """获取所有事件"""
        return self.events.copy()
    
    def clear(self):
        """清空事件"""
        self.events.clear()
    
    def get_event_count(self) -> int:
        """获取事件数量"""
        return len(self.events)


async def test_basic_api_functionality():
    """测试基本API功能"""
    print("=== 测试基本API功能 ===")
    
    # 创建模拟响应写入器
    writer = MockSSEResponseWriter()
    
    # 创建API实例
    api = SSEGTPlannerAPI(
        include_metadata=True,
        buffer_events=False,
        heartbeat_interval=0,  # 禁用心跳以简化测试
        verbose=True
    )
    
    try:
        # 测试API状态
        status = api.get_api_status()
        print(f"API状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 测试简单请求处理
        result = await api.process_simple_request(
            user_input="Hello, GTPlanner!",
            response_writer=writer.write
        )
        
        print(f"处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"生成的SSE事件数量: {writer.get_event_count()}")
        
        print("✅ 基本API功能测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        raise
    
    finally:
        writer.close()


async def test_configuration_options():
    """测试配置选项"""
    print("\n=== 测试配置选项 ===")
    
    writer = MockSSEResponseWriter()
    api = SSEGTPlannerAPI(verbose=True)
    
    try:
        # 测试配置方法
        api.enable_metadata()
        api.enable_buffering()
        api.set_heartbeat_interval(60.0)
        
        # 检查配置状态
        status = api.get_api_status()
        config = status["current_config"]
        
        assert config["include_metadata"] == True
        assert config["buffer_events"] == True
        assert config["heartbeat_interval"] == 60.0
        
        print("✅ 配置选项测试完成")
        
    finally:
        writer.close()


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    writer = MockSSEResponseWriter()
    api = SSEGTPlannerAPI(verbose=True)
    
    try:
        # 测试空输入
        result = await api.process_simple_request(
            user_input="",
            response_writer=writer.write
        )
        
        print(f"空输入处理结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        print("✅ 错误处理测试完成")
        
    finally:
        writer.close()


async def test_convenience_function():
    """测试便捷函数"""
    print("\n=== 测试便捷函数 ===")
    
    writer = MockSSEResponseWriter()
    
    try:
        # 使用便捷函数
        result = await create_sse_response(
            user_input="测试便捷函数",
            response_writer=writer.write,
            include_metadata=True,
            verbose=True
        )
        
        print(f"便捷函数结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
        print(f"生成的SSE事件数量: {writer.get_event_count()}")
        
        print("✅ 便捷函数测试完成")
        
    finally:
        writer.close()


async def test_streaming_session_management():
    """测试流式会话管理"""
    print("\n=== 测试流式会话管理 ===")
    
    writer = MockSSEResponseWriter()
    api = SSEGTPlannerAPI(verbose=True)
    
    try:
        # 检查初始状态
        status_before = api.get_api_status()
        assert status_before["active_session"] == False
        
        # 处理请求（会创建临时会话）
        result = await api.process_request_stream(
            user_input="测试会话管理",
            response_writer=writer.write,
            session_id="test-session-123"
        )
        
        # 检查处理后状态（应该已清理）
        status_after = api.get_api_status()
        assert status_after["active_session"] == False
        
        print("✅ 流式会话管理测试完成")
        
    finally:
        writer.close()


async def run_all_tests():
    """运行所有测试"""
    print("🚀 开始GTPlanner SSE API测试")
    print("=" * 50)
    
    try:
        await test_basic_api_functionality()
        await test_configuration_options()
        await test_error_handling()
        await test_convenience_function()
        await test_streaming_session_management()
        
        print("\n" + "=" * 50)
        print("✅ 所有API测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


async def demo_api_usage():
    """演示API使用方法"""
    print("\n🎯 API使用演示")
    print("=" * 30)
    
    writer = MockSSEResponseWriter()
    
    # 方式1: 使用API类
    print("方式1: 使用API类")
    api = SSEGTPlannerAPI(
        include_metadata=True,
        buffer_events=False,
        verbose=True
    )
    
    result1 = await api.process_simple_request(
        user_input="设计一个简单的待办事项应用",
        response_writer=writer.write
    )
    
    print(f"结果1: {result1['success']}")
    
    # 方式2: 使用便捷函数
    print("\n方式2: 使用便捷函数")
    writer.clear()
    
    result2 = await create_sse_response(
        user_input="解释什么是微服务架构",
        response_writer=writer.write,
        include_metadata=False,
        verbose=True
    )
    
    print(f"结果2: {result2['success']}")
    
    print("🎯 API使用演示完成")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(run_all_tests())
    
    # 运行演示
    asyncio.run(demo_api_usage())
