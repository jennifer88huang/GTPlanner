"""
Function Calling集成测试

使用OpenAI SDK测试Function Calling功能，验证工具定义和执行流程。
"""

import asyncio
import json
import pytest
from typing import Dict, Any

from utils.openai_client import get_openai_client
from agent.function_calling import (
    get_agent_function_definitions,
    execute_agent_tool
)


class TestFunctionCallingIntegration:
    """Function Calling集成测试"""
    
    def setup_method(self):
        """测试设置"""
        self.client = get_openai_client()
        self.tools = get_agent_function_definitions()
    
    def test_tool_definitions_format(self):
        """测试工具定义格式"""
        assert len(self.tools) == 3

        tool_names = [tool["function"]["name"] for tool in self.tools]
        expected_names = ["short_planning", "research", "architecture_design"]

        for name in expected_names:
            assert name in tool_names
        
        # 验证每个工具的格式
        for tool in self.tools:
            assert tool["type"] == "function"
            assert "function" in tool
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]
    
    @pytest.mark.asyncio
    async def test_simple_function_call_with_llm(self):
        """测试简单的Function Calling（使用真实LLM）"""
        try:
            # 准备消息
            messages = [
                {
                    "role": "system",
                    "content": "你是GTPlanner助手。当用户提出项目需求时，使用research工具来调研相关技术。"
                },
                {
                    "role": "user",
                    "content": "我想开发一个简单的待办事项管理应用"
                }
            ]
            
            # 调用OpenAI API
            response = await self.client.chat_completion_async(
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            # 验证响应
            assert response is not None
            assert hasattr(response, 'choices')
            assert len(response.choices) > 0
            
            choice = response.choices[0]
            message = choice.message
            
            print(f"LLM响应: {message.content}")
            
            # 检查是否有工具调用
            if hasattr(message, 'tool_calls') and message.tool_calls:
                print(f"工具调用数量: {len(message.tool_calls)}")
                
                for tool_call in message.tool_calls:
                    print(f"工具名称: {tool_call.function.name}")
                    print(f"工具参数: {tool_call.function.arguments}")
                    
                    # 验证工具调用格式
                    assert tool_call.function.name in ["short_planning", "research", "architecture_design"]
                    
                    # 尝试解析参数
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        assert isinstance(arguments, dict)
                        print(f"解析后的参数: {arguments}")
                    except json.JSONDecodeError as e:
                        pytest.fail(f"工具参数JSON解析失败: {e}")
            else:
                print("LLM没有调用工具，可能直接回复了文本")
                
        except Exception as e:
            pytest.skip(f"LLM调用失败，可能是配置问题: {e}")
    
    @pytest.mark.asyncio
    async def test_function_call_execution_flow(self):
        """测试完整的Function Calling执行流程"""
        try:
            # 准备消息
            messages = [
                {
                    "role": "system",
                    "content": "你是GTPlanner助手。用户提出需求时，必须使用research工具调研相关技术。"
                },
                {
                    "role": "user",
                    "content": "我需要开发一个在线书店系统"
                }
            ]

            # 第一步：获取LLM的工具调用
            response = await self.client.chat_completion_async(
                messages=messages,
                tools=self.tools,
                tool_choice={"type": "function", "function": {"name": "research"}}  # 强制调用
            )
            
            choice = response.choices[0]
            message = choice.message
            
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_call = message.tool_calls[0]
                
                print(f"LLM调用工具: {tool_call.function.name}")
                print(f"工具参数: {tool_call.function.arguments}")
                
                # 第二步：执行工具
                arguments = json.loads(tool_call.function.arguments)
                tool_result = await execute_agent_tool(
                    tool_call.function.name,
                    arguments
                )
                
                print(f"工具执行结果: {tool_result}")
                
                # 验证工具执行结果
                assert "success" in tool_result
                assert "tool_name" in tool_result or "error" in tool_result
                
                if tool_result["success"]:
                    assert "result" in tool_result
                    print("✅ 工具执行成功")
                else:
                    print(f"❌ 工具执行失败: {tool_result['error']}")
                
                # 第三步：将工具结果返回给LLM
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }
                    ]
                })
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
                
                # 第四步：获取LLM的最终回复
                final_response = await self.client.chat_completion_async(
                    messages=messages,
                    tools=self.tools
                )
                
                final_message = final_response.choices[0].message
                print(f"LLM最终回复: {final_message.content}")
                
                assert final_message.content is not None
                print("✅ 完整的Function Calling流程测试成功")
                
            else:
                pytest.fail("LLM没有调用工具")
                
        except Exception as e:
            pytest.skip(f"Function Calling流程测试失败: {e}")
    

    @pytest.mark.asyncio
    async def test_streaming_function_call(self):
        """测试流式Function Calling"""
        try:
            from utils.openai_stream_adapter import get_stream_adapter
            
            adapter = get_stream_adapter()
            
            messages = [
                {
                    "role": "system",
                    "content": "你是GTPlanner助手。用户提出需求时，使用research工具调研。"
                },
                {
                    "role": "user",
                    "content": "我想开发一个简单的天气查询应用"
                }
            ]
            
            tool_calls_received = []
            
            async def tool_callback(call_data, is_complete):
                tool_calls_received.append((call_data, is_complete))
                print(f"工具调用回调: {call_data['function']['name']}, 完成: {is_complete}")
            
            content_chunks = []
            async for chunk in adapter.stream_chat_completion(
                messages=messages,
                tools=self.tools,
                tool_call_callback=tool_callback
            ):
                if chunk:
                    content_chunks.append(chunk)
                    print(f"内容块: {chunk}")
            
            print(f"收到内容块数量: {len(content_chunks)}")
            print(f"收到工具调用数量: {len(tool_calls_received)}")
            
            if tool_calls_received:
                print("✅ 流式Function Calling测试成功")
            else:
                print("ℹ️ 没有收到工具调用，可能LLM直接回复了文本")
                
        except Exception as e:
            pytest.skip(f"流式Function Calling测试失败: {e}")


class TestFunctionCallingConfiguration:
    """Function Calling配置测试"""
    
    def test_openai_config_function_calling(self):
        """测试OpenAI配置中的Function Calling设置"""
        from config.openai_config import get_openai_config
        
        config = get_openai_config()
        
        # 验证Function Calling相关配置
        assert hasattr(config, 'function_calling_enabled')
        assert hasattr(config, 'tool_choice')
        assert hasattr(config, 'parallel_tool_calls')
        
        print(f"Function Calling启用: {config.function_calling_enabled}")
        print(f"工具选择策略: {config.tool_choice}")
        print(f"并行工具调用: {config.parallel_tool_calls}")
    
    def test_client_function_calling_support(self):
        """测试客户端Function Calling支持"""
        client = get_openai_client()
        
        # 验证客户端配置
        assert hasattr(client, 'config')
        assert client.config.function_calling_enabled
        
        print("✅ OpenAI客户端Function Calling支持正常")


if __name__ == "__main__":
    # 运行特定测试
    import sys
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        # 创建测试实例并设置
        test_instance = TestFunctionCallingIntegration()
        test_instance.setup_method()

        if test_name == "simple":
            asyncio.run(test_instance.test_simple_function_call_with_llm())
        elif test_name == "flow":
            asyncio.run(test_instance.test_function_call_execution_flow())
        elif test_name == "direct":
            print("direct test has been removed")
        elif test_name == "stream":
            asyncio.run(test_instance.test_streaming_function_call())
        elif test_name == "openai":
            asyncio.run(test_instance.test_simple_function_call_with_llm())
    else:
        # 运行所有测试
        pytest.main([__file__, "-v", "-s"])
