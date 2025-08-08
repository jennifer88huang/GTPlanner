"""
状态管理器

负责共享状态的构建、更新和分析，分离状态管理逻辑。
"""

from typing import Dict, List, Any
from .constants import StateKeys, ToolNames, DefaultValues


class StateManager:
    """状态管理器类"""

    def __init__(self):
        # 工具执行历史跟踪
        self.tool_execution_history = []
    
    def build_state_description(self, shared: Dict[str, Any], user_message: str) -> str:
        """
        构建当前状态描述
        
        Args:
            shared: 共享状态字典
            user_message: 用户消息
            
        Returns:
            状态描述字符串
        """
        # 分析已完成的任务
        completed_tasks = self._get_completed_tasks(shared)
        
        # 分析数据完整性
        completeness_status = self._analyze_data_completeness(shared)
        
        # 计算处理轮次
        react_cycles = shared.get(StateKeys.REACT_CYCLE_COUNT, 0)
        
        # 分析Agent调用可行性
        feasibility_status = self._analyze_agent_feasibility(shared, user_message)
        
        # 获取工具执行摘要
        execution_summary = self.get_tool_execution_summary(shared)

        description = f"""
当前状态分析：

用户最新消息: {user_message}

已完成的任务: {', '.join(completed_tasks) if completed_tasks else '无'}

工具执行历史摘要:
- 总执行次数: {execution_summary['total_executions']}
- 成功执行: {execution_summary['successful_executions']}
- 失败执行: {execution_summary['failed_executions']}
- 已执行工具: {', '.join(execution_summary['tools_executed']) if execution_summary['tools_executed'] else '无'}

数据完整性检查:
{self._format_completeness_status(completeness_status)}

处理进度:
- ReAct循环次数: {react_cycles}
- 当前阶段: {shared.get(StateKeys.CURRENT_STAGE, DefaultValues.DEFAULT_STAGE)}
- 对话消息数: {len(shared.get(StateKeys.DIALOGUE_HISTORY, {}).get("messages", []))}

Agent调用可行性检查:
{self._format_feasibility_status(feasibility_status)}

请分析当前状态，决定下一步应该执行什么任务。

决策优先级：
1. 首先检查工具执行历史，避免重复调用已成功执行的工具
2. 判断用户意图（是否有具体项目需求）
3. 检查Agent调用可行性
4. 根据数据完整性选择最合适的行动
5. 优先选择用户交互，除非明确需要专业处理
"""
        return description
    
    def _get_completed_tasks(self, shared: Dict[str, Any]) -> List[str]:
        """
        获取已完成的任务列表 - 基于工具执行历史

        Args:
            shared: 共享状态字典

        Returns:
            已完成任务列表
        """
        completed_tasks = []

        # 优先从工具执行历史获取已完成任务
        executed_tools = self.get_successfully_executed_tools(shared)
        print(f"🔍 [DEBUG] 从执行历史获取的工具: {executed_tools}")
        completed_tasks.extend(executed_tools)

        # 兼容性检查：如果历史记录为空，回退到原有逻辑
        if not completed_tasks:
            print("🔍 [DEBUG] 执行历史为空，回退到数据检查")
            if shared.get(StateKeys.STRUCTURED_REQUIREMENTS):
                completed_tasks.append(ToolNames.REQUIREMENTS_ANALYSIS)
            if shared.get(StateKeys.CONFIRMATION_DOCUMENT):
                completed_tasks.append(ToolNames.SHORT_PLANNING)
            if shared.get(StateKeys.RESEARCH_FINDINGS):
                completed_tasks.append(ToolNames.RESEARCH)
            if shared.get(StateKeys.AGENT_DESIGN_DOCUMENT):
                completed_tasks.append(ToolNames.ARCHITECTURE_DESIGN)
            print(f"🔍 [DEBUG] 从数据检查获取的任务: {completed_tasks}")

        # 去重并保持顺序
        final_tasks = list(dict.fromkeys(completed_tasks))
        print(f"🔍 [DEBUG] 最终已完成任务列表: {final_tasks}")
        return final_tasks
    
    def _analyze_data_completeness(self, shared: Dict[str, Any]) -> Dict[str, bool]:
        """
        分析数据完整性

        Args:
            shared: 共享状态字典

        Returns:
            完整性状态字典
        """
        try:
            # 调试：检查状态键
            print(f"🔍 [DEBUG] 检查数据完整性，shared键: {list(shared.keys())}")

            requirements_data = shared.get(StateKeys.STRUCTURED_REQUIREMENTS)
            print(f"🔍 [DEBUG] STRUCTURED_REQUIREMENTS值: {requirements_data}")
            print(f"🔍 [DEBUG] STRUCTURED_REQUIREMENTS类型: {type(requirements_data)}")

            # 安全地检查requirements_data
            requirements_complete = False
            if requirements_data and isinstance(requirements_data, dict):
                requirements_complete = bool(requirements_data.get("project_overview"))
                print(f"🔍 [DEBUG] project_overview存在: {requirements_complete}")

            # 安全地检查其他数据
            research_data = shared.get(StateKeys.RESEARCH_FINDINGS)
            research_complete = False
            if research_data and isinstance(research_data, dict):
                research_complete = bool(research_data.get("topics"))

            return {
                "requirements_complete": requirements_complete,
                "planning_complete": bool(shared.get(StateKeys.CONFIRMATION_DOCUMENT)),
                "research_complete": research_complete,
                "architecture_complete": bool(shared.get(StateKeys.AGENT_DESIGN_DOCUMENT))
            }
        except Exception as e:
            print(f"🔍 [DEBUG] 数据完整性检查出错: {e}")
            return {
                "requirements_complete": False,
                "planning_complete": False,
                "research_complete": False,
                "architecture_complete": False
            }
    
    def _analyze_agent_feasibility(self, shared: Dict[str, Any], user_message: str) -> Dict[str, bool]:
        """
        分析Agent调用可行性
        
        Args:
            shared: 共享状态字典
            user_message: 用户消息
            
        Returns:
            可行性状态字典
        """
        completeness = self._analyze_data_completeness(shared)
        
        return {
            "requirements_analysis_feasible": bool(user_message),
            "short_planning_feasible": completeness["requirements_complete"],
            "research_feasible": completeness["requirements_complete"],
            "architecture_design_feasible": (
                completeness["requirements_complete"] and 
                completeness["research_complete"]
            )
        }
    
    def _format_completeness_status(self, completeness: Dict[str, bool]) -> str:
        """
        格式化完整性状态
        
        Args:
            completeness: 完整性状态字典
            
        Returns:
            格式化的状态字符串
        """
        status_lines = []
        status_map = {
            "requirements_complete": "需求分析",
            "planning_complete": "短规划文档",
            "research_complete": "研究调研",
            "architecture_complete": "架构设计"
        }
        
        for key, label in status_map.items():
            status = "✅ 已完成" if completeness.get(key, False) else "❌ 未完成"
            status_lines.append(f"- {label}: {status}")
        
        return "\n".join(status_lines)
    
    def _format_feasibility_status(self, feasibility: Dict[str, bool]) -> str:
        """
        格式化可行性状态
        
        Args:
            feasibility: 可行性状态字典
            
        Returns:
            格式化的状态字符串
        """
        status_lines = []
        status_map = {
            "requirements_analysis_feasible": ("requirements_analysis", "缺少用户输入"),
            "short_planning_feasible": ("short_planning", "需要先完成需求分析"),
            "research_feasible": ("research", "需要先完成需求分析"),
            "architecture_design_feasible": ("architecture_design", "需要先完成需求分析和研究")
        }
        
        for key, (tool_name, error_msg) in status_map.items():
            if feasibility.get(key, False):
                status = "✅ 可调用"
            else:
                status = f"❌ {error_msg}"
            status_lines.append(f"- {tool_name}: {status}")
        
        return "\n".join(status_lines)
    
    def update_shared_state_with_tool_result(
        self,
        shared: Dict[str, Any],
        tool_name: str,
        tool_result: Dict[str, Any]
    ) -> None:
        """
        更新共享状态中的工具执行结果

        Args:
            shared: 共享状态字典
            tool_name: 工具名称
            tool_result: 工具执行结果
        """
        print(f"🔍 [DEBUG] 更新共享状态: {tool_name}, 成功: {tool_result.get('success')}")

        if not tool_result.get("success"):
            print(f"🔍 [DEBUG] 工具执行失败，跳过状态更新")
            return

        result_data = tool_result.get("result")
        if not result_data:
            print(f"🔍 [DEBUG] 工具结果为空，跳过状态更新")
            return

        # 根据工具类型更新相应的共享状态
        state_mapping = {
            ToolNames.REQUIREMENTS_ANALYSIS: StateKeys.STRUCTURED_REQUIREMENTS,
            ToolNames.SHORT_PLANNING: StateKeys.CONFIRMATION_DOCUMENT,
            ToolNames.RESEARCH: StateKeys.RESEARCH_FINDINGS,
            ToolNames.ARCHITECTURE_DESIGN: StateKeys.AGENT_DESIGN_DOCUMENT
        }

        if tool_name in state_mapping:
            state_key = state_mapping[tool_name]
            shared[state_key] = result_data
            print(f"🔍 [DEBUG] 已更新状态键: {state_key}")
        else:
            print(f"🔍 [DEBUG] 未知工具名称: {tool_name}")
    
    def add_assistant_message_to_history(
        self, 
        shared: Dict[str, Any], 
        user_message: str,
        tool_calls: List[Dict[str, Any]],
        reasoning: str,
        confidence: float = DefaultValues.DEFAULT_CONFIDENCE
    ) -> None:
        """
        添加AI回复到对话历史
        
        Args:
            shared: 共享状态字典
            user_message: 用户消息
            tool_calls: 工具调用列表
            reasoning: 推理过程
            confidence: 置信度
        """
        import time
        
        if user_message:
            dialogue_history = shared.setdefault(StateKeys.DIALOGUE_HISTORY, {})
            messages = dialogue_history.setdefault("messages", [])
            
            messages.append({
                "timestamp": time.time(),
                "role": "assistant",
                "content": user_message,
                "metadata": {
                    "agent_source": "react_orchestrator_function_calling",
                    "tool_calls": tool_calls,
                    "reasoning": reasoning,
                    "confidence": confidence
                }
            })
    
    def increment_react_cycle(self, shared: Dict[str, Any]) -> int:
        """
        增加ReAct循环计数
        
        Args:
            shared: 共享状态字典
            
        Returns:
            新的循环计数
        """
        react_cycles = shared.get(StateKeys.REACT_CYCLE_COUNT, 0) + 1
        shared[StateKeys.REACT_CYCLE_COUNT] = react_cycles
        return react_cycles
    
    def get_user_message_from_history(self, shared: Dict[str, Any]) -> str:
        """
        从对话历史中获取最新用户消息
        
        Args:
            shared: 共享状态字典
            
        Returns:
            最新用户消息
        """
        dialogue_history = shared.get(StateKeys.DIALOGUE_HISTORY, {})
        messages = dialogue_history.get("messages", [])
        
        # 获取最新用户消息
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content", "")
        
        return ""

    def record_tool_execution(
        self,
        shared: Dict[str, Any],
        tool_name: str,
        tool_args: Dict[str, Any],
        execution_result: Dict[str, Any],
        execution_time: float = None
    ) -> None:
        """
        记录工具执行历史

        Args:
            shared: 共享状态字典
            tool_name: 工具名称
            tool_args: 工具参数
            execution_result: 执行结果
            execution_time: 执行时间（秒）
        """
        import time

        # 确保shared中有工具执行历史
        if 'tool_execution_history' not in shared:
            shared['tool_execution_history'] = []

        execution_record = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "tool_args": tool_args,
            "execution_result": execution_result,
            "execution_time": execution_time,
            "success": execution_result.get("success", False),
            "session_id": shared.get("session_id", "unknown")
        }

        shared['tool_execution_history'].append(execution_record)
        print(f"🔍 [DEBUG] 记录工具执行: {tool_name}, 成功: {execution_record['success']}")
        print(f"🔍 [DEBUG] 当前历史记录数量: {len(shared['tool_execution_history'])}")

        # 保持历史记录在合理范围内（最多保留50条）
        if len(shared['tool_execution_history']) > 50:
            shared['tool_execution_history'] = shared['tool_execution_history'][-50:]

    def get_successfully_executed_tools(self, shared: Dict[str, Any]) -> List[str]:
        """
        获取成功执行的工具列表

        Args:
            shared: 共享状态字典

        Returns:
            成功执行的工具名称列表
        """
        history = shared.get('tool_execution_history', [])
        print(f"🔍 [DEBUG] shared状态键: {list(shared.keys())}")
        print(f"🔍 [DEBUG] 工具执行历史长度: {len(history)}")
        if history:
            print(f"🔍 [DEBUG] 最新记录: {history[-1]}")

        successful_tools = []

        for record in history:
            if record.get("success", False) and record.get("tool_name"):
                tool_name = record["tool_name"]
                if tool_name not in successful_tools:
                    successful_tools.append(tool_name)

        return successful_tools

    def get_tool_execution_summary(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取工具执行摘要

        Args:
            shared: 共享状态字典

        Returns:
            工具执行摘要
        """
        history = shared.get('tool_execution_history', [])

        summary = {
            "total_executions": len(history),
            "successful_executions": 0,
            "failed_executions": 0,
            "tools_executed": set(),
            "last_execution_time": None,
            "execution_timeline": []
        }

        for record in history:
            if record.get("success", False):
                summary["successful_executions"] += 1
            else:
                summary["failed_executions"] += 1

            tool_name = record.get("tool_name")
            if tool_name:
                summary["tools_executed"].add(tool_name)

            timestamp = record.get("timestamp")
            if timestamp:
                summary["last_execution_time"] = max(
                    summary["last_execution_time"] or 0,
                    timestamp
                )
                summary["execution_timeline"].append({
                    "tool": tool_name,
                    "timestamp": timestamp,
                    "success": record.get("success", False)
                })

        # 转换set为list以便JSON序列化
        summary["tools_executed"] = list(summary["tools_executed"])

        return summary

    def has_tool_been_executed(self, shared: Dict[str, Any], tool_name: str) -> bool:
        """
        检查指定工具是否已经被执行过

        Args:
            shared: 共享状态字典
            tool_name: 工具名称

        Returns:
            是否已执行过
        """
        history = shared.get('tool_execution_history', [])

        for record in history:
            if (record.get("tool_name") == tool_name and
                record.get("success", False)):
                return True

        return False

    def get_last_execution_of_tool(self, shared: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """
        获取指定工具的最后一次执行记录

        Args:
            shared: 共享状态字典
            tool_name: 工具名称

        Returns:
            最后一次执行记录，如果没有则返回空字典
        """
        history = shared.get('tool_execution_history', [])

        # 从后往前查找
        for record in reversed(history):
            if record.get("tool_name") == tool_name:
                return record

        return {}
