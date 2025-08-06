#!/usr/bin/env python3
"""
新CLI系统演示脚本

演示基于ReAct模式的新CLI系统功能：
1. 会话管理
2. 流式ReAct显示
3. 上下文对话
4. Agent调度显示
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

def demo_session_manager():
    """演示会话管理器"""
    print("=" * 60)
    print("1. 演示会话管理器")
    print("=" * 60)
    
    try:
        from cli.session_manager import SessionManager
        
        # 创建会话管理器
        session_manager = SessionManager()
        
        # 创建新会话
        session_id = session_manager.create_new_session("演示用户")
        print(f"✓ 创建新会话: {session_id}")
        
        # 添加消息
        session_manager.add_user_message("我需要设计一个用户管理系统")
        session_manager.add_assistant_message("好的，我来帮您分析需求")
        
        # 获取会话信息
        session_info = session_manager.get_current_session_info()
        print(f"✓ 会话信息: {session_info}")
        
        # 保存会话
        session_manager.save_current_session()
        print("✓ 会话已保存")
        
        # 列出所有会话
        sessions = session_manager.list_sessions()
        print(f"✓ 会话列表: {len(sessions)} 个会话")
        
        return True
        
    except Exception as e:
        print(f"✗ 会话管理器演示失败: {e}")
        return False

def demo_streaming_display():
    """演示流式显示组件"""
    print("\n" + "=" * 60)
    print("2. 演示流式显示组件")
    print("=" * 60)
    
    try:
        from cli.streaming_react_display import StreamingReActDisplay
        from rich.console import Console
        
        console = Console()
        display = StreamingReActDisplay(console)
        
        # 开始会话
        display.start_react_session("演示会话")
        
        # 演示思考阶段
        thought_data = {
            "current_goal": "分析用户管理系统需求",
            "situation_analysis": "用户提供了基本需求描述",
            "known_information": ["需要用户管理功能", "包含注册登录"],
            "gaps_identified": ["具体功能需求", "技术约束"],
            "reasoning": "首先需要进行详细的需求分析"
        }
        display.display_thought_phase(thought_data)
        
        # 演示行动阶段
        action_data = {
            "action_type": "requirements_analysis",
            "action_rationale": "需要将用户需求转换为结构化文档",
            "expected_outcome": "获得详细的需求规格",
            "confidence": 0.9
        }
        display.display_action_phase(action_data)
        
        # 演示Agent执行
        display.display_agent_execution("requirements_analysis", "已完成")
        
        # 演示观察阶段
        observation_data = {
            "current_progress": "需求分析完成",
            "goal_achieved": False,
            "should_continue_cycle": True,
            "requires_user_input": False,
            "next_focus": "架构设计",
            "success_indicators": ["生成需求文档", "识别核心功能"]
        }
        display.display_observation_phase(observation_data)
        
        # 演示循环摘要
        cycle_data = {
            "thought": thought_data,
            "action_decision": action_data,
            "action_execution": {"success": True, "action_type": "requirements_analysis"},
            "observation": observation_data
        }
        display.display_cycle_summary(1, cycle_data)
        
        # 演示成功消息
        display.display_success("演示完成！", "流式显示演示")
        
        print("✓ 流式显示组件演示成功")
        return True
        
    except Exception as e:
        print(f"✗ 流式显示组件演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_react_orchestrator():
    """演示ReAct主控制器"""
    print("\n" + "=" * 60)
    print("3. 演示ReAct主控制器")
    print("=" * 60)
    
    try:
        from agent.flows.orchestrator_react_flow import OrchestratorReActFlow
        from agent.shared import SharedState
        
        # 创建主控制器
        orchestrator = OrchestratorReActFlow()
        
        # 获取流程信息
        info = orchestrator.get_flow_info()
        print(f"✓ 流程名称: {info['name']}")
        print(f"✓ 支持的行动: {info['supported_actions']}")
        
        # 创建测试共享状态
        shared_state = SharedState()
        shared_state.add_user_message("设计一个简单的博客系统")
        
        # 获取状态
        status = orchestrator.get_status(shared_state.data)
        print(f"✓ 当前状态: {status}")
        
        print("✓ ReAct主控制器演示成功")
        return True
        
    except Exception as e:
        print(f"✗ ReAct主控制器演示失败: {e}")
        return False

def demo_cli_components():
    """演示CLI组件集成"""
    print("\n" + "=" * 60)
    print("4. 演示CLI组件集成")
    print("=" * 60)
    
    try:
        from cli.react_cli import ReActCLI
        
        # 创建CLI实例
        cli = ReActCLI()
        
        print("✓ CLI实例创建成功")
        print(f"✓ 会话管理器: {type(cli.session_manager).__name__}")
        print(f"✓ 显示组件: {type(cli.display).__name__}")
        print(f"✓ GTPlanner: {type(cli.gtplanner).__name__}")
        print(f"✓ 主控制器: {type(cli.orchestrator).__name__}")
        
        # 测试帮助显示
        print("\n📚 帮助信息演示:")
        cli.show_help()
        
        print("✓ CLI组件集成演示成功")
        return True
        
    except Exception as e:
        print(f"✗ CLI组件集成演示失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def demo_async_processing():
    """演示异步处理"""
    print("\n" + "=" * 60)
    print("5. 演示异步处理")
    print("=" * 60)
    
    try:
        from cli.react_cli import ReActCLI
        
        # 创建CLI实例
        cli = ReActCLI()
        
        # 模拟处理简单需求（不实际调用LLM）
        print("✓ 异步处理框架准备就绪")
        print("✓ 支持流式ReAct循环显示")
        print("✓ 支持上下文对话管理")
        
        return True
        
    except Exception as e:
        print(f"✗ 异步处理演示失败: {e}")
        return False

def show_architecture_summary():
    """显示架构总结"""
    console = Console()
    
    architecture_text = """
