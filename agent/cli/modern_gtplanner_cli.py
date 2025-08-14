#!/usr/bin/env python3
"""
现代化GTPlanner CLI

基于新的流式响应架构的CLI实现：
1. 集成StreamingSession和CLIStreamHandler
2. 使用StatelessGTPlanner而不是旧的ReActOrchestratorFlow
3. 支持类型安全的流式响应（StreamEventType/StreamCallbackType）
4. 保持会话管理和配置功能
5. 优雅的中断处理和资源清理

使用方式:
    python cli/modern_gtplanner_cli.py                    # 启动交互式CLI
    python cli/modern_gtplanner_cli.py "设计用户管理系统"   # 直接处理需求
    python cli/modern_gtplanner_cli.py --no-streaming     # 禁用流式响应
    python cli/modern_gtplanner_cli.py --load <session_id> # 加载指定会话
"""

import sys
import asyncio
import argparse
import signal
from typing import Optional, Dict, Any
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.markdown import Markdown
from rich.table import Table
from rich.text import Text

# 导入新的流式响应架构
from agent.stateless_planner import StatelessGTPlanner
from agent.context_types import AgentContext, Message, MessageRole, ProjectStage
from agent.streaming import StreamingSession, CLIStreamHandler, streaming_manager

# 导入新的SQLite会话管理
from agent.persistence.sqlite_session_manager import SQLiteSessionManager


class ModernGTPlannerCLI:
    """基于新流式响应架构的现代化GTPlanner CLI"""

    def __init__(self, 
                 enable_streaming: bool = True,
                 show_timestamps: bool = False,
                 show_metadata: bool = False,
                 verbose: bool = False):
        """
        初始化现代化CLI
        
        Args:
            enable_streaming: 是否启用流式响应
            show_timestamps: 是否显示时间戳
            show_metadata: 是否显示元数据
            verbose: 是否显示详细信息
        """
        self.console = Console()
        self.enable_streaming = enable_streaming
        self.show_timestamps = show_timestamps
        self.show_metadata = show_metadata
        self.verbose = verbose
        self.running = True
        
        # 使用新的StatelessGTPlanner
        self.planner = StatelessGTPlanner()

        # 使用新的SQLite会话管理器
        self.session_manager = SQLiteSessionManager()
        
        # 流式响应组件
        self.current_streaming_session: Optional[StreamingSession] = None
        self.cli_handler: Optional[CLIStreamHandler] = None
        
        # 设置信号处理
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """设置信号处理器，优雅处理中断"""
        def signal_handler(signum, frame):
            self.console.print("\n🛑 [yellow]接收到中断信号，正在优雅退出...[/yellow]")
            self.running = False
            # 触发异步清理
            if self.current_streaming_session:
                asyncio.create_task(self._cleanup_streaming_session())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def _cleanup_streaming_session(self):
        """清理流式会话资源"""
        if self.current_streaming_session:
            try:
                await self.current_streaming_session.stop()
                self.current_streaming_session = None
                self.cli_handler = None
                self.console.print("✅ [green]流式会话已清理[/green]")
            except Exception as e:
                self.console.print(f"⚠️ [yellow]清理流式会话时出错: {e}[/yellow]")
    
    def _create_streaming_session(self, session_id: str) -> StreamingSession:
        """创建流式会话和处理器"""
        # 创建流式会话
        streaming_session = streaming_manager.create_session(session_id)
        
        # 创建CLI处理器
        cli_handler = CLIStreamHandler(
            show_timestamps=self.show_timestamps,
            show_metadata=self.show_metadata
        )
        
        # 添加处理器到会话
        streaming_session.add_handler(cli_handler)
        
        return streaming_session
    
    def _build_agent_context(self) -> Optional[AgentContext]:
        """构建AgentContext（使用SQLiteSessionManager）"""
        # 直接使用SQLiteSessionManager的build_agent_context方法
        context = self.session_manager.build_agent_context()

        if not context:
            # 如果没有当前会话，创建一个默认的上下文
            return AgentContext(
                session_id="default",
                dialogue_history=[],
                current_stage=ProjectStage.REQUIREMENTS,
                project_state={},
                tool_execution_history=[],
                session_metadata={}
            )

        return context
    
    def show_welcome(self):
        """显示欢迎信息"""
        welcome_text = """
# 🚀 现代化GTPlanner CLI

欢迎使用基于新流式响应架构的智能规划助手！

## ✨ 新特性
- 🌊 **真实流式响应**: 基于StreamEventType/StreamCallbackType的类型安全架构
- 🎯 **无状态设计**: 使用StatelessGTPlanner，支持高并发和水平扩展
- 🔧 **智能工具调用**: 实时显示工具执行状态和进度
- 💬 **优雅交互**: Rich库美化显示，支持中断处理
- 📊 **会话管理**: 完整的会话创建、加载、切换功能

## 🎯 使用方法
直接输入您的需求，我将通过现代化的流式响应为您提供智能规划服务。

## ⚙️ 配置选项
- 流式响应: {'启用' if self.enable_streaming else '禁用'}
- 时间戳显示: {'启用' if self.show_timestamps else '禁用'}
- 元数据显示: {'启用' if self.show_metadata else '禁用'}

## 📝 可用命令
- `/help` - 显示帮助信息
- `/sessions` - 查看会话列表
- `/new` - 创建新会话
- `/load <session_id>` - 加载指定会话
- `/config` - 配置选项
- `/quit` - 退出程序
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🚀 现代化GTPlanner CLI",
            border_style="blue"
        ))
    
    def show_help(self):
        """显示帮助信息"""
        help_text = """
