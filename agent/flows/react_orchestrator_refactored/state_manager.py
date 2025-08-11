"""
状态管理器 - 基于统一上下文管理

负责共享状态的构建、更新和分析，现在基于统一上下文管理器实现。
消除了重复的状态管理代码，提供统一的接口。
"""

from typing import Dict, List, Any
from core.unified_context import get_context
from .constants import StateKeys, ToolNames, DefaultValues


class StateManager:
    """状态管理器类 - 基于统一上下文"""

    def __init__(self):
        # 获取统一上下文实例
        self.context = get_context()
    
    def build_state_description(self, shared: Dict[str, Any], user_message: str) -> str:
        """
        构建当前状态描述
        
        Args:
            shared: 共享状态字典（保持兼容性，但实际使用统一上下文）
            user_message: 用户消息
            
        Returns:
            状态描述字符串
        """
        # 从统一上下文获取状态信息
        context_summary = self.context.get_context_summary()
        tool_summary = self.context.get_tool_summary()
        
        # 分析数据完整性
        completeness_status = self._analyze_data_completeness_from_context()
        
        description = f"""
当前状态分析：

用户最新消息: {user_message}

项目阶段: {context_summary.get('stage', 'initialization')}

数据完整性状态:
- 需求分析: {'✅ 完成' if completeness_status['requirements_complete'] else '❌ 未完成'}
- 规划文档: {'✅ 完成' if completeness_status['planning_complete'] else '❌ 未完成'}
- 研究调研: {'✅ 完成' if completeness_status['research_complete'] else '❌ 未完成'}
- 架构设计: {'✅ 完成' if completeness_status['architecture_complete'] else '❌ 未完成'}

消息数量: {context_summary.get('message_count', 0)}
工具执行次数: {context_summary.get('tool_execution_count', 0)}

最近工具执行: {tool_summary}
"""
        return description.strip()
    
    def _analyze_data_completeness_from_context(self) -> Dict[str, bool]:
        """从统一上下文分析数据完整性"""
        return {
            "requirements_complete": bool(self.context.get_state("structured_requirements")),
            "planning_complete": bool(self.context.get_state("planning_document")),
            "research_complete": bool(self.context.get_state("research_findings")),
            "architecture_complete": bool(self.context.get_state("architecture_document"))
        }
    
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
            shared: 共享状态字典（保持兼容性）
            user_message: 用户消息
            tool_calls: 工具调用列表
            reasoning: 推理过程
            confidence: 置信度
        """
        if user_message:
            # 使用统一上下文添加消息
            self.context.add_assistant_message(user_message, tool_calls)
    
    def increment_react_cycle(self, shared: Dict[str, Any]) -> int:
        """
        增加ReAct循环计数
        
        Args:
            shared: 共享状态字典（保持兼容性）
            
        Returns:
            新的循环计数
        """
        # 从统一上下文获取或更新循环计数
        current_count = self.context.get_state("react_cycle_count", 0)
        new_count = current_count + 1
        self.context.update_state("react_cycle_count", new_count)
        return new_count
    
    def get_user_message_from_history(self, shared: Dict[str, Any]) -> str:
        """
        从对话历史中获取最新用户消息
        
        Args:
            shared: 共享状态字典（保持兼容性）
            
        Returns:
            最新用户消息
        """
        latest_user_message = self.context.get_latest_user_message()
        return latest_user_message or ""
    
    def record_tool_execution(
        self,
        shared: Dict[str, Any],
        tool_name: str,
        tool_args: Dict[str, Any],
        tool_result: Dict[str, Any],
        execution_time: float = None
    ) -> None:
        """
        记录工具执行历史
        
        Args:
            shared: 共享状态字典（保持兼容性）
            tool_name: 工具名称
            tool_args: 工具参数
            tool_result: 执行结果
            execution_time: 执行时间
        """
        self.context.record_tool_execution(
            tool_name=tool_name,
            arguments=tool_args,
            result=tool_result,
            execution_time=execution_time
        )
    
    def update_shared_state_with_tool_result(
        self,
        shared: Dict[str, Any],
        tool_name: str,
        tool_result: Dict[str, Any]
    ) -> None:
        """
        更新共享状态（基于工具执行结果）
        
        Args:
            shared: 共享状态字典（保持兼容性）
            tool_name: 工具名称
            tool_result: 工具结果
        """
        if tool_result.get("success") and "result" in tool_result:
            result_data = tool_result["result"]
            
            # 根据工具名称更新相应的状态
            state_mapping = {
                "requirements_analysis": "structured_requirements",
                "short_planning": "planning_document",
                "research": "research_findings",
                "architecture_design": "architecture_document"
            }
            
            if tool_name in state_mapping:
                self.context.update_state(state_mapping[tool_name], result_data)
                
                # 根据工具类型更新项目阶段
                stage_mapping = {
                    "requirements_analysis": "requirements",
                    "short_planning": "planning",
                    "research": "planning",
                    "architecture_design": "architecture"
                }
                
                if tool_name in stage_mapping:
                    self.context.update_stage(stage_mapping[tool_name])
    
    def get_tool_execution_summary(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取工具执行摘要
        
        Args:
            shared: 共享状态字典（保持兼容性）
            
        Returns:
            工具执行摘要字典
        """
        tool_history = self.context.tool_history
        
        if not tool_history:
            return {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "tools_executed": []
            }
        
        successful = sum(1 for tool in tool_history if tool.get("success", False))
        failed = len(tool_history) - successful
        tools_executed = list(set(tool["tool_name"] for tool in tool_history))
        
        return {
            "total_executions": len(tool_history),
            "successful_executions": successful,
            "failed_executions": failed,
            "tools_executed": tools_executed
        }
    
    def get_context_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要（新增方法）
        
        Returns:
            上下文摘要字典
        """
        return self.context.get_context_summary()
    
    def cleanup_duplicate_messages(self) -> int:
        """
        清理重复消息（新增方法）
        
        Returns:
            清理的消息数量
        """
        if not self.context.session_id:
            return 0
        
        original_count = len(self.context.messages)
        
        # 使用内容哈希去重
        seen_hashes = set()
        unique_messages = []
        
        for msg in self.context.messages:
            if msg.content_hash not in seen_hashes:
                seen_hashes.add(msg.content_hash)
                unique_messages.append(msg)
        
        self.context.messages = unique_messages
        
        # 重建缓存
        self.context.message_hashes.clear()
        for msg in unique_messages:
            self.context.message_hashes.add(msg.content_hash)
        
        cleaned_count = original_count - len(unique_messages)
        
        if cleaned_count > 0:
            print(f"🧹 StateManager已清理 {cleaned_count} 条重复消息")
        
        return cleaned_count
