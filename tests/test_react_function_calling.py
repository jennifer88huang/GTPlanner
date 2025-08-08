"""
测试重构后的ReAct主控制器Function Calling功能

验证新的基于Function Calling的ReAct主控制器是否能正常工作。
"""

import pytest
import asyncio
from agent.flows.react_orchestrator_node import ReActOrchestratorNode


class TestReActFunctionCalling:
    """ReAct Function Calling功能测试"""

    @pytest.fixture
    def react_node(self):
        """创建ReAct主控制器节点 - 使用真实组件"""
        return ReActOrchestratorNode()

    @pytest.fixture
    def mock_shared_data(self):
        """模拟共享数据"""
        return {
            "dialogue_history": {
                "messages": [
                    {"role": "user", "content": "我想开发一个电商网站"}
                ]
            },
            "react_cycle_count": 0
        }

    @pytest.mark.asyncio
    async def test_prep_async(self, react_node, mock_shared_data):
        """测试准备阶段"""
        result = await react_node.prep_async(mock_shared_data)
        
        assert result["success"] is True
        assert "user_message" in result
        assert "state_info" in result
        assert result["user_message"] == "我想开发一个电商网站"

    @pytest.mark.asyncio
    async def test_build_conversation_messages(self, react_node):
        """测试对话消息构建"""
        user_message = "我想开发一个电商网站"
        state_info = "当前状态：初始化"
        shared_data = {
            "dialogue_history": {
                "messages": [
                    {"role": "user", "content": "你好"},
                    {"role": "assistant", "content": "您好！我是GTPlanner助手"}
                ]
            }
        }
        
        messages = react_node._build_conversation_messages(user_message, state_info, shared_data)
        
        # 检查消息结构
        assert len(messages) >= 3  # 系统消息 + 历史消息 + 当前消息
        assert messages[0]["role"] == "system"
        assert "GTPlanner" in messages[0]["content"]
        assert messages[-1]["role"] == "user"
        assert user_message in messages[-1]["content"]

    @pytest.mark.asyncio
    async def test_function_calling_system_prompt(self, react_node):
        """测试Function Calling系统提示词"""
        prompt = react_node._build_function_calling_system_prompt()
        
        # 检查关键内容
        assert "GTPlanner" in prompt
        assert "Function Calling" in prompt
        assert "requirements_analysis" in prompt
        assert "short_planning" in prompt
        assert "research" in prompt
        assert "architecture_design" in prompt

    # 移除了mock测试，使用真实LLM测试替代

    @pytest.mark.asyncio
    async def test_update_shared_state_with_tool_result(self, react_node):
        """测试工具结果更新共享状态"""
        shared = {}
        
        # 测试需求分析结果
        tool_result = {
            "success": True,
            "result": {"project_overview": {"title": "测试项目"}}
        }
        
        react_node._update_shared_state_with_tool_result(shared, "requirements_analysis", tool_result)
        assert "structured_requirements" in shared
        assert shared["structured_requirements"]["project_overview"]["title"] == "测试项目"
        
        # 测试短期规划结果
        tool_result = {
            "success": True,
            "result": {"phases": ["阶段1", "阶段2"]}
        }
        
        react_node._update_shared_state_with_tool_result(shared, "short_planning", tool_result)
        assert "confirmation_document" in shared
        assert shared["confirmation_document"]["phases"] == ["阶段1", "阶段2"]

    @pytest.mark.asyncio
    async def test_post_async_with_tool_calls(self, react_node):
        """测试带工具调用的post处理"""
        shared = {"react_cycle_count": 0}
        prep_res = {}
        exec_res = {
            "user_message": "我已经完成了需求分析。",
            "tool_calls": [
                {
                    "tool_name": "requirements_analysis",
                    "result": {
                        "success": True,
                        "result": {"project_overview": {"title": "电商项目"}}
                    }
                }
            ],
            "next_action": "continue_conversation",
            "decision_success": True
        }

        result = await react_node.post_async(shared, prep_res, exec_res)

        # 验证结果
        assert result == "wait_for_user"
        assert shared["react_cycle_count"] == 1
        assert "dialogue_history" in shared
        assert len(shared["dialogue_history"]["messages"]) == 1
        assert shared["dialogue_history"]["messages"][0]["role"] == "assistant"
        assert "structured_requirements" in shared

    @pytest.mark.asyncio
    async def test_error_handling(self, react_node):
        """测试错误处理"""
        # 测试prep阶段错误
        shared_with_error = {}  # 缺少必要数据

        result = await react_node.prep_async(shared_with_error)
        assert result["success"] is True  # prep应该能处理空数据

        # 测试exec阶段错误
        prep_result = {"error": "测试错误"}
        exec_result = await react_node.exec_async(prep_result)
        assert "error" in exec_result
        assert exec_result["decision_success"] is False

    @pytest.mark.asyncio
    async def test_mixed_mode_real_llm_call(self, react_node):
        """测试混合模式：使用真实LLM调用"""
        # 构建测试消息
        messages = [
            {"role": "system", "content": react_node._build_function_calling_system_prompt()},
            {"role": "user", "content": "我想开发一个简单的待办事项管理应用，请帮我分析需求并进行技术调研"}
        ]

        print("🚀 开始真实LLM调用测试...")

        # 执行真实的Function Calling
        result = await react_node._execute_with_function_calling(messages, {})

        # 输出结果
        print(f"✅ LLM调用完成")
        print(f"📝 用户消息: {result.get('user_message', '')}")
        print(f"🔧 工具调用数量: {len(result.get('tool_calls', []))}")
        print(f"🎯 执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"💭 推理过程: {result.get('reasoning', '')}")

        # 详细输出工具调用结果
        for i, tool_call in enumerate(result.get('tool_calls', [])):
            print(f"🛠️ 工具调用 {i+1}:")
            print(f"   名称: {tool_call.get('tool_name', 'unknown')}")
            print(f"   成功: {tool_call.get('success', False)}")
            if tool_call.get('result', {}).get('success'):
                print(f"   结果: 执行成功")
            else:
                print(f"   错误: {tool_call.get('result', {}).get('error', 'unknown')}")

        # 基本验证
        assert result["decision_success"] is True, "LLM调用应该成功"
        assert "user_message" in result, "应该有用户消息"

        # 如果有工具调用，验证其结构
        if result.get("tool_calls"):
            for tool_call in result["tool_calls"]:
                assert "tool_name" in tool_call, "工具调用应该有名称"
                assert "result" in tool_call, "工具调用应该有结果"
                assert "success" in tool_call, "工具调用应该有成功标志"

        print("✅ 真实LLM调用测试通过！")

        return result  # 返回结果供进一步分析

    @pytest.mark.asyncio
    async def test_mixed_mode_streaming_real_llm(self, react_node):
        """测试混合模式：使用真实LLM流式调用"""
        # 构建测试消息
        messages = [
            {"role": "system", "content": react_node._build_function_calling_system_prompt()},
            {"role": "user", "content": "我想开发一个在线教育平台，请帮我分析需求"}
        ]

        print("🚀 开始真实流式LLM调用测试...")

        # 收集流式内容
        streamed_content = []

        async def stream_callback(content: str):
            streamed_content.append(content)
            print(content, end='', flush=True)

        # 执行真实的流式Function Calling
        result = await react_node._execute_with_function_calling_stream(
            messages, stream_callback, {}
        )

        print(f"\n✅ 流式LLM调用完成")
        print(f"📝 最终消息: {result.get('user_message', '')}")
        print(f"🔧 工具调用数量: {len(result.get('tool_calls', []))}")
        print(f"🎯 执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"💭 推理过程: {result.get('reasoning', '')}")
        print(f"🔄 对话轮数: {result.get('conversation_rounds', 1)}")

        # 验证流式内容
        total_streamed = ''.join(streamed_content)
        print(f"📡 流式内容长度: {len(total_streamed)} 字符")

        # 基本验证
        assert result["decision_success"] is True, "流式LLM调用应该成功"
        assert "user_message" in result, "应该有用户消息"

        # 验证流式内容
        if streamed_content:
            assert len(total_streamed) > 0, "应该有流式内容输出"

        print("✅ 真实流式LLM调用测试通过！")

        return result

    @pytest.mark.asyncio
    async def test_optimized_streaming_with_tools(self, react_node):
        """测试优化后的流式输出与工具调用协调"""
        # 构建测试消息
        messages = [
            {"role": "system", "content": react_node._build_function_calling_system_prompt()},
            {"role": "user", "content": "我想开发一个博客系统，请帮我分析需求并调研技术方案"}
        ]

        print("🚀 开始优化流式输出测试...")

        # 收集所有流式输出
        stream_log = []

        async def detailed_stream_callback(content: str):
            stream_log.append(content)
            print(f"📡 [{len(stream_log)}] {content}", end='', flush=True)

        # 执行优化后的流式Function Calling
        result = await react_node._execute_with_function_calling_stream(
            messages, detailed_stream_callback, {}
        )

        print(f"\n✅ 优化流式调用完成")
        print(f"📝 最终消息: {result.get('user_message', '')}")
        print(f"🔧 工具调用数量: {len(result.get('tool_calls', []))}")
        print(f"🎯 执行模式: {result.get('execution_mode', 'unknown')}")
        print(f"💭 推理过程: {result.get('reasoning', '')}")

        # 分析流式输出
        total_stream_content = ''.join(stream_log)
        print(f"📡 总流式内容长度: {len(total_stream_content)} 字符")
        print(f"📡 流式块数量: {len(stream_log)}")

        # 检查流式输出中的工具执行反馈
        tool_feedback_count = sum(1 for item in stream_log if any(
            keyword in item for keyword in ['🔧', '✅', '❌', '⏳']
        ))
        print(f"🔧 工具执行反馈数量: {tool_feedback_count}")

        # 基本验证
        assert result["decision_success"] is True, "优化流式调用应该成功"
        assert "user_message" in result, "应该有用户消息"

        # 如果流式输出为空，可能是模型不支持流式或回退到了标准调用
        if len(stream_log) == 0:
            print("⚠️ 流式输出为空，可能模型不支持流式或回退到标准调用")
            # 在这种情况下，验证是否有有效的响应
            assert len(result.get("user_message", "")) > 0 or len(result.get("tool_calls", [])) > 0, "应该有有效的响应或工具调用"
        else:
            # 如果有流式输出，验证其质量
            assert result.get("execution_mode") == "stream_mixed", "应该是流式混合模式"

        print("✅ 优化流式输出测试通过！")

        return result

    @pytest.mark.asyncio
    async def test_determine_next_action(self, react_node):
        """测试下一步行动决策"""
        # 测试无工具调用
        next_action = react_node._determine_next_action([], "Hello")
        assert next_action == "continue_conversation"

        # 测试单个成功的需求分析
        tool_calls = [
            {"tool_name": "requirements_analysis", "success": True}
        ]
        next_action = react_node._determine_next_action(tool_calls, "分析完成")
        assert next_action == "continue_conversation"

        # 测试多个成功的工具调用
        tool_calls = [
            {"tool_name": "requirements_analysis", "success": True},
            {"tool_name": "short_planning", "success": True}
        ]
        next_action = react_node._determine_next_action(tool_calls, "处理完成")
        assert next_action == "complete"

        # 测试有失败的工具调用
        tool_calls = [
            {"tool_name": "requirements_analysis", "success": True},
            {"tool_name": "research", "success": False}
        ]
        next_action = react_node._determine_next_action(tool_calls, "部分失败")
        assert next_action == "continue_conversation"

    @pytest.mark.asyncio
    async def test_build_reasoning(self, react_node):
        """测试推理说明构建"""
        # 测试无工具调用
        reasoning = react_node._build_reasoning([], "Hello")
        assert "未调用工具" in reasoning

        # 测试单个成功工具调用
        tool_calls = [
            {"tool_name": "requirements_analysis", "success": True}
        ]
        reasoning = react_node._build_reasoning(tool_calls, "分析完成")
        assert "单个工具调用" in reasoning
        assert "requirements_analysis" in reasoning
        assert "成功" in reasoning

        # 测试多个混合结果的工具调用
        tool_calls = [
            {"tool_name": "requirements_analysis", "success": True},
            {"tool_name": "research", "success": False}
        ]
        reasoning = react_node._build_reasoning(tool_calls, "混合结果")
        assert "并行执行了 2 个工具调用" in reasoning
        assert "成功: requirements_analysis" in reasoning
        assert "失败: research" in reasoning


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