## 📖 命令帮助

### 基本命令
- `/help` - 显示此帮助信息
- `/quit` - 退出程序

### 会话管理
- `/sessions` - 查看所有会话列表
- `/new [title]` - 创建新会话（可选标题）
- `/load <session_id>` - 加载指定会话
- `/current` - 显示当前会话信息

### 配置选项
- `/config` - 显示当前配置
- `/streaming on|off` - 开启/关闭流式响应
- `/timestamps on|off` - 开启/关闭时间戳显示
- `/metadata on|off` - 开启/关闭元数据显示

### 使用示例
```
我想做一个在线教育平台
/new 教育平台项目
/load abc123
/streaming off
```
        """
        
        self.console.print(Panel(
            Markdown(help_text),
            title="帮助信息",
            border_style="green"
        ))
    
    async def process_user_input(self, user_input: str) -> bool:
        """
        处理用户输入（新架构）
        
        Args:
            user_input: 用户输入内容
            
        Returns:
            是否继续运行
        """
        # 处理命令
        if user_input.startswith('/'):
            return await self._handle_command(user_input)
        
        # 确保有当前会话
        if not self.session_manager.current_session_id:
            session_id = self.session_manager.create_new_session()
            self.console.print(f"🆕 [green]创建新会话:[/green] {session_id}")

        try:
            # 添加用户消息到会话
            self.session_manager.add_user_message(user_input)

            # 构建AgentContext
            context = self._build_agent_context()
            if not context:
                self.console.print("❌ [red]无法构建上下文[/red]")
                return True
            
            # 创建流式会话（统一流式架构，总是创建）
            streaming_session = self._create_streaming_session(
                self.session_manager.current_session_id
            )
            self.current_streaming_session = streaming_session

            # 只有在启用流式显示时才启动流式会话
            if self.enable_streaming:
                await streaming_session.start()

            # 使用StatelessGTPlanner处理
            result = await self.planner.process(user_input, context, streaming_session)
            
            # 处理结果
            if result.success:
                # 使用SQLiteSessionManager的update_from_agent_result方法
                update_success = self.session_manager.update_from_agent_result(result)
                if not update_success:
                    self.console.print("⚠️ [yellow]保存结果到数据库时出现问题[/yellow]")
                
                # 如果没有启用流式响应，显示结果
                if not self.enable_streaming and result.new_assistant_messages:
                    self.console.print(Panel(
                        result.new_assistant_messages[0].content,
                        title="🤖 GTPlanner",
                        border_style="blue"
                    ))
            else:
                self.console.print(f"❌ [red]处理失败:[/red] {result.error}")
            
        except Exception as e:
            self.console.print(f"💥 [red]处理异常:[/red] {str(e)}")
            if self.verbose:
                import traceback
                self.console.print(traceback.format_exc())
        
        finally:
            # 清理流式会话
            if self.current_streaming_session:
                await self._cleanup_streaming_session()
        
        return True

    async def _handle_command(self, command: str) -> bool:
        """处理CLI命令"""
        parts = command[1:].split()
        if not parts:
            return True

        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd == "help":
            self.show_help()

        elif cmd == "quit" or cmd == "exit":
            self.console.print("👋 [yellow]再见！[/yellow]")
            return False

        elif cmd == "sessions":
            self._show_sessions()

        elif cmd == "new":
            title = " ".join(args) if args else None
            session_id = self.session_manager.create_new_session(title)
            self.console.print(f"🆕 [green]创建新会话:[/green] {session_id}")

        elif cmd == "load":
            if not args:
                self.console.print("❌ [red]请指定会话ID[/red]")
            else:
                session_id = args[0]
                if self.session_manager.load_session(session_id):
                    self.console.print(f"📂 [green]已加载会话:[/green] {session_id}")
                else:
                    self.console.print(f"❌ [red]加载会话失败:[/red] {session_id}")

        elif cmd == "current":
            self._show_current_session()

        elif cmd == "config":
            self._show_config()

        elif cmd == "streaming":
            if args and args[0].lower() in ["on", "off"]:
                self.enable_streaming = args[0].lower() == "on"
                status = "启用" if self.enable_streaming else "禁用"
                self.console.print(f"🌊 [blue]流式响应已{status}[/blue]")
            else:
                self.console.print("❌ [red]用法: /streaming on|off[/red]")

        elif cmd == "timestamps":
            if args and args[0].lower() in ["on", "off"]:
                self.show_timestamps = args[0].lower() == "on"
                status = "启用" if self.show_timestamps else "禁用"
                self.console.print(f"⏰ [blue]时间戳显示已{status}[/blue]")
            else:
                self.console.print("❌ [red]用法: /timestamps on|off[/red]")

        elif cmd == "metadata":
            if args and args[0].lower() in ["on", "off"]:
                self.show_metadata = args[0].lower() == "on"
                status = "启用" if self.show_metadata else "禁用"
                self.console.print(f"📊 [blue]元数据显示已{status}[/blue]")
            else:
                self.console.print("❌ [red]用法: /metadata on|off[/red]")

        else:
            self.console.print(f"❓ [yellow]未知命令:[/yellow] {cmd}")
            self.console.print("💡 [blue]输入 /help 查看可用命令[/blue]")

        return True

    def _show_sessions(self):
        """显示会话列表"""
        sessions = self.session_manager.list_sessions()

        if not sessions:
            self.console.print("📭 [yellow]暂无会话[/yellow]")
            return

        table = Table(title="📋 会话列表")
        table.add_column("会话ID", style="cyan")
        table.add_column("标题", style="green")
        table.add_column("创建时间", style="blue")
        table.add_column("消息数", style="yellow")
        table.add_column("状态", style="magenta")

        current_id = self.session_manager.current_session_id

        for session in sessions:
            status = "🔸 当前" if session["session_id"] == current_id else ""
            table.add_row(
                session["session_id"][:8] + "...",  # 显示前8位
                session["title"],
                session["created_at"],
                str(session["total_messages"]),  # 使用新的字段名
                status
            )

        self.console.print(table)

    def _show_current_session(self):
        """显示当前会话信息"""
        if not self.session_manager.current_session_id:
            self.console.print("❌ [red]当前无活跃会话[/red]")
            return

        session = self.session_manager.get_current_session()
        if not session:
            self.console.print("❌ [red]无法获取当前会话信息[/red]")
            return

        # 获取统计信息
        stats = self.session_manager.get_session_statistics()

        info_text = f"""
