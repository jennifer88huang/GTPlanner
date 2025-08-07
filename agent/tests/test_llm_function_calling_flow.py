#!/usr/bin/env python3
"""
LLM Function Calling流程测试

测试LLM使用Function Calling实现的多轮工具调用和文本输出：
用户输入 -> [tool1] -> LLM处理 -> [tool2] -> LLM处理 -> 最终输出

这个测试模拟真实的对话场景，其中LLM会：
1. 分析用户需求并调用需求分析工具
2. 基于需求分析结果调用短期规划工具
3. 可能调用技术调研工具
4. 最终生成综合性的回复
"""

import asyncio
import json
from typing import Dict, Any, List
from utils.openai_client import get_openai_client
from agent.function_calling import get_agent_function_definitions, execute_agent_tool


class LLMFunctionCallingFlowTest:
    """LLM Function Calling流程测试类"""
    
    def __init__(self):
        self.client = get_openai_client()
        self.tools = get_agent_function_definitions()
        self.conversation_history = []
    
    async def test_single_tool_call_flow(self):
        """测试单个工具调用流程"""
        print("🔄 测试单个工具调用流程...")
        
        # 用户输入
        user_input = "我想开发一个在线教育平台，支持视频课程和在线考试功能"
        
        # 系统提示
        system_prompt = """你是GTPlanner助手，专门帮助用户进行项目规划。
当用户提出开发需求时，你需要：
1. 使用requirements_analysis工具分析用户需求
2. 基于分析结果，为用户提供专业的项目建议

请始终使用工具来处理用户的需求，不要直接回答。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 第一轮：LLM调用工具
        print(f"👤 用户: {user_input}")
        response = await self.client.chat_completion_async(
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        # 处理工具调用
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            print(f"🔧 LLM调用工具: {tool_name}")
            print(f"📝 工具参数: {tool_args}")
            
            # 执行工具
            tool_result = await execute_agent_tool(tool_name, tool_args)
            
            # 添加工具调用和结果到对话历史
            messages.append(response.choices[0].message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(tool_result, ensure_ascii=False)
            })
            
            # 第二轮：LLM基于工具结果生成回复
            final_response = await self.client.chat_completion_async(
                messages=messages,
                tools=self.tools,
                tool_choice="none"  # 不再调用工具，只生成文本
            )
            
            final_content = final_response.choices[0].message.content
            print(f"🤖 LLM最终回复: {final_content[:200]}...")
            
            return {
                "success": True,
                "tool_called": tool_name,
                "tool_result": tool_result,
                "final_response": final_content
            }
        else:
            print("❌ LLM没有调用工具")
            return {"success": False, "error": "No tool called"}
    
    async def test_multi_tool_call_flow(self):
        """测试多工具调用流程"""
        print("\n🔄 测试多工具调用流程...")
        
        # 用户输入
        user_input = "我需要开发一个电商系统，请帮我分析需求并制定开发计划"
        
        # 系统提示
        system_prompt = """你是GTPlanner助手，专门帮助用户进行项目规划。
当用户提出开发需求时，你需要按顺序：
1. 首先使用requirements_analysis工具分析用户需求
2. 然后使用short_planning工具制定开发计划
3. 最后为用户提供综合性的项目建议

