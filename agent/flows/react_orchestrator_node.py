"""
ReAct Orchestrator Node

基于你的demo代码重构的ReAct主控制器。
参考MainReActAgent的设计，作为中心调度器，通过动态路由连接到各个专业Agent。
"""

import json
import time
from typing import Dict, List, Any
from pocketflow import Node, AsyncNode
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from call_llm import call_llm


class ReActOrchestratorNode(AsyncNode):
    """ReAct主控制器 - 异步版本，支持流式LLM调用"""

    def __init__(self):
        super().__init__()
        self.name = "ReActOrchestratorNode"
        self.description = "异步ReAct主控制器，支持流式输出"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """异步准备ReAct执行环境"""
        try:
            # 获取对话历史
            dialogue_history = shared.get("dialogue_history", {})
            messages = dialogue_history.get("messages", [])
            
            # 获取最新用户消息
            user_message = ""
            if messages:
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_message = msg.get("content", "")
                        break
            
            # 获取当前状态
            current_stage = shared.get("current_stage", "initialization")
            
            # 构建状态描述
            state_info = self._build_state_description(shared, user_message)
            
            return {
                "success": True,
                "user_message": user_message,
                "current_stage": current_stage,
                "state_info": state_info,
                "shared_data": shared
            }
            
        except Exception as e:
            return {"error": f"ReAct preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步ReAct推理和决策逻辑"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            user_message = prep_result["user_message"]
            state_info = prep_result["state_info"]
            
            # 构建系统提示词
            system_prompt = self._build_system_prompt()

            # 异步让LLM进行推理和决策
            shared_data = prep_result.get("shared_data", {})
            decision = await self._make_decision_async(system_prompt, state_info, shared_data)
            
            return {
                "user_message": decision.get("user_message", "我正在处理您的请求..."),
                "next_action": decision.get("next_action", "user_interaction"),
                "reasoning": decision.get("reasoning", "继续处理用户请求"),
                "confidence": decision.get("confidence", 0.5),
                "requires_user_input": decision.get("requires_user_input", True),
                "decision_success": True
            }
            
        except Exception as e:
            return {"error": f"ReAct execution failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """异步更新共享状态并返回下一个节点路由"""
        try:
            if "error" in exec_res:
                shared["react_error"] = exec_res["error"]
                return "error"

            # 更新ReAct循环计数
            react_cycles = shared.get("react_cycle_count", 0) + 1
            shared["react_cycle_count"] = react_cycles

            # 添加AI回复到对话历史
            user_message = exec_res.get("user_message", "")
            if user_message:
                shared.setdefault("dialogue_history", {}).setdefault("messages", []).append({
                    "timestamp": time.time(),
                    "role": "assistant",
                    "content": user_message,
                    "metadata": {
                        "agent_source": "react_orchestrator",
                        "reasoning": exec_res.get("reasoning", ""),
                        "confidence": exec_res.get("confidence", 0.5)
                    }
                })

            # 根据决策返回下一个节点路由（参考demo的动态路由）
            next_action = exec_res.get("next_action", "user_interaction")

            # 动态路由到相应的Agent节点
            if next_action == "requirements_analysis":
                return "requirements_analysis"
            elif next_action == "short_planning":
                return "short_planning"
            elif next_action == "research":
                return "research"
            elif next_action == "architecture_design":
                return "architecture_design"
            elif next_action == "complete":
                return "complete"
            elif next_action == "user_interaction":
                return "wait_for_user"
            else:
                # 其他情况，等待用户输入
                return "wait_for_user"

        except Exception as e:
            shared["react_post_error"] = str(e)
            return "error"
    
    def _build_system_prompt(self) -> str:
        """构建ReAct系统提示词"""
        return """你是GTPlanner的智能助手，使用ReAct（推理-行动）模式工作。

你的任务是分析当前状态，进行推理，并决定下一步应该执行什么行动。

可用的专业Agent：
1. requirements_analysis - 需求分析Agent（仅当用户明确提出具体项目需求时使用）
2. short_planning - 短规划Agent（仅当需求分析完成且需要生成规划文档时使用）
3. research - 研究调研Agent（仅当需要调研特定技术或方案时使用）
4. architecture_design - 架构设计Agent（仅当需要设计具体系统架构时使用）
5. user_interaction - 用户交互（用于一般对话、问候、澄清问题）
6. complete - 任务完成

重要决策原则：
1. **保守原则**：如果不确定是否需要调用专业Agent，优先选择user_interaction
2. **需求驱动**：只有在用户明确表达项目需求时才调用requirements_analysis
3. **避免过度处理**：简单问候、介绍、澄清问题都应该使用user_interaction
4. **用户体验优先**：避免不必要的等待和复杂处理

请返回简洁的JSON格式：
{
    "user_message": "用自然、友好的语言与用户对话",
    "next_action": "requirements_analysis|short_planning|research|architecture_design|user_interaction|complete",
    "reasoning": "简要说明为什么选择这个行动",
    "confidence": 0.8,
    "requires_user_input": true/false
}"""
    
    def _build_state_description(self, shared: Dict[str, Any], user_message: str) -> str:
        """构建当前状态描述"""
        # 分析已完成的任务
        completed_tasks = []
        if shared.get("structured_requirements"):
            completed_tasks.append("requirements_analysis")
        if shared.get("confirmation_document"):
            completed_tasks.append("short_planning")
        if shared.get("research_findings"):
            completed_tasks.append("research")
        if shared.get("agent_design_document"):
            completed_tasks.append("architecture_design")
        
        # 分析数据完整性
        requirements_complete = bool(shared.get("structured_requirements", {}).get("project_overview"))
        research_complete = bool(shared.get("research_findings", {}).get("topics"))
        architecture_complete = bool(shared.get("agent_design_document"))
        
        # 计算处理轮次
        react_cycles = shared.get("react_cycle_count", 0)
        
        description = f"""
当前状态分析：

用户最新消息: {user_message}

已完成的任务: {', '.join(completed_tasks) if completed_tasks else '无'}

数据完整性检查:
- 需求分析: {'✅ 已完成' if requirements_complete else '❌ 未完成'}
- 短规划文档: {'✅ 已完成' if shared.get("confirmation_document") else '❌ 未完成'}
- 研究调研: {'✅ 已完成' if research_complete else '❌ 未完成'}
- 架构设计: {'✅ 已完成' if architecture_complete else '❌ 未完成'}

处理进度:
- ReAct循环次数: {react_cycles}
- 当前阶段: {shared.get("current_stage", "initialization")}
- 对话消息数: {len(shared.get("dialogue_history", {}).get("messages", []))}

Agent调用可行性检查:
- requirements_analysis: {'✅ 可调用' if user_message else '❌ 缺少用户输入'}
- short_planning: {'✅ 可调用' if requirements_complete else '❌ 需要先完成需求分析'}
- research: {'✅ 可调用' if requirements_complete else '❌ 需要先完成需求分析'}
- architecture_design: {'✅ 可调用' if (requirements_complete and research_complete) else '❌ 需要先完成需求分析和研究'}

请分析当前状态，决定下一步应该执行什么任务。

决策优先级：
1. 首先判断用户意图（是否有具体项目需求）
2. 检查Agent调用可行性
3. 根据数据完整性选择最合适的行动
4. 优先选择用户交互，除非明确需要专业处理
"""
        return description
    
    async def _make_decision_async(self, system_prompt: str, state_description: str, shared: Dict[str, Any] = None) -> Dict:
        """异步使用LLM进行决策，支持流式输出"""
        try:
            # 检查是否有流式回调
            stream_callback = shared.get("_stream_callback") if shared else None

            if stream_callback:
                # 使用流式调用
                return await self._make_decision_with_stream_async(system_prompt, state_description, stream_callback)
            else:
                # 使用普通调用
                result = call_llm(
                    prompt=f"{system_prompt}\n\n{state_description}",
                    is_json=True
                )

                # 确保返回的是字典格式
                if isinstance(result, str):
                    result = json.loads(result)

                return result

        except Exception as e:
            print(f"❌ ReAct决策失败: {e}")
            # 返回默认的安全决策
            return {
                "user_message": "我正在处理您的请求，请稍等...",
                "next_action": "user_interaction",
                "reasoning": f"LLM决策失败，使用默认交互模式: {str(e)}",
                "confidence": 0.3,
                "requires_user_input": True
            }

    async def _make_decision_with_stream_async(self, system_prompt: str, state_description: str, stream_callback) -> Dict:
        """异步流式LLM调用进行决策"""
        try:
            from utils.json_stream_parser import JSONStreamParser
            from call_llm import call_llm_stream_async

            # 创建JSON流式解析器
            parser = JSONStreamParser()
            collected_data = {}
            user_message_buffer = ""

            async def on_field_update(field_path: str, new_content: str, is_complete: bool):
                nonlocal user_message_buffer, collected_data

                # 处理user_message字段的流式输出
                if field_path == "user_message":
                    user_message_buffer += new_content

                    # 异步发送新增内容给CLI
                    if stream_callback and len(new_content) > 0:
                        try:
                            stream_data = {
                                "user_message": new_content,
                                "field_path": field_path,
                                "is_complete": is_complete
                            }
                            # 检查回调是否存在且是协程函数
                            import asyncio
                            if asyncio.iscoroutinefunction(stream_callback):
                                await stream_callback(stream_data, new_content)
                            elif callable(stream_callback):
                                stream_callback(stream_data, new_content)
                        except Exception as e:
                            print(f"⚠️ 流式回调失败: {e}")

                # 收集完整字段数据
                if is_complete:
                    collected_data[field_path] = user_message_buffer

            # 设置解析器回调
            parser.subscribe_field("user_message", on_field_update)

            # 异步调用流式LLM
            prompt = f"{system_prompt}\n\n{state_description}"

            async for chunk in call_llm_stream_async(prompt, is_json=True):
                if chunk:
                    parser.add_chunk(chunk)

            # 获取最终结果
            final_result = parser.get_result()

            # 构建返回结果
            result = {
                "user_message": collected_data.get("user_message", user_message_buffer),
                "next_action": final_result.get("next_action", "user_interaction"),
                "reasoning": final_result.get("reasoning", "流式处理完成"),
                "confidence": float(final_result.get("confidence", 0.5)),
                "requires_user_input": final_result.get("requires_user_input", True)
            }

            return result

        except Exception as e:
            print(f"❌ 异步流式决策失败: {e}")
            return {
                "user_message": "我正在处理您的请求，请稍等...",
                "next_action": "user_interaction",
                "reasoning": f"异步流式处理失败: {str(e)}",
                "confidence": 0.3,
                "requires_user_input": True
            }
    

