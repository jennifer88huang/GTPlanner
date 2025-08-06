"""
真正的实时流式显示组件 (RealTimeStreamingDisplay)

实现字符级的真正流式显示：
1. 订阅特定JSON字段的实时更新
2. 字符级的增量显示，模型输出什么就立即显示什么
3. 支持多个字段同时流式显示
4. 美观的终端界面和动画效果

使用Rich库提供美观的终端界面。
"""

import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout
from rich.align import Align
from rich.columns import Columns
from rich.markdown import Markdown
from rich.syntax import Syntax


class RealTimeStreamingDisplay:
    """真正的实时流式显示器"""

    def __init__(self, console: Optional[Console] = None):
        """
        初始化显示器

        Args:
            console: Rich控制台实例，如果为None则创建新实例
        """
        self.console = console or Console()

        # 字段显示状态
        self.field_displays = {}  # 字段名 -> 显示内容
        self.field_panels = {}    # 字段名 -> Panel对象
        self.field_titles = {
            "user_message": "💬 AI助手回复",  # 新增：用户消息字段
            "thought.current_goal": "🎯 当前目标",
            "thought.situation_analysis": "📊 情况分析",
            "thought.reasoning": "🤔 推理过程",
            "action_decision.action_type": "⚡ 行动类型",
            "action_decision.action_rationale": "💡 行动理由",
            "observation.current_progress": "📈 当前进度",
            "observation.next_focus": "🎯 下一步重点"
        }

        # 显示状态
        self.is_active = False
        self.live_display = None
        self.current_layout = None

        # 更新控制
        self.last_update_time = 0
        self.update_interval = 0.1  # 最小更新间隔（秒）
        self.pending_updates = set()  # 待更新的字段

        # 样式配置
        self.styles = {
            "thought": "bold blue",
            "action": "bold green",
            "observation": "bold yellow",
            "success": "bold green",
            "error": "bold red",
            "info": "bold cyan"
        }

    def start_streaming_session(self, session_title: str = "GTPlanner 实时流式显示"):
        """开始流式会话显示"""
        self.is_active = True
        self.field_displays = {}
        self.field_panels = {}

        # 简化会话开始显示，减少视觉干扰
        self.console.print(f"🚀 {session_title}", style="bold blue")

        # 启动Live显示（降低刷新频率以减少闪烁）
        self.current_layout = Layout()
        self.live_display = Live(self.current_layout, console=self.console, refresh_per_second=5)
        self.live_display.start()

    def create_field_callback(self, field_path: str) -> Callable:
        """
        创建字段的实时更新回调函数
        
        Args:
            field_path: 字段路径，如 "thought.reasoning"
            
        Returns:
            回调函数
        """
        def field_callback(path: str, new_content: str, is_complete: bool):
            """字段更新回调"""
            if path != field_path:
                return
                
            # 更新字段显示内容
            if field_path not in self.field_displays:
                self.field_displays[field_path] = ""
            
            # 添加新内容
            self.field_displays[field_path] += new_content
            
            # 立即显示更新
            self._display_field_update(field_path, new_content, is_complete)
        
        return field_callback

    def handle_field_update(self, field_path: str, new_content: str, is_complete: bool):
        """
        处理字段更新的公共接口

        Args:
            field_path: 字段路径，如 "thought.current_goal"
            new_content: 新增的内容
            is_complete: 字段是否完成
        """
        # 特殊处理user_message字段：只在完成时显示，流式过程中不显示
        if field_path == "user_message":
            # 更新内容但不显示
            if field_path not in self.field_displays:
                self.field_displays[field_path] = ""
            self.field_displays[field_path] += new_content

            # 只在完成时显示独立的对话消息
            if is_complete:
                self._display_user_message_complete()
            return

        # 其他字段正常处理，但只显示重要字段
        important_fields = [
            "thought.reasoning",
            "action_decision.action_type",
            "observation.current_progress"
        ]
        if field_path in important_fields:
            self._display_field_update(field_path, new_content, is_complete)

    def _display_user_message_complete(self):
        """当user_message完成时，显示为独立的对话消息"""
        user_message = self.field_displays.get("user_message", "")
        if user_message:
            # 临时停止Live显示以显示独立消息
            live_was_active = False
            if self.live_display:
                live_was_active = True
                self.live_display.stop()
                self.live_display = None

            # 显示AI回复（处理换行符），使用更简洁的格式
            formatted_message = user_message.replace("\\n", "\n")
            self.console.print(f"\n🤖 {formatted_message}\n", style="bold cyan")

            # 重新启动Live显示（如果之前是活跃的）
            if self.is_active and live_was_active:
                self.live_display = Live(self.current_layout, console=self.console, refresh_per_second=5)
                self.live_display.start()

    def _display_field_update(self, field_path: str, new_content: str, is_complete: bool):
        """显示字段更新（使用Live显示避免刷屏）"""
        if not new_content:
            return

        # 更新字段内容
        if field_path not in self.field_displays:
            self.field_displays[field_path] = ""
        self.field_displays[field_path] += new_content

        # 标记字段需要更新
        self.pending_updates.add(field_path)

        # 控制更新频率
        import time
        current_time = time.time()

        # 如果字段完成或者距离上次更新超过间隔时间，则立即更新
        if is_complete or (current_time - self.last_update_time) >= self.update_interval:
            self._flush_pending_updates()
            self.last_update_time = current_time

    def _flush_pending_updates(self):
        """刷新所有待更新的字段"""
        if not self.pending_updates:
            return

        # 更新所有待更新的字段面板
        for field_path in self.pending_updates:
            self._update_field_panel(field_path)

        # 更新Live显示
        self._update_live_display()

        # 清空待更新列表
        self.pending_updates.clear()

    def _update_field_panel(self, field_path: str):
        """更新单个字段的面板"""
        # 获取字段标题
        title = self.field_titles.get(field_path, field_path)

        # 获取字段样式
        field_category = field_path.split('.')[0]  # thought, action, observation, user_message

        # 特殊处理user_message字段
        if field_path == "user_message":
            style = "bold cyan"
            border_style = "cyan"
        else:
            style = self.styles.get(field_category, "white")
            # 修复border_style，使用有效的颜色名称
            border_style_map = {
                "thought": "blue",
                "action": "green",
                "observation": "yellow"
            }
            border_style = border_style_map.get(field_category, "white")

        # 获取完整内容
        full_content = self.field_displays.get(field_path, "")

        # 创建面板
        panel = Panel(
            full_content,
            title=title,
            style=style,
            border_style=border_style
        )

        # 更新字段面板
        self.field_panels[field_path] = panel

    def _update_live_display(self):
        """更新Live显示"""
        if self.live_display and self.current_layout:
            # 创建包含所有字段的布局
            panels = list(self.field_panels.values())
            if panels:
                from rich.columns import Columns
                self.current_layout.update(Columns(panels, equal=True))
        elif self.field_panels:
            # 如果Live显示未启动，直接打印最新的面板（兜底方案）
            for panel in self.field_panels.values():
                self.console.print(panel)

    def display_phase_header(self, phase: str):
        """显示阶段标题"""
        phase_map = {
            "thought": "💭 思考阶段 (Thought)",
            "action": "⚡ 行动阶段 (Action)", 
            "observation": "👁️ 观察阶段 (Observation)"
        }
        
        title = phase_map.get(phase, phase)
        style = self.styles.get(phase, "white")
        
        self.console.print(f"\n{title}", style=f"bold {style}")
        self.console.print("─" * 80, style=style)

    def display_success(self, message: str, title: str = "成功"):
        """显示成功信息"""
        self.console.print(Panel(
            message,
            title=f"✅ {title}",
            style=self.styles["success"],
            border_style="green"
        ))

    def display_error(self, message: str, title: str = "错误"):
        """显示错误信息"""
        self.console.print(Panel(
            message,
            title=f"❌ {title}",
            style=self.styles["error"],
            border_style="red"
        ))

    def display_info(self, message: str, title: str = "信息"):
        """显示信息"""
        self.console.print(Panel(
            message,
            title=f"ℹ️ {title}",
            style=self.styles["info"],
            border_style="cyan"
        ))

    def end_streaming_session(self, final_result: Dict[str, Any]):
        """结束流式会话显示"""
        self.is_active = False

        # 刷新所有待更新的内容
        self._flush_pending_updates()

        # 停止Live显示
        if self.live_display:
            self.live_display.stop()
            self.live_display = None

        # 简化最终结果显示
        success = final_result.get("success", False)
        cycles = final_result.get("react_cycles", 0)

        if success:
            self.console.print(f"✅ 处理完成 (循环次数: {cycles})", style="bold green")
        else:
            error_msg = final_result.get("error", "未知错误")
            self.console.print(f"❌ 处理失败: {error_msg}", style="bold red")

    def reset_display_state(self):
        """重置显示状态"""
        self.field_displays = {}
        self.field_panels = {}

    def get_field_content(self, field_path: str) -> str:
        """获取字段的当前内容"""
        return self.field_displays.get(field_path, "")

    def clear_field(self, field_path: str):
        """清空字段内容"""
        if field_path in self.field_displays:
            self.field_displays[field_path] = ""