请逐步使用工具，每次只调用一个工具。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        print(f"👤 用户: {user_input}")
        
        tools_called = []
        max_rounds = 5  # 最多5轮对话
        
        for round_num in range(max_rounds):
            print(f"\n--- 第 {round_num + 1} 轮 ---")
            
            # LLM响应
            response = await self.client.chat_completion_async(
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            # 检查是否有工具调用
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 LLM调用工具: {tool_name}")
                print(f"📝 工具参数: {tool_args}")
                
                # 执行工具
                tool_result = await execute_agent_tool(tool_name, tool_args)
                tools_called.append({
                    "tool": tool_name,
                    "args": tool_args,
                    "result": tool_result
                })
                
                # 添加到对话历史
                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
                
                print(f"✅ 工具执行{'成功' if tool_result.get('success') else '失败'}")
                
            else:
                # 没有工具调用，LLM生成最终回复
                final_content = response.choices[0].message.content
                print(f"🤖 LLM最终回复: {final_content[:300]}...")
                
                return {
                    "success": True,
                    "tools_called": tools_called,
                    "final_response": final_content,
                    "rounds": round_num + 1
                }
        
        return {
            "success": False,
            "error": "达到最大轮数限制",
            "tools_called": tools_called
        }
    
    async def test_conditional_tool_call_flow(self):
        """测试条件性工具调用流程"""
        print("\n🔄 测试条件性工具调用流程...")
        
        # 用户输入 - 一个需要技术调研的复杂需求
        user_input = "我想开发一个AI驱动的智能客服系统，需要支持多语言和情感分析，请帮我分析技术方案"
        
        # 系统提示
        system_prompt = """你是GTPlanner助手，专门帮助用户进行项目规划。
根据用户需求的复杂程度，你需要智能选择合适的工具：

1. 对于所有开发需求，都要先使用requirements_analysis工具
2. 如果涉及复杂技术或新技术，使用research工具进行技术调研
3. 如果用户明确要求制定计划，使用short_planning工具
4. 最后提供综合建议

请根据实际需要选择工具，不要盲目调用所有工具。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        print(f"👤 用户: {user_input}")
        
        tools_called = []
        conversation_log = []
        max_rounds = 6
        
        for round_num in range(max_rounds):
            print(f"\n--- 第 {round_num + 1} 轮 ---")
            
            response = await self.client.chat_completion_async(
                messages=messages,
                tools=self.tools,
                tool_choice="auto"
            )
            
            if response.choices[0].message.tool_calls:
                tool_call = response.choices[0].message.tool_calls[0]
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                print(f"🔧 LLM智能选择工具: {tool_name}")
                
                # 执行工具
                tool_result = await execute_agent_tool(tool_name, tool_args)
                tools_called.append(tool_name)
                
                # 记录对话
                conversation_log.append({
                    "round": round_num + 1,
                    "action": "tool_call",
                    "tool": tool_name,
                    "success": tool_result.get('success', False)
                })
                
                # 更新对话历史
                messages.append(response.choices[0].message)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                })
                
            else:
                # 最终回复
                final_content = response.choices[0].message.content
                conversation_log.append({
                    "round": round_num + 1,
                    "action": "final_response",
                    "content_length": len(final_content)
                })
                
                print(f"🤖 LLM最终回复: {final_content[:300]}...")
                
                return {
                    "success": True,
                    "tools_called": tools_called,
                    "conversation_log": conversation_log,
                    "final_response": final_content
                }
        
        return {
            "success": False,
            "error": "达到最大轮数限制",
            "tools_called": tools_called,
            "conversation_log": conversation_log
        }
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始LLM Function Calling流程测试\n")
        
        # 测试1：单工具调用
        result1 = await self.test_single_tool_call_flow()
        print(f"✅ 单工具调用测试: {'成功' if result1['success'] else '失败'}")
        
        # 测试2：多工具调用
        result2 = await self.test_multi_tool_call_flow()
        print(f"✅ 多工具调用测试: {'成功' if result2['success'] else '失败'}")
        if result2['success']:
            print(f"   调用了 {len(result2['tools_called'])} 个工具，共 {result2['rounds']} 轮对话")
        
        # 测试3：条件性工具调用
        result3 = await self.test_conditional_tool_call_flow()
        print(f"✅ 条件性工具调用测试: {'成功' if result3['success'] else '失败'}")
        if result3['success']:
            print(f"   智能选择了工具: {', '.join(result3['tools_called'])}")
        
        print(f"\n🎉 所有测试完成！")
        return {
            "single_tool": result1,
            "multi_tool": result2,
            "conditional_tool": result3
        }


async def main():
    """主函数"""
    test = LLMFunctionCallingFlowTest()
    results = await test.run_all_tests()
    
    # 输出测试总结
    print("\n📊 测试总结:")
    for test_name, result in results.items():
        status = "✅ 成功" if result.get('success') else "❌ 失败"
        print(f"  {test_name}: {status}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        test_type = sys.argv[1]
        test = LLMFunctionCallingFlowTest()
        
        if test_type == "single":
            asyncio.run(test.test_single_tool_call_flow())
        elif test_type == "multi":
            asyncio.run(test.test_multi_tool_call_flow())
        elif test_type == "conditional":
            asyncio.run(test.test_conditional_tool_call_flow())
        else:
            print("用法: python test_llm_function_calling_flow.py [single|multi|conditional]")
    else:
        asyncio.run(main())
