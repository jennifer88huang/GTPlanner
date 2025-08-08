#!/usr/bin/env python3
"""
GTPlanner CLI

基于Function Calling架构的现代化GTPlanner命令行界面：
1. 原生OpenAI Function Calling支持
2. 实时流式输出显示
3. 完整的会话管理功能
4. 简洁高效的用户体验

使用方式:
    python cli/gtplanner_cli.py                    # 启动交互式CLI
    python cli/gtplanner_cli.py "设计用户管理系统"   # 直接处理需求
    python cli/gtplanner_cli.py --verbose "需求"    # 详细模式
    python cli/gtplanner_cli.py --load <session_id> # 加载指定会话
"""

import sys
import os
import asyncio
import argparse
import time
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.markdown import Markdown
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich.align import Align
from rich.box import ROUNDED
from rich.style import Style

from agent.flows.react_orchestrator_refactored.react_orchestrator_refactored import ReActOrchestratorRefactored
from cli.session_manager import SessionManager


class GTPlannerCLI:
    """基于Function Calling的现代化GTPlanner CLI"""

    def __init__(self, verbose: bool = False):
        """初始化CLI"""
        self.console = Console()
        self.orchestrator = ReActOrchestratorRefactored()
        self.verbose = verbose
        self.running = True
        self.is_first_interaction = True  # 跟踪是否是第一次交互

        # 会话管理器
        self.session_manager = SessionManager()

        # 当前会话状态（从会话管理器获取）
        self.session_state = {
            "dialogue_history": {"messages": []},
            "current_stage": "initialization"
        }

    def show_welcome(self):
        """显示欢迎信息"""
        welcome_text = """
# 🚀 GTPlanner CLI

欢迎使用基于Function Calling的现代化智能规划助手！

## ✨ 主要特性
- 🔧 **Function Calling**: 原生OpenAI Function Calling支持
- 💬 **智能对话**: 自然语言交互，智能工具调用
- 🤖 **专业工具**: 需求分析、研究、架构设计等专业工具
- 📊 **实时反馈**: 流式显示处理过程和工具执行状态
- 🎯 **简洁高效**: 无历史包袱，专为Function Calling优化

## 🎯 使用方法
直接输入您的需求，我将通过Function Calling为您提供智能规划服务。

输入 `/help` 查看所有可用命令，输入 `/quit` 退出。
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="[bold blue]🚀 GTPlanner CLI[/bold blue]",
            border_style="blue",
            box=ROUNDED
        ))

    def show_help(self):
        """显示帮助信息"""
        help_text = """
## 📚 可用命令

- `/help` - 显示帮助信息
- `/quit` - 退出CLI
- `/new` - 创建新会话
- `/sessions` - 列出所有会话
- `/load <id>` - 加载指定会话
- `/delete <id>` - 删除指定会话
- `/tools` - 显示可用工具
- `/stats` - 显示性能统计
- `/verbose` - 切换详细模式

## 🎯 使用示例