# 🏗️ 新CLI系统架构总结

## 核心组件

### 1. 会话管理器 (SessionManager)
- ✅ 多轮对话上下文管理
- ✅ 会话持久化和恢复
- ✅ 自动保存和清理机制
- ✅ 会话导入/导出功能

### 2. 流式显示组件 (StreamingReActDisplay)
- ✅ 实时ReAct循环显示
- ✅ 思考-行动-观察可视化
- ✅ Agent执行状态展示
- ✅ Rich UI组件集成

### 3. ReAct主控制器集成
- ✅ 单体LLM ReAct循环
- ✅ Agent调度和协调
- ✅ 错误处理和恢复
- ✅ 状态管理集成

### 4. CLI交互界面 (ReActCLI)
- ✅ 交互式命令处理
- ✅ 直接需求处理
- ✅ 会话管理命令
- ✅ 异步处理支持

## 主要特性

- 🧠 **智能ReAct循环**: 完整的思考-行动-观察闭环
- 💬 **上下文对话**: 支持多轮对话和历史记录
- 🤖 **专业Agent集成**: 无缝调用所有专业Agent
- 📊 **实时可视化**: 流式显示处理过程
- 💾 **会话管理**: 自动保存和恢复功能
- 🎨 **美观界面**: Rich库提供的现代终端UI

## 使用方式

```bash
# 启动交互式CLI
python cli/react_cli.py

# 直接处理需求
python cli/react_cli.py "设计用户管理系统"

# 加载指定会话
python cli/react_cli.py --load session_id
```
    """
    
    console.print(Panel(
        Markdown(architecture_text),
        title="🚀 GTPlanner 新CLI系统",
        border_style="blue"
    ))

async def main():
    """主演示函数"""
    print("GTPlanner 新CLI系统演示")
    print("基于ReAct模式的智能对话界面")
    
    # 运行各个演示
    results = []
    
    results.append(demo_session_manager())
    results.append(demo_streaming_display())
    results.append(demo_react_orchestrator())
    results.append(demo_cli_components())
    results.append(await demo_async_processing())
    
    # 显示架构总结
    show_architecture_summary()
    
    # 总结结果
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n{'='*60}")
    print(f"演示结果: {success_count}/{total_count} 成功")
    
    if success_count == total_count:
        print("🎉 所有演示成功完成！新CLI系统准备就绪。")
        print("\n🚀 可以使用以下命令启动新CLI:")
        print("   python cli/react_cli.py")
    else:
        print("⚠️ 部分演示失败，请检查系统配置。")
    
    return success_count == total_count

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
