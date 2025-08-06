#!/usr/bin/env python3
"""
简化版GTPlanner CLI

提供最简洁的用户体验，避免复杂的流式显示和调试信息。
专注于核心功能：接收用户需求，返回清晰的AI回复。
"""

import sys
import asyncio
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.prompt import Prompt, Confirm

from cli.session_manager import SessionManager
from agent.gtplanner import GTPlanner
from agent.flows.orchestrator_react_flow import OrchestratorReActFlow


class SimpleCLI:
    """简化版GTPlanner CLI"""

    def __init__(self):
        """初始化CLI"""
        self.console = Console()
        self.session_manager = SessionManager()
        self.gtplanner = GTPlanner()
        self.orchestrator = OrchestratorReActFlow()

        # CLI状态
        self.running = True
        self.current_session_id = None

    def show_welcome(self):
        """显示欢迎信息"""
        self.console.print("🚀 GTPlanner - 智能项目规划助手", style="bold blue")
        self.console.print("输入您的项目需求，我将为您提供专业的规划建议。\n", style="cyan")

    async def process_user_input(self, user_input: str):
        """
        处理用户输入

        Args:
            user_input: 用户输入内容
        """
        if not self.current_session_id:
            # 如果没有当前会话，创建新会话
            self.current_session_id = self.session_manager.create_new_session()

        # 添加用户消息到会话
        self.session_manager.add_user_message(user_input)

        # 显示处理提示
        self.console.print(f"🤔 正在分析: {user_input[:50]}{'...' if len(user_input) > 50 else ''}", style="yellow")

        try:
            # 获取当前共享状态
            shared_state = self.session_manager.current_shared_state

            # 运行ReAct主控制器（不使用流式显示）
            result = await self.orchestrator.run_async(shared_state.data, stream_callback=None)

            # 显示结果
            self._display_result(result)

            # 保存会话
            self.session_manager.save_current_session()

        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            self.console.print(f"❌ {error_msg}", style="red")

            # 记录错误到会话
            try:
                self.session_manager.add_assistant_message(f"❌ 处理失败: {str(e)}")
                self.session_manager.save_current_session()
            except:
                pass

    def _display_result(self, result: dict):
        """显示处理结果"""
        flow_result = result.get("flow_result", "")

        # 检查是否是正常的等待用户输入状态
        if flow_result == "wait_for_user":
            self.console.print("✅ 分析完成，等待您的进一步需求", style="green")
            return

        # 检查是否是其他正常结束状态
        if flow_result in ["goal_achieved", "react_complete", "max_cycles_reached"]:
            completion_status = result.get("completion_status", {})
            completed_count = sum(1 for status in completion_status.values() if status)
            total_count = len(completion_status)

            self.console.print(f"✅ 处理完成 ({completed_count}/{total_count} 个阶段)", style="green")

            # 显示具体输出
            if result.get("agent_design_document"):
                self.console.print("📄 已生成完整的架构设计文档", style="bold green")
        else:
            # 错误情况
            error_msg = result.get("error", f"处理异常: {flow_result}")
            self.console.print(f"❌ {error_msg}", style="red")

    def handle_command(self, command: str) -> bool:
        """
        处理命令

        Args:
            command: 用户输入的命令

        Returns:
            是否继续运行
        """
        command = command.lower().strip()

        if command in ["/quit", "/exit", "/q"]:
            return False
        elif command == "/help":
            self._show_help()
        elif command == "/history":
            self._show_history()
        elif command == "/new":
            self._start_new_session()
        else:
            self.console.print(f"❓ 未知命令: {command}，输入 /help 查看帮助", style="yellow")

        return True

    def _show_help(self):
        """显示帮助信息"""
        help_text = """
📖 可用命令：
  /help     - 显示此帮助信息
  /history  - 显示对话历史
  /new      - 开始新会话
  /quit     - 退出程序

💡 使用方法：
  直接输入您的项目需求，例如：
  "我想开发一个在线购物网站"
  "帮我设计一个用户管理系统"
        """
        self.console.print(help_text, style="cyan")

    def _show_history(self):
        """显示对话历史"""
        if not self.current_session_id:
            self.console.print("📝 当前没有活跃会话", style="yellow")
            return

        session_info = self.session_manager.get_current_session_info()
        history = session_info.get("dialogue_history", {}).get("messages", [])

        if not history:
            self.console.print("📝 当前会话没有对话历史", style="yellow")
            return

        self.console.print("💬 对话历史:", style="bold blue")
        for message in history[-5:]:  # 只显示最近5条
            role = message.get("role", "unknown")
            content = message.get("content", "")[:100]  # 限制长度
            if role == "user":
                self.console.print(f"👤 {content}", style="blue")
            elif role == "assistant":
                self.console.print(f"🤖 {content}", style="green")

    def _start_new_session(self):
        """开始新会话"""
        self.current_session_id = self.session_manager.create_new_session()
        self.console.print(f"🆕 已创建新会话: {self.current_session_id}", style="green")

    async def run_interactive(self):
        """运行交互式CLI"""
        self.show_welcome()

        while self.running:
            try:
                # 显示提示符
                session_prompt = f"[{self.current_session_id[:8] if self.current_session_id else '新会话'}] "
                user_input = Prompt.ask(f"{session_prompt}GTPlanner", default="").strip()

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
                self.console.print(f"❌ 发生错误: {e}", style="red")

        self.console.print("👋 再见！", style="blue")

    async def run_direct(self, requirement: str):
        """直接处理需求"""
        self.console.print(f"🚀 处理需求: {requirement}", style="bold blue")
        await self.process_user_input(requirement)


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="GTPlanner 简化版CLI")
    parser.add_argument("requirement", nargs="?", help="直接处理的需求")
    parser.add_argument("--load", help="加载指定会话ID")

    args = parser.parse_args()

    cli = SimpleCLI()

    # 如果指定了加载会话
    if args.load:
        if cli.session_manager.load_session(args.load):
            cli.current_session_id = args.load
            cli.console.print(f"✅ 已加载会话: {args.load}", style="green")
        else:
            cli.console.print(f"❌ 无法加载会话: {args.load}", style="red")
            return

    # 如果提供了直接需求
    if args.requirement:
        await cli.run_direct(args.requirement)
    else:
        await cli.run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