- "我想开发一个电商网站"
- "帮我分析在线教育平台的需求"
- "设计一个微服务架构"
- "进行React vs Vue的技术调研"
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="帮助信息",
            border_style="green"
        ))

    async def process_user_input(self, user_input: str) -> bool:
        """
        处理用户输入
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            是否继续运行
        """
        # 处理命令
        if user_input.startswith('/'):
            return self._handle_command(user_input)
        
        # 如果没有当前会话，创建新会话
        if not self.session_manager.current_session_id:
            session_id = self.session_manager.create_new_session()
            self.console.print(f"🆕 [green]创建新会话:[/green] {session_id}")
            # 更新会话状态
            self.session_state = self.session_manager.get_session_data()

        
        # 添加用户消息到会话管理器
        self.session_manager.add_user_message(user_input)

        # 同步会话状态
        self.session_state = self.session_manager.get_session_data()

        # 不再显示处理状态框，直接开始处理
        
        try:
            # 创建流式回调
            stream_callback = self._create_stream_callback()
            
            # 设置流式回调
            self.session_state["_stream_callback"] = stream_callback
            
            # 执行Function Calling流程
            # 1. 准备阶段
            prep_result = await self.orchestrator.prep_async(self.session_state)
            if "error" in prep_result:
                self.console.print(f"❌ [bold red]准备失败:[/bold red] {prep_result['error']}")
                return True
            
            # 2. 执行阶段
            exec_result = await self.orchestrator.exec_async(prep_result)
            if "error" in exec_result:
                self.console.print(f"❌ [bold red]执行失败:[/bold red] {exec_result['error']}")
                return True
            
            # 3. 后处理阶段
            next_route = await self.orchestrator.post_async(
                self.session_state, prep_result, exec_result
            )

            # 🔧 关键修复：同步工具执行历史和结果数据到会话管理器
            if 'tool_execution_history' in self.session_state:
                print(f"🔍 [DEBUG] 同步工具执行历史到会话管理器，历史记录数: {len(self.session_state['tool_execution_history'])}")
                self.session_manager.sync_tool_execution_history(self.session_state['tool_execution_history'])

            # 🔧 新增：同步工具结果数据
            print(f"🔍 [DEBUG] 同步工具结果数据到会话管理器")
            self.session_manager.sync_tool_result_data(self.session_state)

            # 显示结果并保存到会话
            user_message = exec_result.get("user_message", "")
            tool_calls = exec_result.get("tool_calls", [])

            print(f"🔍 [DEBUG] CLI收到exec_result键: {list(exec_result.keys())}")
            print(f"🔍 [DEBUG] CLI收到tool_calls数量: {len(tool_calls)}")
            if tool_calls:
                print(f"🔍 [DEBUG] CLI第一个tool_call: {tool_calls[0]}")

            if user_message:
                # 停止Live显示
                if hasattr(stream_callback, 'stop_live_display'):
                    stream_callback.stop_live_display()

                # 添加AI回复到会话管理器
                self.session_manager.add_assistant_message(user_message, tool_calls)

                # 同步会话状态
                self.session_state = self.session_manager.get_session_data()

            # 不再显示完成状态框

            # 添加一个空行，让界面更清晰
            self.console.print()

            # 保存会话
            self.session_manager.save_current_session()

            return True
            
        except Exception as e:
            self.console.print(f"❌ [bold red]处理异常:[/bold red] {str(e)}")
            return True

    def _handle_command(self, command: str) -> bool:
        """
        处理命令

        Args:
            command: 命令字符串

        Returns:
            是否继续运行
        """
        parts = command.lower().strip().split()
        cmd = parts[0] if parts else ""

        if cmd == '/help':
            self.show_help()
        elif cmd == '/quit':
            self.console.print("👋 [bold blue]再见！[/bold blue]")
            return False
        elif cmd == '/new':
            self._create_new_session()
        elif cmd == '/sessions':
            self._list_sessions()
        elif cmd == '/load':
            if len(parts) > 1:
                self._load_session(parts[1])
            else:
                self.console.print("❓ [yellow]请指定会话ID:[/yellow] /load <session_id>")
        elif cmd == '/delete':
            if len(parts) > 1:
                self._delete_session(parts[1])
            else:
                self.console.print("❓ [yellow]请指定会话ID:[/yellow] /delete <session_id>")
        elif cmd == '/tools':
            self._show_available_tools()
        elif cmd == '/stats':
            self._show_stats()
        elif cmd == '/verbose':
            self.verbose = not self.verbose
            mode = "详细" if self.verbose else "简洁"
            self.console.print(f"🔧 [blue]已切换到{mode}模式[/blue]")
        else:
            self.console.print(f"❓ [yellow]未知命令:[/yellow] {command}")
            self.console.print("输入 `/help` 查看可用命令")

        return True

    def _create_stream_callback(self):
        """创建美化的流式回调函数"""

        # 状态跟踪
        in_final_response = False
        has_tool_calls = False
        ai_response_started = False
        current_tool = None
        tool_start_time = None
        ai_content_buffer = ""  # 收集AI回复内容
        live_display = None  # Live显示对象

        async def stream_callback(content: str):
            """美化的流式回调函数"""
            nonlocal in_final_response, has_tool_calls, ai_response_started, current_tool, tool_start_time, ai_content_buffer, live_display

            if not content.strip():
                return

            # 过滤掉不需要的信息
            if any(skip in content for skip in [
                "🔧 准备调用OpenAI API",
                "🤔 正在分析您的请求",
                "工具数量:",
                "准备调用OpenAI API"
            ]):
                return

            # 检测工具调用开始
            if "🔧 开始执行" in content:
                has_tool_calls = True
                # 提取工具名称
                parts = content.split("🔧 开始执行")
                if len(parts) > 1:
                    current_tool = parts[1].strip()
                    tool_start_time = time.time()

                    # 显示美化的工具执行状态
                    tool_panel = Panel(
                        Text(f"🔧 正在执行工具: {current_tool}", style="bold yellow"),
                        border_style="yellow",
                        box=ROUNDED
                    )
                    self.console.print(tool_panel)
                return

            # 检测工具执行完成
            if "✅" in content and ("执行成功" in content or "执行完成" in content) and current_tool:
                # 计算执行时间
                if tool_start_time:
                    execution_time = time.time() - tool_start_time
                    success_text = Text()
                    success_text.append("✅ ", style="bold green")
                    success_text.append(f"工具 {current_tool} 执行完成", style="green")
                    success_text.append(f" ({execution_time:.1f}s)", style="dim")

                    success_panel = Panel(
                        Align.center(success_text),
                        border_style="green",
                        box=ROUNDED
                    )
                    self.console.print(success_panel)
                current_tool = None
                tool_start_time = None
                return

            # 检测最终响应开始
            if "📝" in content:
                in_final_response = True
                ai_content_buffer = ""  # 重置缓冲区
                return

            # 在详细模式下显示所有流式内容
            if self.verbose:
                if in_final_response:
                    ai_content_buffer += content
                else:
                    self.console.print(content, end="")
            else:
                # 在简洁模式下的处理
                if in_final_response:
                    # 如果是第一次进入AI回复阶段，创建Live显示
                    if not ai_response_started:
                        ai_response_started = True
                        ai_content_buffer = ""

                        # 创建初始面板
                        initial_panel = Panel(
                            Text("🤖 正在回复...", style="dim"),
                            title="[bold cyan]🤖 AI 回复[/bold cyan]",
                            border_style="cyan",
                            box=ROUNDED,
                            padding=(0, 1)
                        )

                        # 启动Live显示
                        live_display = Live(
                            initial_panel,
                            console=self.console,
                            refresh_per_second=10,
                            transient=False
                        )
                        live_display.start()

                    # 更新AI回复内容
                    ai_content_buffer += content

                    # 动态更新Live显示
                    if live_display:
                        updated_panel = Panel(
                            Text(ai_content_buffer, style="white"),
                            title="[bold cyan]🤖 AI 回复[/bold cyan]",
                            border_style="cyan",
                            box=ROUNDED,
                            padding=(0, 1)
                        )
                        live_display.update(updated_panel)
                elif any(marker in content for marker in ["🔄", "💭"]):
                    # 显示处理状态（简化显示）
                    if "🔄" in content:
                        self.console.print("🔄 [dim]处理中...[/dim]")
                    elif "💭" in content:
                        self.console.print("💭 [dim]整理结果...[/dim]")
                elif not has_tool_calls and not ai_response_started:
                    # 如果没有工具调用，开始Live显示AI回复
                    ai_response_started = True
                    ai_content_buffer = content

                    # 创建初始面板
                    initial_panel = Panel(
                        Text(content, style="white"),
                        title="[bold cyan]🤖 AI 回复[/bold cyan]",
                        border_style="cyan",
                        box=ROUNDED,
                        padding=(0, 1)
                    )

                    # 启动Live显示
                    live_display = Live(
                        initial_panel,
                        console=self.console,
                        refresh_per_second=10,
                        transient=False
                    )
                    live_display.start()
                elif not has_tool_calls and ai_response_started:
                    # 继续更新AI回复内容
                    ai_content_buffer += content

                    # 动态更新Live显示
                    if live_display:
                        updated_panel = Panel(
                            Text(ai_content_buffer, style="white"),
                            title="[bold cyan]🤖 AI 回复[/bold cyan]",
                            border_style="cyan",
                            box=ROUNDED,
                            padding=(0, 1)
                        )
                        live_display.update(updated_panel)

        # 返回回调函数和相关方法
        def get_ai_content():
            return ai_content_buffer

        def stop_live_display():
            nonlocal live_display
            if live_display:
                live_display.stop()
                live_display = None

        stream_callback.get_ai_content = get_ai_content
        stream_callback.stop_live_display = stop_live_display
        return stream_callback

    def _get_user_input(self) -> str:
        """获取用户输入，只在第一次交互时显示美化的输入框"""
        # 只在第一次交互时显示输入提示面板
        if self.is_first_interaction:
            input_panel = Panel(
                Text("💭 请输入您的需求或命令 (输入 /help 查看帮助)", style="dim"),
                title="[bold cyan]✨ GTPlanner Assistant[/bold cyan]",
                border_style="cyan",
                box=ROUNDED,
                padding=(0, 1)
            )

            self.console.print()
            self.console.print(input_panel)
            self.is_first_interaction = False  # 标记已经不是第一次交互了

        # 使用标准input()替代Rich的Prompt.ask()来避免readline冲突
        # 先打印提示符
        self.console.print("[bold green]🎯[/bold green] ", end="")

        # 使用标准input获取输入
        try:
            user_input = input().strip()
            return user_input
        except (EOFError, KeyboardInterrupt):
            # 处理Ctrl+C或Ctrl+D
            return ""

    def _show_processing_status(self, message: str):
        """显示处理状态，使用动态效果"""
        status_text = Text()
        status_text.append("🤖 ", style="bold blue")
        status_text.append(message, style="blue")

        panel = Panel(
            Align.center(status_text),
            border_style="blue",
            box=ROUNDED,
            padding=(0, 2)
        )

        self.console.print(panel)

    def _show_tool_execution(self, tool_name: str, start_time: float):
        """显示工具执行状态，带有动态加载效果"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]🔧 执行工具:[/bold blue]"),
            TextColumn(f"[bold green]{tool_name}[/bold green]"),
            TimeElapsedColumn(),
            console=self.console,
            transient=True
        ) as progress:
            task = progress.add_task("", total=None)

            # 这里可以添加实际的工具执行逻辑
            # 现在只是为了演示效果
            import time
            while True:
                time.sleep(0.1)
                # 检查工具是否完成（这里需要实际的完成检查逻辑）
                if time.time() - start_time > 1:  # 临时的完成条件
                    break

    def _show_completion_status(self, tool_calls: list):
        """显示美化的完成状态"""
        if tool_calls:
            successful_tools = [tc for tc in tool_calls if tc.get("success", False)]
            failed_tools = [tc for tc in tool_calls if not tc.get("success", False)]

            # 创建完成状态文本
            status_text = Text()
            status_text.append("🎉 ", style="bold green")
            status_text.append("处理完成", style="bold green")

            if failed_tools:
                status_text.append(f" ({len(successful_tools)}/{len(tool_calls)} 工具成功)", style="yellow")
            else:
                status_text.append(f" (执行了 {len(successful_tools)} 个工具)", style="green")

            completion_panel = Panel(
                Align.center(status_text),
                border_style="green",
                box=ROUNDED,
                padding=(0, 2)
            )
        else:
            # 没有工具调用的简单完成状态
            status_text = Text()
            status_text.append("✨ ", style="bold cyan")
            status_text.append("回复完成", style="bold cyan")

            completion_panel = Panel(
                Align.center(status_text),
                border_style="cyan",
                box=ROUNDED,
                padding=(0, 2)
            )

        self.console.print()
        self.console.print(completion_panel)


    def _show_ai_response(self, ai_content: str):
        """显示AI回复，放在框内"""
        ai_panel = Panel(
            Text(ai_content, style="white"),
            title="[bold cyan]🤖 AI 回复[/bold cyan]",
            border_style="cyan",
            box=ROUNDED,
            padding=(0, 1)
        )

        self.console.print()
        self.console.print(ai_panel)

    def _create_new_session(self):
        """创建新会话"""
        session_id = self.session_manager.create_new_session()
        self.session_state = self.session_manager.get_session_data()
        self.console.print(f"🆕 [green]创建新会话:[/green] {session_id}")

    def _list_sessions(self):
        """列出所有会话"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            self.console.print("📝 [yellow]暂无保存的会话[/yellow]")
            return

        table = Table(title="📚 会话列表")
        table.add_column("会话ID", style="bold green")
        table.add_column("标题")
        table.add_column("消息数", justify="center")
        table.add_column("最后更新", style="dim")
        table.add_column("状态", justify="center")

        current_id = self.session_manager.current_session_id

        for session in sessions:
            status = "🟢 当前" if session["session_id"] == current_id else ""

            # 格式化时间
            try:
                from datetime import datetime
                last_updated = datetime.fromisoformat(session["last_updated"])
                time_str = last_updated.strftime("%m-%d %H:%M")
            except:
                time_str = session["last_updated"][:16] if session["last_updated"] else ""

            table.add_row(
                session["session_id"],
                session["title"],
                str(session["message_count"]),
                time_str,
                status
            )

        self.console.print(table)

    def _load_session(self, session_id: str):
        """加载指定会话"""
        if self.session_manager.load_session(session_id):
            self.session_state = self.session_manager.get_session_data()

            # 显示会话信息
            message_count = len(self.session_state.get("dialogue_history", {}).get("messages", []))
            self.console.print(f"📂 [green]已加载会话:[/green] {session_id} ({message_count} 条消息)")

            # 显示最近几条对话
            self._show_recent_messages()
        else:
            self.console.print(f"❌ [red]加载会话失败:[/red] {session_id}")

    def _delete_session(self, session_id: str):
        """删除指定会话"""
        if self.session_manager.delete_session(session_id):
            self.console.print(f"🗑️ [green]已删除会话:[/green] {session_id}")

            # 如果删除的是当前会话，重置状态
            if self.session_manager.current_session_id is None:
                self.session_state = {
                    "dialogue_history": {"messages": []},
                    "current_stage": "initialization"
                }
        else:
            self.console.print(f"❌ [red]删除会话失败:[/red] {session_id}")

    def _show_recent_messages(self, count: int = 3):
        """显示最近的对话消息"""
        messages = self.session_state.get("dialogue_history", {}).get("messages", [])

        if not messages:
            return

        recent_messages = messages[-count:] if len(messages) > count else messages

        self.console.print(f"\n💬 [dim]最近 {len(recent_messages)} 条对话:[/dim]")

        for msg in recent_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "user":
                # 截取用户消息
                preview = content[:50] + "..." if len(content) > 50 else content
                self.console.print(f"  👤 [blue]{preview}[/blue]")
            elif role == "assistant":
                # 截取AI回复
                preview = content[:50] + "..." if len(content) > 50 else content
                self.console.print(f"  🤖 [cyan]{preview}[/cyan]")

        self.console.print("")

    def _show_available_tools(self):
        """显示可用工具列表"""
        tools_info = """
## 🔧 可用工具

### 📋 需求分析工具 (requirements_analysis)
- **功能**: 分析用户需求并生成结构化需求文档
- **适用场景**: 项目初期需求梳理、功能规划
- **输出**: 详细的需求分析报告

### 📅 短期规划工具 (short_planning)
- **功能**: 基于需求分析生成项目短期规划
- **适用场景**: 制定开发计划、里程碑规划
- **输出**: 分阶段的项目执行计划

### 🔍 技术调研工具 (research)
- **功能**: 进行技术调研和解决方案研究
- **适用场景**: 技术选型、方案对比、最佳实践研究
- **输出**: 详细的技术调研报告

### 🏗️ 架构设计工具 (architecture_design)
- **功能**: 生成详细的系统架构设计方案
- **适用场景**: 系统设计、技术架构规划
- **输出**: 完整的架构设计文档

### 💡 使用建议
- 可以在一次对话中同时调用多个工具
- 工具会根据需求自动选择和组合
- 支持迭代优化和深度分析
        """

        self.console.print(Panel(
            Markdown(tools_info),
            title="[bold green]🔧 GTPlanner 工具箱[/bold green]",
            border_style="green",
            box=ROUNDED
        ))

    def _show_stats(self):
        """显示性能统计"""
        stats = self.orchestrator.get_performance_stats()
        session_stats = self.session_manager.get_session_stats()

        stats_text = f"""
## 📊 性能统计

**请求统计:**
- 总请求数: {stats.get('total_requests', 0)}
- 成功请求: {stats.get('successful_requests', 0)}
- 失败请求: {stats.get('failed_requests', 0)}
- 成功率: {stats.get('successful_requests', 0) / max(stats.get('total_requests', 1), 1) * 100:.1f}%

**性能指标:**
- 平均响应时间: {stats.get('average_response_time', 0):.2f}s
- 工具调用总数: {stats.get('total_tool_calls', 0)}

**会话统计:**
- 总会话数: {session_stats.get('total_sessions', 0)}
- 当前会话ID: {session_stats.get('current_session_id', '无')}
- 当前对话消息数: {session_stats.get('current_message_count', 0)}
- 会话存储目录: {session_stats.get('sessions_dir', '')}
        """

        self.console.print(Panel(
            Markdown(stats_text),
            title="性能统计",
            border_style="yellow"
        ))

    async def run_interactive(self):
        """运行交互式CLI"""
        self.show_welcome()
        
        while self.running:
            try:
                # 获取美化的用户输入
                user_input = self._get_user_input()

                if not user_input:
                    continue

                # 处理用户输入
                should_continue = await self.process_user_input(user_input)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                if Confirm.ask("\n🤔 确定要退出吗？"):
                    break
                else:
                    self.console.print("继续运行...")
            except EOFError:
                break

    async def run_single_command(self, command: str):
        """运行单个命令"""
        self.console.print(f"🚀 [bold blue]直接处理需求:[/bold blue] {command}")
        await self.process_user_input(command)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GTPlanner CLI")
    parser.add_argument("requirement", nargs="?", help="直接处理的需求")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--load", help="加载指定会话ID")

    args = parser.parse_args()

    # 创建CLI实例
    cli = GTPlannerCLI(verbose=args.verbose)

    # 如果指定了加载会话
    if args.load:
        if cli.session_manager.load_session(args.load):
            cli.session_state = cli.session_manager.get_session_data()
            cli.console.print(f"📂 [green]已加载会话:[/green] {args.load}")
        else:
            cli.console.print(f"❌ [red]加载会话失败:[/red] {args.load}")
            return 1

    try:
        if args.requirement:
            # 直接处理需求
            await cli.run_single_command(args.requirement)
        else:
            # 交互式模式
            await cli.run_interactive()
    except Exception as e:
        console = Console()
        console.print(f"❌ [bold red]CLI运行异常:[/bold red] {str(e)}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
