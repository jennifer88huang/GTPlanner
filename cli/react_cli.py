#!/usr/bin/env python3
"""
GTPlanner ReAct CLI

基于ReAct模式的新一代CLI界面：
1. 支持上下文对话的会话管理
2. 实时显示ReAct循环过程
3. 集成所有专业Agent
4. 提供丰富的交互命令
5. 流式输出和美观的UI

使用方式:
    python cli/react_cli.py                    # 启动交互式CLI
    python cli/react_cli.py "设计用户管理系统"   # 直接处理需求
    python cli/react_cli.py --load session_id  # 加载指定会话
"""

import sys
import os
import asyncio
import argparse
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown

from cli.session_manager import SessionManager
from cli.streaming_react_display import StreamingReActDisplay
from cli.real_time_streaming_display import RealTimeStreamingDisplay
from agent.gtplanner import GTPlanner
from agent.flows.orchestrator_react_flow import OrchestratorReActFlow
from utils.json_stream_parser import JSONStreamParser


class ReActCLI:
    """基于ReAct模式的GTPlanner CLI"""

    def __init__(self, verbose: bool = False):
        """初始化CLI"""
        self.console = Console()
        self.session_manager = SessionManager()
        self.display = StreamingReActDisplay(self.console)
        self.real_time_display = RealTimeStreamingDisplay(self.console)
        self.gtplanner = GTPlanner()
        self.orchestrator = OrchestratorReActFlow()

        # 流式解析器
        self.stream_parser = None

        # CLI状态
        self.running = True
        self.current_session_id = None
        self.verbose = verbose  # 控制是否显示详细信息

    def show_welcome(self):
        """显示欢迎信息"""
        welcome_text = """
# 🚀 GTPlanner ReAct CLI

欢迎使用基于ReAct模式的智能规划助手！

## ✨ 主要特性
- 🧠 **智能ReAct循环**: 思考-行动-观察的完整闭环
- 💬 **上下文对话**: 支持多轮对话和会话管理
- 🤖 **专业Agent**: 集成需求分析、研究、架构设计等专业Agent
- 📊 **实时显示**: 流式显示处理过程和Agent状态
- 💾 **会话管理**: 自动保存和恢复对话历史

## 🎯 使用方法
直接输入您的需求，我将通过ReAct模式为您提供智能规划服务。

输入 `/help` 查看所有可用命令。
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="GTPlanner ReAct CLI",
            border_style="blue"
        ))

    def show_help(self):
        """显示帮助信息"""
        help_table = Table(title="📚 可用命令")
        help_table.add_column("命令", style="bold green")
        help_table.add_column("描述")
        help_table.add_column("示例")
        
        commands = [
            ("/help", "显示帮助信息", "/help"),
            ("/new", "创建新会话", "/new"),
            ("/sessions", "列出所有会话", "/sessions"),
            ("/load <id>", "加载指定会话", "/load abc123"),
            ("/save", "保存当前会话", "/save"),
            ("/export <path>", "导出会话", "/export session.json"),
            ("/import <path>", "导入会话", "/import session.json"),
            ("/status", "显示当前状态", "/status"),
            ("/history", "显示对话历史", "/history"),
            ("/clear", "清屏", "/clear"),
            ("/stats", "显示会话统计", "/stats"),
            ("/delete <id>", "删除指定会话", "/delete abc123"),
            ("/quit", "退出程序", "/quit"),
            ("直接输入", "处理需求", "设计一个用户管理系统")
        ]
        
        for cmd, desc, example in commands:
            help_table.add_row(cmd, desc, example)
        
        self.console.print(help_table)

    def show_sessions(self):
        """显示所有会话"""
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            self.console.print("📭 暂无保存的会话")
            return
        
        sessions_table = Table(title="💾 会话列表")
        sessions_table.add_column("ID", style="bold")
        sessions_table.add_column("标题")
        sessions_table.add_column("消息数")
        sessions_table.add_column("ReAct循环")
        sessions_table.add_column("最后更新")
        sessions_table.add_column("状态")
        
        for session in sessions:
            # 标记当前会话
            current_marker = "👉 " if session["session_id"] == self.current_session_id else ""
            
            sessions_table.add_row(
                current_marker + session["session_id"],
                session["title"][:30] + ("..." if len(session["title"]) > 30 else ""),
                str(session["message_count"]),
                str(session["react_cycles"]),
                session["last_updated"][:16],  # 只显示日期和时间
                session["current_stage"]
            )
        
        self.console.print(sessions_table)

    def show_status(self):
        """显示当前状态"""
        if self.current_session_id:
            session_info = self.session_manager.get_current_session_info()
            if session_info:
                self.display.display_session_status(session_info)
            else:
                self.console.print("❌ 无法获取当前会话信息")
        else:
            self.console.print("📭 当前没有活跃会话")
        
        # 显示GTPlanner状态
        planner_state = self.gtplanner.get_state()
        self.console.print(f"\n🤖 GTPlanner状态: {planner_state['current_stage']}")

    def show_history(self):
        """显示对话历史"""
        if not self.current_session_id:
            self.console.print("📭 当前没有活跃会话")
            return
        
        history = self.session_manager.get_conversation_history()
        
        if not history:
            self.console.print("📭 当前会话暂无对话历史")
            return
        
        self.console.print(Panel("💬 对话历史", style="bold blue"))
        
        for i, message in enumerate(history, 1):
            role = message.get("role", "unknown")
            content = message.get("content", "")
            timestamp = message.get("timestamp", "")
            
            role_icon = "👤" if role == "user" else "🤖"
            role_style = "bold blue" if role == "user" else "bold green"
            
            self.console.print(f"\n{role_icon} **{role.title()}** ({timestamp[:16]})", style=role_style)
            self.console.print(content[:200] + ("..." if len(content) > 200 else ""))

    def show_stats(self):
        """显示会话统计信息"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            self.console.print("📭 暂无会话数据")
            return

        # 计算统计信息
        total_sessions = len(sessions)
        total_messages = sum(s["message_count"] for s in sessions)
        total_react_cycles = sum(s["react_cycles"] for s in sessions)

        # 按阶段统计
        stage_counts = {}
        for session in sessions:
            stage = session["current_stage"]
            stage_counts[stage] = stage_counts.get(stage, 0) + 1

        # 创建统计表格
        stats_table = Table(title="📊 会话统计")
        stats_table.add_column("指标", style="bold")
        stats_table.add_column("数值")

        stats_table.add_row("总会话数", str(total_sessions))
        stats_table.add_row("总消息数", str(total_messages))
        stats_table.add_row("总ReAct循环", str(total_react_cycles))
        stats_table.add_row("平均消息/会话", f"{total_messages/total_sessions:.1f}" if total_sessions > 0 else "0")
        stats_table.add_row("平均循环/会话", f"{total_react_cycles/total_sessions:.1f}" if total_sessions > 0 else "0")

        self.console.print(stats_table)

        # 显示阶段分布
        if stage_counts:
            stage_table = Table(title="📈 处理阶段分布")
            stage_table.add_column("阶段", style="bold")
            stage_table.add_column("会话数")
            stage_table.add_column("占比")

            for stage, count in sorted(stage_counts.items()):
                percentage = (count / total_sessions) * 100
                stage_table.add_row(stage, str(count), f"{percentage:.1f}%")

            self.console.print(stage_table)

    async def process_user_input(self, user_input: str):
        """
        处理用户输入，使用流式ReAct模式

        Args:
            user_input: 用户输入内容
        """
        # 移除调试输出以获得更好的用户体验
        # print(f"DEBUG: 开始处理用户输入: {user_input}")

        if not self.current_session_id:
            # 如果没有当前会话，创建新会话
            self.current_session_id = self.session_manager.create_new_session()
            self.console.print(f"🆕 创建新会话: {self.current_session_id}")

        # 添加用户消息到会话
        self.session_manager.add_user_message(user_input)
        # print(f"DEBUG: 已添加用户消息到会话")

        # 根据verbose设置决定是否显示详细的流式会话
        if self.verbose:
            self.real_time_display.start_streaming_session(f"处理需求: {user_input[:30]}...")
        else:
            # 简化模式：只显示基本的处理提示
            self.console.print(f"🤔 正在思考: {user_input[:50]}{'...' if len(user_input) > 50 else ''}", style="bold blue")

        try:
            # 获取当前共享状态
            shared_state = self.session_manager.current_shared_state
            # print(f"DEBUG: 获取共享状态成功，数据键: {list(shared_state.data.keys())}")

            # 根据verbose设置创建流式回调
            if self.verbose:
                stream_callback = self._create_real_time_stream_callback()
            else:
                # 非verbose模式：使用简化的流式回调，只显示重要信息
                stream_callback = self._create_simple_stream_callback()
            # print(f"DEBUG: 创建真正的流式回调成功")

            # 异步运行ReAct主控制器，支持流式显示
            # print(f"DEBUG: 开始调用orchestrator.run_async")
            result = await self.orchestrator.run_async(shared_state.data, stream_callback)
            # print(f"DEBUG: orchestrator.run_async 调用完成，结果: {result}")

            # 显示最终结果
            success = self._display_final_result(result)
            # print(f"DEBUG: 已显示最终结果")

            # 保存会话
            self.session_manager.save_current_session()
            # print(f"DEBUG: 已保存会话")

            return success  # 返回处理是否成功

        except Exception as e:
            # 详细的错误处理
            import traceback
            error_msg = f"处理过程中发生错误: {str(e)}"
            error_type = type(e).__name__

            # 移除调试输出以获得更好的用户体验
            # print(f"DEBUG: 错误类型: {error_type}")
            # print(f"DEBUG: 错误信息: {str(e)}")
            # print(f"DEBUG: 错误堆栈:")
            # traceback.print_exc()

            # 尝试从会话中恢复部分信息
            try:
                session_info = self.session_manager.get_current_session_info()
                if session_info.get("message_count", 0) > 0:
                    error_msg += f"\n会话信息: {session_info['message_count']} 条消息"
            except:
                pass

            self.display.display_error(error_msg, f"ReAct执行错误 ({error_type})")

            # 记录错误到会话
            try:
                self.session_manager.add_assistant_message(f"❌ 处理失败: {str(e)}")
                self.session_manager.save_current_session()
            except:
                pass

        finally:
            if self.verbose:
                # 在verbose模式下，由real_time_display处理结束显示
                success = locals().get('success', False)
                self.real_time_display.end_streaming_session({"success": success, "react_cycles": shared_state.data.get("react_cycle_count", 0)})
            # 在非verbose模式下，不显示额外的完成提示，因为_display_final_result已经处理了

    def _create_real_time_stream_callback(self):
        """创建真正的实时流式处理回调函数"""
        # 创建流式解析器，订阅关键字段
        subscribed_fields = [
            "user_message",  # 新增：AI给用户的回复消息
            "thought.current_goal",
            "thought.situation_analysis",
            "thought.reasoning",
            "action_decision.action_type",
            "action_decision.action_rationale",
            "observation.current_progress",
            "observation.next_focus"
        ]

        self.stream_parser = JSONStreamParser(subscribed_fields=subscribed_fields)

        # 为每个字段创建回调
        for field in subscribed_fields:
            callback = self.real_time_display.create_field_callback(field)
            self.stream_parser.subscribe_field(field, callback)

        async def stream_callback(parsed_data: Dict[str, Any], raw_text: str):
            """
            真正的实时流式处理回调函数

            Args:
                parsed_data: 解析出的JSON数据片段（暂时不用）
                raw_text: 原始文本流
            """
            try:
                # 将原始文本添加到流式解析器
                if raw_text:
                    self.stream_parser.add_chunk(raw_text)

            except Exception:
                # 静默处理流式显示错误，不影响主流程
                pass

        return stream_callback

    def _create_simple_stream_callback(self):
        """创建简单的流式处理回调函数（非verbose模式）"""
        displayed_messages = set()  # 跟踪已显示的消息，避免重复
        last_action_type = None  # 跟踪上次显示的行动类型
        displayed_progress = set()  # 跟踪已显示的进度信息，避免重复

        async def simple_callback(parsed_data: Dict[str, Any], raw_text: str):
            """
            简单的流式处理回调函数，显示关键信息
            """
            nonlocal last_action_type  # 声明要修改外层变量

            try:
                # 1. 优先显示user_message（AI的回复）
                if "user_message" in parsed_data and parsed_data["user_message"]:
                    user_message = parsed_data["user_message"].strip()
                    if user_message and user_message not in displayed_messages:
                        # 只显示完整的、未显示过的消息
                        if len(user_message) > 10:  # 降低长度要求
                            displayed_messages.add(user_message)
                            formatted_message = user_message.replace("\\n", "\n")
                            self.console.print(f"\n🤖 {formatted_message}\n", style="cyan")

                # 2. 显示行动类型变化（简化版）
                if "action_decision" in parsed_data and parsed_data["action_decision"]:
                    action_data = parsed_data["action_decision"]
                    if isinstance(action_data, dict) and "action_type" in action_data:
                        action_type = action_data["action_type"]
                        if action_type and action_type != last_action_type:
                            last_action_type = action_type

                            # 显示行动类型的中文描述
                            action_names = {
                                "requirements_analysis": "📋 需求分析",
                                "short_planning": "📝 快速规划",
                                "research": "🔍 技术调研",
                                "architecture_design": "🏗️ 架构设计",
                                "user_interaction": "💬 用户交互",
                                "complete": "✅ 完成",
                                "wait": "⏳ 等待"
                            }
                            action_display = action_names.get(action_type, f"🔄 {action_type}")
                            self.console.print(f"   {action_display}", style="yellow")

                # 3. 显示当前进度（如果有），避免重复
                if "observation" in parsed_data and parsed_data["observation"]:
                    obs_data = parsed_data["observation"]
                    if isinstance(obs_data, dict) and "current_progress" in obs_data:
                        progress = obs_data["current_progress"]
                        if progress and len(progress) > 10 and progress not in displayed_progress:
                            displayed_progress.add(progress)
                            self.console.print(f"   📊 {progress}", style="green")

            except Exception:
                # 静默处理错误
                pass

        return simple_callback

    def _create_stream_callback(self):
        """创建流式处理回调函数（保留兼容性）"""
        async def stream_callback(parsed_data: Dict[str, Any], raw_text: str):
            """
            流式处理回调函数

            Args:
                parsed_data: 解析出的JSON数据片段
                raw_text: 原始文本
            """
            try:
                # 如果解析出了思考阶段数据
                if "thought" in parsed_data and parsed_data["thought"]:
                    self.display.display_thought_phase(parsed_data["thought"])

                # 如果解析出了行动决策数据
                if "action_decision" in parsed_data and parsed_data["action_decision"]:
                    self.display.display_action_phase(parsed_data["action_decision"])

                # 如果解析出了观察阶段数据
                if "observation" in parsed_data and parsed_data["observation"]:
                    self.display.display_observation_phase(parsed_data["observation"])

            except Exception:
                # 静默处理流式显示错误，不影响主流程
                pass

        return stream_callback



    def _display_final_result(self, result: Dict[str, Any]) -> bool:
        """显示最终结果，返回是否成功"""
        flow_result = result.get("flow_result", "")

        # 检查是否是正常的等待用户输入状态
        # flow_result可能是字符串或字典
        if (flow_result == "wait_for_user" or
            (isinstance(flow_result, dict) and flow_result.get("final_action") == "wait_for_user")):
            self.display.display_success(
                f"ReAct循环完成，等待用户输入\n"
                f"已完成 {result.get('react_cycles', 0)} 个ReAct循环",
                "等待用户输入"
            )
            return True

        # 检查是否是其他正常结束状态
        if flow_result in ["goal_achieved", "react_complete", "max_cycles_reached"]:
            completion_status = result.get("completion_status", {})
            completed_count = sum(1 for status in completion_status.values() if status)
            total_count = len(completion_status)

            self.display.display_success(
                f"成功完成 {completed_count}/{total_count} 个处理阶段\n"
                f"ReAct循环次数: {result.get('react_cycles', 0)}\n"
                f"结束原因: {flow_result}",
                "处理完成"
            )

            # 显示具体输出
            if result.get("agent_design_document"):
                self.console.print(Panel(
                    "📄 已生成完整的架构设计文档",
                    title="✨ 输出结果",
                    style="bold green"
                ))
            return True
        else:
            # 这才是真正的错误情况
            error_msg = result.get("error", f"处理异常结束: {flow_result}")
            self.display.display_error(error_msg, "处理失败")
            return False

    def handle_command(self, command: str) -> bool:
        """
        处理命令
        
        Args:
            command: 用户输入的命令
            
        Returns:
            是否继续运行
        """
        command = command.strip()
        
        if command == "/help":
            self.show_help()
        elif command == "/new":
            self.current_session_id = self.session_manager.create_new_session()
            self.console.print(f"🆕 创建新会话: {self.current_session_id}")
        elif command == "/sessions":
            self.show_sessions()
        elif command.startswith("/load "):
            session_id = command[6:].strip()
            if self.session_manager.load_session(session_id):
                self.current_session_id = session_id
                self.console.print(f"✅ 已加载会话: {session_id}")
            else:
                self.console.print(f"❌ 无法加载会话: {session_id}")
        elif command == "/save":
            if self.current_session_id:
                self.session_manager.save_current_session()
                self.console.print("💾 会话已保存")
            else:
                self.console.print("❌ 当前没有活跃会话")
        elif command.startswith("/export "):
            export_path = command[8:].strip()
            if self.current_session_id and self.session_manager.export_session(self.current_session_id, export_path):
                self.console.print(f"📤 会话已导出到: {export_path}")
            else:
                self.console.print("❌ 导出失败")
        elif command.startswith("/import "):
            import_path = command[8:].strip()
            session_id = self.session_manager.import_session(import_path)
            if session_id:
                self.console.print(f"📥 会话已导入，ID: {session_id}")
            else:
                self.console.print("❌ 导入失败")
        elif command == "/status":
            self.show_status()
        elif command == "/history":
            self.show_history()
        elif command == "/stats":
            self.show_stats()
        elif command.startswith("/delete "):
            session_id = command[8:].strip()
            if Confirm.ask(f"确定要删除会话 {session_id} 吗？"):
                if self.session_manager.delete_session(session_id):
                    self.console.print(f"🗑️ 会话 {session_id} 已删除")
                    if self.current_session_id == session_id:
                        self.current_session_id = None
                else:
                    self.console.print(f"❌ 无法删除会话: {session_id}")
        elif command == "/clear":
            self.display.clear_screen()
        elif command in ["/quit", "/exit", "/q"]:
            return False
        else:
            self.console.print(f"❓ 未知命令: {command}")
            self.console.print("输入 /help 查看可用命令")
        
        return True

    async def run_interactive(self):
        """运行交互式CLI"""
        self.show_welcome()
        
        while self.running:
            try:
                # 显示提示符
                session_prompt = f"[{self.current_session_id}] " if self.current_session_id else "[新会话] "
                user_input = Prompt.ask(f"\n{session_prompt}GTPlanner", default="").strip()
                
                if not user_input:
                    continue
                
                # 处理命令
                if user_input.startswith("/"):
                    self.running = self.handle_command(user_input)
                else:
                    # 处理用户需求
                    await self.process_user_input(user_input)
                    
            except KeyboardInterrupt:
                if Confirm.ask("\n🤔 确定要退出吗？"):
                    break
            except Exception as e:
                self.console.print(f"❌ 发生错误: {e}")
        
        self.console.print("👋 再见！")

    async def run_direct(self, requirement: str):
        """直接处理需求"""
        self.console.print(f"🚀 直接处理需求: {requirement}")
        await self.process_user_input(requirement)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GTPlanner ReAct CLI")
    parser.add_argument("requirement", nargs="?", help="直接处理的需求")
    parser.add_argument("--load", help="加载指定会话ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细调试信息")

    args = parser.parse_args()

    cli = ReActCLI(verbose=args.verbose)
    
    # 如果指定了加载会话
    if args.load:
        if cli.session_manager.load_session(args.load):
            cli.current_session_id = args.load
            cli.console.print(f"✅ 已加载会话: {args.load}")
        else:
            cli.console.print(f"❌ 无法加载会话: {args.load}")
            return
    
    # 如果提供了直接需求
    if args.requirement:
        await cli.run_direct(args.requirement)
    else:
        await cli.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
