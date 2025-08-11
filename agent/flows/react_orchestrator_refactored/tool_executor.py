"""
工具执行器

负责工具调用的执行、验证和结果处理，支持并行执行和流式反馈。
"""

import json
import time
import asyncio
from typing import Dict, List, Any, Optional, Callable
from agent.function_calling import execute_agent_tool, validate_tool_arguments
from .constants import (
    ErrorMessages,
    DefaultValues, ToolCallPatterns
)


class ToolExecutor:
    """工具执行器类"""
    
    def __init__(self):
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }
    
    async def execute_tools_parallel(
        self, 
        tool_calls: List[Any],
        stream_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        并行执行多个工具调用
        
        Args:
            tool_calls: 工具调用列表
            stream_callback: 流式回调函数
            
        Returns:
            工具执行结果列表
        """
        if not tool_calls:
            return []
        

        
        # 创建异步任务
        tasks = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name

            
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError as e:
                print(f"❌ {ErrorMessages.JSON_PARSE_FAILED}: {e}")
                arguments = {}
            
            # 验证工具参数
            validation = validate_tool_arguments(tool_name, arguments)
            if not validation["valid"]:
                print(f"⚠️ {ErrorMessages.TOOL_VALIDATION_FAILED}: {validation['errors']}")
                continue
            

            
            # 创建异步任务
            if stream_callback:
                task = self._execute_single_tool_with_stream_feedback(
                    tool_call.id, tool_name, arguments, stream_callback
                )
            else:
                task = self._execute_single_tool(
                    tool_call.id, tool_name, arguments
                )
            tasks.append(task)
        
        print(f"🔧 创建了 {len(tasks)} 个工具执行任务")
        
        # 等待所有工具执行完成
        if tasks:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            return self._process_tool_results(tool_results)
        
        return []
    
    async def execute_custom_tool_calls(
        self, 
        custom_tool_calls: List[Dict[str, Any]],
        stream_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        执行自定义格式的工具调用
        
        Args:
            custom_tool_calls: 自定义工具调用列表
            stream_callback: 流式回调函数
            
        Returns:
            工具执行结果列表
        """
        if not custom_tool_calls:
            return []
        
        print(f"🔧 解析到 {len(custom_tool_calls)} 个自定义工具调用")
        
        # 并行执行自定义格式的工具调用
        tasks = []
        for i, tool_call_data in enumerate(custom_tool_calls):
            tool_name = tool_call_data.get("name")
            arguments = tool_call_data.get("arguments", {})
            call_id = f"custom_call_{i}"
            
            print(f"🔧 处理自定义工具调用: {tool_name}")
            
            # 验证工具参数
            validation = validate_tool_arguments(tool_name, arguments)
            if not validation["valid"]:
                print(f"⚠️ {ErrorMessages.TOOL_VALIDATION_FAILED}: {validation['errors']}")
                continue
            

            
            # 创建异步任务
            if stream_callback:
                task = self._execute_single_tool_with_stream_feedback(
                    call_id, tool_name, arguments, stream_callback
                )
            else:
                task = self._execute_single_tool(call_id, tool_name, arguments)
            tasks.append(task)
        
        print(f"🔧 创建了 {len(tasks)} 个自定义工具执行任务")
        
        # 等待所有工具执行完成
        if tasks:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            return self._process_tool_results(tool_results)
        
        return []
    
    async def _execute_single_tool(
        self, 
        call_id: str, 
        tool_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行单个工具调用
        
        Args:
            call_id: 调用ID
            tool_name: 工具名称
            arguments: 工具参数
            
        Returns:
            工具执行结果
        """
        try:

            start_time = time.time()
            
            tool_result = await execute_agent_tool(tool_name, arguments)
            execution_time = time.time() - start_time
            
            # 更新统计信息
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            if tool_result.get("success", False):
                self.execution_stats["successful_executions"] += 1
            else:
                self.execution_stats["failed_executions"] += 1
            
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": tool_result,
                "call_id": call_id,
                "success": tool_result.get("success", False),
                "execution_time": execution_time
            }
            
        except Exception as e:
            print(f"❌ 工具 {tool_name} 执行失败: {e}")
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": {"success": False, "error": str(e)},
                "call_id": call_id,
                "success": False,
                "execution_time": 0
            }
    
    async def _execute_single_tool_with_stream_feedback(
        self,
        call_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        stream_callback: Callable
    ) -> Dict[str, Any]:
        """
        执行单个工具调用并提供流式反馈
        
        Args:
            call_id: 调用ID
            tool_name: 工具名称
            arguments: 工具参数
            stream_callback: 流式回调函数
            
        Returns:
            工具执行结果
        """
        try:
            
            # 记录开始时间
            start_time = time.time()
            
            # 执行工具
            tool_result = await execute_agent_tool(tool_name, arguments)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            # 更新统计信息
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            if tool_result.get("success"):
                self.execution_stats["successful_executions"] += 1
            else:
                self.execution_stats["failed_executions"] += 1
            
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": tool_result,
                "call_id": call_id,
                "success": tool_result.get("success", False),
                "execution_time": execution_time
            }
            
        except Exception as e:
            
            self.execution_stats["total_executions"] += 1
            self.execution_stats["failed_executions"] += 1
            
            return {
                "tool_name": tool_name,
                "arguments": arguments,
                "result": {"success": False, "error": str(e)},
                "call_id": call_id,
                "success": False,
                "execution_time": 0
            }
    
    def _process_tool_results(self, tool_results: List[Any]) -> List[Dict[str, Any]]:
        """
        处理工具执行结果，过滤异常
        
        Args:
            tool_results: 原始工具结果列表
            
        Returns:
            处理后的工具结果列表
        """
        processed_results = []
        for result in tool_results:
            if isinstance(result, Exception):
                print(f"❌ 工具执行异常: {result}")
                processed_results.append({
                    "tool_name": "unknown",
                    "arguments": {},
                    "result": {"success": False, "error": str(result)},
                    "call_id": "error",
                    "success": False
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _summarize_tool_arguments(self, arguments: Dict[str, Any]) -> str:
        """
        生成工具参数的简化摘要
        
        Args:
            arguments: 工具参数
            
        Returns:
            参数摘要字符串
        """
        try:
            summary_parts = []
            for key, value in arguments.items():
                if isinstance(value, str) and len(value) > DefaultValues.TOOL_ARGUMENT_MAX_LENGTH:
                    summary_parts.append(f"{key}='{value[:DefaultValues.TOOL_ARGUMENT_MAX_LENGTH]}...'")
                elif isinstance(value, list) and len(value) > 3:
                    summary_parts.append(f"{key}=[{len(value)} items]")
                elif isinstance(value, dict) and len(value) > 3:
                    summary_parts.append(f"{key}={{{len(value)} keys}}")
                else:
                    summary_parts.append(f"{key}={value}")
            
            return ", ".join(summary_parts[:DefaultValues.MAX_TOOL_ARGUMENT_DISPLAY])
        except:
            return "..."
    
    def _summarize_tool_result(self, result: Dict[str, Any]) -> str:
        """
        生成工具结果的简化摘要
        
        Args:
            result: 工具结果
            
        Returns:
            结果摘要字符串
        """
        try:
            if not result:
                return ""
            
            # 根据不同工具类型生成不同的摘要
            if "tool_name" in result:
                tool_name = result["tool_name"]
                if tool_name == "requirements_analysis":
                    return "需求分析完成"
                elif tool_name == "short_planning":
                    return "短期规划生成"
                elif tool_name == "research":
                    keywords_count = result.get("keywords_processed", 0)
                    return f"技术调研完成 ({keywords_count} 个关键词)"
                elif tool_name == "architecture_design":
                    return "架构设计完成"
            
            # 通用摘要
            if isinstance(result, dict) and len(result) > 0:
                return f"包含 {len(result)} 个字段的结果"
            
            return "执行完成"
        except:
            return ""
    
    def parse_custom_tool_calls(self, content: str) -> List[Dict[str, Any]]:
        """
        解析自定义格式的工具调用
        
        Args:
            content: 包含工具调用的内容
            
        Returns:
            解析出的工具调用列表
        """
        import re
        
        # 查找 <tool_call>[...]</tool_call> 格式
        matches = re.findall(ToolCallPatterns.CUSTOM_TOOL_CALL_PATTERN, content, re.DOTALL)
        
        tool_calls = []
        for match in matches:
            try:
                # 解析JSON数组
                tools_data = json.loads(f'[{match}]')
                tool_calls.extend(tools_data)
            except json.JSONDecodeError as e:
                print(f"❌ 解析自定义工具调用失败: {e}")
                continue
        
        return tool_calls
    
    def clean_tool_call_markers(self, content: str) -> str:
        """
        清理内容中的工具调用标记

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        import re

        # 移除 <tool_call>[...]</tool_call> 标记
        cleaned = re.sub(ToolCallPatterns.CUSTOM_TOOL_CALL_PATTERN, '', content, flags=re.DOTALL)

        # 清理多余的空白
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned).strip()

        # 如果清理后为空，提供默认消息
        if not cleaned:
            cleaned = "我正在为您执行相关的工具调用，请稍等..."

        return cleaned

    def get_execution_stats(self) -> Dict[str, Any]:
        """
        获取执行统计信息

        Returns:
            统计信息字典
        """
        return self.execution_stats.copy()

    def reset_execution_stats(self) -> None:
        """重置执行统计信息"""
        self.execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }
