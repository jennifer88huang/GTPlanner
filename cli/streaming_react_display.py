"""
流式ReAct显示组件 (StreamingReActDisplay)

实时显示ReAct（Reasoning and Acting）循环过程：
1. 思考阶段（Thought）的实时显示
2. 行动阶段（Action）的进度展示
3. 观察阶段（Observation）的结果呈现
4. Agent调度过程的可视化
5. 错误处理和状态更新的友好展示

使用Rich库提供美观的终端界面和动画效果。
"""

import json
import time
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.markdown import Markdown
from rich.syntax import Syntax


class StreamingReActDisplay:
    """流式ReAct过程显示器"""

    def __init__(self, console: Optional[Console] = None):
        """
        初始化显示器

        Args:
            console: Rich控制台实例，如果为None则创建新实例
        """
        self.console = console or Console()
        self.current_cycle = 0
        self.total_cycles = 0
        self.current_stage = "准备中"
        self.current_agent = None
        self.react_history = []

        # 显示状态
        self.is_active = False
        self.live_display = None

        # 增量显示状态跟踪
        self.displayed_content = {
            "thought": {},
            "action": {},
            "observation": {}
        }

        # 样式配置
        self.styles = {
            "thought": "bold blue",
            "action": "bold green",
            "observation": "bold yellow",
            "agent": "bold magenta",
            "success": "bold green",
            "error": "bold red",
            "info": "bold cyan"
        }

    def start_react_session(self, session_title: str = "GTPlanner ReAct 会话"):
        """开始ReAct会话显示"""
        self.is_active = True
        self.current_cycle = 0
        self.react_history = []

        # 重置显示状态
        self.reset_display_state()

        # 显示会话开始
        self.console.print(Panel(
            f"🚀 {session_title}",
            style="bold blue",
            border_style="blue"
        ))

    def reset_display_state(self):
        """重置显示状态，用于新的ReAct循环"""
        self.displayed_content = {
            "thought": {},
            "action": {},
            "observation": {}
        }

    def display_thought_phase(self, thought_data: Dict[str, Any]):
        """
        显示思考阶段（增量显示）

        Args:
            thought_data: 思考数据，包含目标、分析、推理等
        """
        self.current_stage = "思考中"

        # 检查并显示新增内容
        new_content = []

        # 检查当前目标
        if "current_goal" in thought_data:
            if thought_data["current_goal"] != self.displayed_content["thought"].get("current_goal"):
                new_content.append(f"🎯 **当前目标**: {thought_data['current_goal']}")
                self.displayed_content["thought"]["current_goal"] = thought_data["current_goal"]

        # 检查情况分析
        if "situation_analysis" in thought_data:
            if thought_data["situation_analysis"] != self.displayed_content["thought"].get("situation_analysis"):
                new_content.append(f"📊 **情况分析**: {thought_data['situation_analysis']}")
                self.displayed_content["thought"]["situation_analysis"] = thought_data["situation_analysis"]

        # 检查已知信息
        if "known_information" in thought_data and thought_data["known_information"]:
            current_known = self.displayed_content["thought"].get("known_information", [])
            new_known = [info for info in thought_data["known_information"] if info not in current_known]
            if new_known:
                known_info = "\n".join([f"  • {info}" for info in new_known])
                new_content.append(f"✅ **已知信息**:\n{known_info}")
                self.displayed_content["thought"]["known_information"] = thought_data["known_information"]

        # 检查缺失信息
        if "gaps_identified" in thought_data and thought_data["gaps_identified"]:
            current_gaps = self.displayed_content["thought"].get("gaps_identified", [])
            new_gaps = [gap for gap in thought_data["gaps_identified"] if gap not in current_gaps]
            if new_gaps:
                gaps = "\n".join([f"  • {gap}" for gap in new_gaps])
                new_content.append(f"❓ **缺失信息**:\n{gaps}")
                self.displayed_content["thought"]["gaps_identified"] = thought_data["gaps_identified"]

        # 检查推理过程
        if "reasoning" in thought_data:
            if thought_data["reasoning"] != self.displayed_content["thought"].get("reasoning"):
                new_content.append(f"🤔 **推理过程**: {thought_data['reasoning']}")
                self.displayed_content["thought"]["reasoning"] = thought_data["reasoning"]

        # 只显示新增内容
        if new_content:
            content = "\n\n".join(new_content)
            self.console.print(Panel(
                Markdown(content),
                title="💭 思考阶段 (Thought)",
                style=self.styles["thought"],
                border_style="blue"
            ))

    def display_action_phase(self, action_data: Dict[str, Any]):
        """
        显示行动阶段（增量显示）

        Args:
            action_data: 行动数据，包含行动类型、理由等
        """
        self.current_stage = "行动中"

        # 检查并显示新增内容
        new_content = []

        # 检查行动类型
        if "action_type" in action_data:
            if action_data["action_type"] != self.displayed_content["action"].get("action_type"):
                action_type_map = {
                    "requirements_analysis": "📋 需求分析",
                    "short_planning": "📝 短规划生成",
                    "research": "🔍 信息研究",
                    "architecture_design": "🏗️ 架构设计",
                    "user_interaction": "💬 用户交互",
                    "complete": "✅ 完成处理"
                }
                action_type_display = action_type_map.get(action_data["action_type"], action_data["action_type"])
                new_content.append(f"🎬 **行动类型**: {action_type_display}")
                self.displayed_content["action"]["action_type"] = action_data["action_type"]

        # 检查行动理由
        if "action_rationale" in action_data:
            if action_data["action_rationale"] != self.displayed_content["action"].get("action_rationale"):
                new_content.append(f"💡 **行动理由**: {action_data['action_rationale']}")
                self.displayed_content["action"]["action_rationale"] = action_data["action_rationale"]

        # 检查预期结果
        if "expected_outcome" in action_data:
            if action_data["expected_outcome"] != self.displayed_content["action"].get("expected_outcome"):
                new_content.append(f"🎯 **预期结果**: {action_data['expected_outcome']}")
                self.displayed_content["action"]["expected_outcome"] = action_data["expected_outcome"]

        # 检查置信度
        if "confidence" in action_data:
            if action_data["confidence"] != self.displayed_content["action"].get("confidence"):
                confidence = action_data["confidence"]
                confidence_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
                new_content.append(f"📊 **置信度**: {confidence:.1%} [{confidence_bar}]")
                self.displayed_content["action"]["confidence"] = action_data["confidence"]

        # 只显示新增内容
        if new_content:
            content = "\n\n".join(new_content)
            self.console.print(Panel(
                Markdown(content),
                title="⚡ 行动阶段 (Action)",
                style=self.styles["action"],
                border_style="green"
            ))

    def display_agent_execution(self, agent_type: str, status: str = "执行中"):
        """
        显示Agent执行状态
        
        Args:
            agent_type: Agent类型
            status: 执行状态
        """
        self.current_agent = agent_type
        
        agent_name_map = {
            "requirements_analysis": "需求分析Agent",
            "short_planning": "短规划Agent",
            "research": "研究Agent",
            "architecture_design": "架构设计Agent"
        }
        
        agent_name = agent_name_map.get(agent_type, agent_type)
        
        # 使用进度条显示Agent执行
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
            console=self.console
        ) as progress:
            task = progress.add_task(f"🤖 {agent_name} {status}...", total=None)
            
            # 模拟执行时间（实际使用时应该与真实执行同步）
            time.sleep(0.5)

    def display_observation_phase(self, observation_data: Dict[str, Any]):
        """
        显示观察阶段（增量显示）

        Args:
            observation_data: 观察数据，包含进度、结果等
        """
        self.current_stage = "观察中"

        # 检查并显示新增内容
        new_content = []

        # 检查当前进度
        if "current_progress" in observation_data:
            if observation_data["current_progress"] != self.displayed_content["observation"].get("current_progress"):
                new_content.append(f"📈 **当前进度**: {observation_data['current_progress']}")
                self.displayed_content["observation"]["current_progress"] = observation_data["current_progress"]

        # 检查目标状态
        if "goal_achieved" in observation_data:
            if observation_data["goal_achieved"] != self.displayed_content["observation"].get("goal_achieved"):
                goal_status = "✅ 已达成" if observation_data["goal_achieved"] else "⏳ 进行中"
                new_content.append(f"🎯 **目标状态**: {goal_status}")
                self.displayed_content["observation"]["goal_achieved"] = observation_data["goal_achieved"]

        # 检查循环决策
        if "should_continue_cycle" in observation_data:
            if observation_data["should_continue_cycle"] != self.displayed_content["observation"].get("should_continue_cycle"):
                continue_status = "🔄 继续循环" if observation_data["should_continue_cycle"] else "⏹️ 停止循环"
                new_content.append(f"🔄 **循环决策**: {continue_status}")
                self.displayed_content["observation"]["should_continue_cycle"] = observation_data["should_continue_cycle"]

        # 检查用户交互需求
        if "requires_user_input" in observation_data:
            if observation_data["requires_user_input"] != self.displayed_content["observation"].get("requires_user_input"):
                user_input_status = "💬 需要用户输入" if observation_data["requires_user_input"] else "🤖 自动处理"
                new_content.append(f"👤 **用户交互**: {user_input_status}")
                self.displayed_content["observation"]["requires_user_input"] = observation_data["requires_user_input"]

        # 检查下一步重点
        if "next_focus" in observation_data:
            if observation_data["next_focus"] != self.displayed_content["observation"].get("next_focus"):
                new_content.append(f"🎯 **下一步重点**: {observation_data['next_focus']}")
                self.displayed_content["observation"]["next_focus"] = observation_data["next_focus"]

        # 检查成功指标
        if "success_indicators" in observation_data and observation_data["success_indicators"]:
            current_indicators = self.displayed_content["observation"].get("success_indicators", [])
            new_indicators = [ind for ind in observation_data["success_indicators"] if ind not in current_indicators]
            if new_indicators:
                indicators = "\n".join([f"  • {indicator}" for indicator in new_indicators])
                new_content.append(f"✅ **成功指标**:\n{indicators}")
                self.displayed_content["observation"]["success_indicators"] = observation_data["success_indicators"]

        # 只显示新增内容
        if new_content:
            content = "\n\n".join(new_content)
            self.console.print(Panel(
                Markdown(content),
                title="👁️ 观察阶段 (Observation)",
                style=self.styles["observation"],
                border_style="yellow"
            ))

    def display_cycle_summary(self, cycle_number: int, cycle_data: Dict[str, Any]):
        """
        显示ReAct循环摘要
        
        Args:
            cycle_number: 循环编号
            cycle_data: 循环数据
        """
        self.current_cycle = cycle_number
        
        # 创建摘要表格
        table = Table(title=f"🔄 ReAct 循环 #{cycle_number} 摘要")
        table.add_column("阶段", style="bold")
        table.add_column("状态", style="bold")
        table.add_column("关键信息")
        
        # 思考阶段
        thought = cycle_data.get("thought", {})
        table.add_row(
            "💭 思考",
            "✅ 完成",
            thought.get("current_goal", "N/A")[:50] + ("..." if len(thought.get("current_goal", "")) > 50 else "")
        )
        
        # 行动阶段
        action_decision = cycle_data.get("action_decision", {})
        action_execution = cycle_data.get("action_execution", {})
        action_status = "✅ 成功" if action_execution.get("success") else "❌ 失败"
        table.add_row(
            "⚡ 行动",
            action_status,
            action_decision.get("action_type", "N/A")
        )
        
        # 观察阶段
        observation = cycle_data.get("observation", {})
        obs_status = "🎯 目标达成" if observation.get("goal_achieved") else "⏳ 继续处理"
        table.add_row(
            "👁️ 观察",
            obs_status,
            observation.get("current_progress", "N/A")[:50] + ("..." if len(observation.get("current_progress", "")) > 50 else "")
        )
        
        self.console.print(table)
        self.console.print()  # 添加空行

    def display_error(self, error_message: str, error_type: str = "执行错误"):
        """
        显示错误信息
        
        Args:
            error_message: 错误消息
            error_type: 错误类型
        """
        self.console.print(Panel(
            f"❌ **{error_type}**\n\n{error_message}",
            title="🚨 错误",
            style=self.styles["error"],
            border_style="red"
        ))

    def display_success(self, success_message: str, title: str = "成功"):
        """
        显示成功信息
        
        Args:
            success_message: 成功消息
            title: 标题
        """
        self.console.print(Panel(
            f"✅ {success_message}",
            title=f"🎉 {title}",
            style=self.styles["success"],
            border_style="green"
        ))

    def display_session_status(self, session_info: Dict[str, Any]):
        """
        显示会话状态
        
        Args:
            session_info: 会话信息
        """
        # 创建状态表格
        table = Table(title="📊 会话状态")
        table.add_column("项目", style="bold")
        table.add_column("值")
        
        table.add_row("会话ID", session_info.get("session_id", "N/A"))
        table.add_row("当前阶段", session_info.get("current_stage", "N/A"))
        table.add_row("消息数量", str(session_info.get("message_count", 0)))
        table.add_row("ReAct循环", str(session_info.get("react_cycles", 0)))
        table.add_row("创建时间", session_info.get("created_at", "N/A"))
        
        self.console.print(table)

    def display_agent_status_table(self, agents_status: Dict[str, Any]):
        """
        显示Agent状态表格
        
        Args:
            agents_status: Agent状态信息
        """
        table = Table(title="🤖 Agent 状态")
        table.add_column("Agent", style="bold")
        table.add_column("状态")
        table.add_column("最后调用")
        table.add_column("成功率")
        
        for agent_name, status in agents_status.items():
            status_icon = "✅" if status.get("available", False) else "❌"
            last_call = status.get("last_call", "从未调用")
            success_rate = f"{status.get('success_rate', 0):.1%}"
            
            table.add_row(agent_name, status_icon, last_call, success_rate)
        
        self.console.print(table)

    def end_react_session(self, final_result: Dict[str, Any]):
        """
        结束ReAct会话显示
        
        Args:
            final_result: 最终结果
        """
        self.is_active = False
        
        # 显示最终结果
        success = final_result.get("success", False)
        cycles = final_result.get("react_cycles", 0)
        
        if success:
            self.console.print(Panel(
                f"🎉 **ReAct会话成功完成！**\n\n"
                f"📊 总循环次数: {cycles}\n"
                f"✅ 处理状态: 成功\n"
                f"🕒 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                title="✨ 会话完成",
                style=self.styles["success"],
                border_style="green"
            ))
        else:
            error_msg = final_result.get("error", "未知错误")
            self.console.print(Panel(
                f"❌ **ReAct会话未能完成**\n\n"
                f"📊 总循环次数: {cycles}\n"
                f"❌ 错误信息: {error_msg}\n"
                f"🕒 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                title="⚠️ 会话结束",
                style=self.styles["error"],
                border_style="red"
            ))

    def clear_screen(self):
        """清屏"""
        self.console.clear()

    def print_separator(self, title: str = ""):
        """打印分隔符"""
        if title:
            self.console.print(f"\n{'='*20} {title} {'='*20}\n")
        else:
            self.console.print("\n" + "="*60 + "\n")