## 📋 当前会话信息

- **会话ID**: {session['session_id'][:8]}...
- **标题**: {session['title']}
- **创建时间**: {session['created_at']}
- **项目阶段**: {session['project_stage']}
- **消息数量**: {session['total_messages']}
- **Token数量**: {session['total_tokens']}
- **工具执行数**: {stats.get('total_executions', 0)}
- **成功执行数**: {stats.get('successful_executions', 0)}
        """

        self.console.print(Panel(
            Markdown(info_text),
            title="当前会话",
            border_style="cyan"
        ))

    def _show_config(self):
        """显示当前配置"""
        config_text = f"""
## ⚙️ 当前配置

- **流式响应**: {'✅ 启用' if self.enable_streaming else '❌ 禁用'}
- **时间戳显示**: {'✅ 启用' if self.show_timestamps else '❌ 禁用'}
- **元数据显示**: {'✅ 启用' if self.show_metadata else '❌ 禁用'}
- **详细模式**: {'✅ 启用' if self.verbose else '❌ 禁用'}

## 🔧 修改配置
- `/streaming on|off` - 开启/关闭流式响应
- `/timestamps on|off` - 开启/关闭时间戳显示
- `/metadata on|off` - 开启/关闭元数据显示
        """

        self.console.print(Panel(
            Markdown(config_text),
            title="配置信息",
            border_style="green"
        ))

    async def run_interactive(self):
        """运行交互式CLI"""
        self.show_welcome()

        while self.running:
            try:
                # 显示提示符
                current_session = self.session_manager.current_session_id or "无会话"
                prompt_text = f"[bold blue]GTPlanner[/bold blue] ({current_session[:8]}) > "

                user_input = Prompt.ask(prompt_text).strip()

                if not user_input:
                    continue

                # 处理用户输入
                should_continue = await self.process_user_input(user_input)
                if not should_continue:
                    break

            except KeyboardInterrupt:
                self.console.print("\n🛑 [yellow]接收到中断信号[/yellow]")
                if Confirm.ask("确定要退出吗？"):
                    break
            except EOFError:
                self.console.print("\n👋 [yellow]再见！[/yellow]")
                break
            except Exception as e:
                self.console.print(f"💥 [red]CLI异常:[/red] {str(e)}")
                if self.verbose:
                    import traceback
                    self.console.print(traceback.format_exc())

        # 清理资源
        await self._cleanup_streaming_session()

    async def run_single_command(self, requirement: str):
        """运行单个命令（非交互式）"""
        self.console.print(f"🚀 [blue]处理需求:[/blue] {requirement}")

        # 创建新会话
        session_id = self.session_manager.create_new_session("单次需求")
        self.console.print(f"🆕 [green]创建会话:[/green] {session_id}")

        # 处理需求
        await self.process_user_input(requirement)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="现代化GTPlanner CLI")
    parser.add_argument("requirement", nargs="?", help="直接处理的需求")
    parser.add_argument("--no-streaming", action="store_true", help="禁用流式响应")
    parser.add_argument("--timestamps", action="store_true", help="显示时间戳")
    parser.add_argument("--metadata", action="store_true", help="显示元数据")
    parser.add_argument("--verbose", "-v", action="store_true", help="显示详细信息")
    parser.add_argument("--load", help="加载指定会话ID")

    args = parser.parse_args()

    # 创建现代化CLI实例
    cli = ModernGTPlannerCLI(
        enable_streaming=not args.no_streaming,
        show_timestamps=args.timestamps,
        show_metadata=args.metadata,
        verbose=args.verbose
    )

    # 如果指定了加载会话
    if args.load:
        if cli.session_manager.load_session(args.load):
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
