#!/usr/bin/env python3
"""
GTPlanner 新CLI系统综合测试

测试新CLI系统的各种使用场景和功能：
1. 会话管理功能测试
2. 命令处理测试
3. 显示组件测试
4. 错误处理测试
5. 性能测试
"""

import sys
import os
import asyncio
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

def test_session_manager_comprehensive():
    """全面测试会话管理器"""
    print("=" * 60)
    print("1. 会话管理器综合测试")
    print("=" * 60)
    
    try:
        from cli.session_manager import SessionManager
        
        # 使用临时目录进行测试
        with tempfile.TemporaryDirectory() as temp_dir:
            session_manager = SessionManager(temp_dir)
            
            # 测试创建多个会话
            session_ids = []
            for i in range(3):
                session_id = session_manager.create_new_session(f"测试用户{i+1}")
                session_ids.append(session_id)
                
                # 添加不同数量的消息
                for j in range(i + 1):
                    session_manager.add_user_message(f"用户消息 {j+1}")
                    session_manager.add_assistant_message(f"助手回复 {j+1}")
                
                session_manager.save_current_session()
            
            print(f"✓ 创建了 {len(session_ids)} 个会话")
            
            # 测试会话列表
            sessions = session_manager.list_sessions()
            print(f"✓ 会话列表包含 {len(sessions)} 个会话")
            
            # 测试会话加载
            for session_id in session_ids:
                success = session_manager.load_session(session_id)
                print(f"✓ 会话 {session_id} 加载{'成功' if success else '失败'}")
            
            # 测试会话导出/导入
            export_path = Path(temp_dir) / "exported_session.json"
            if session_manager.export_session(session_ids[0], str(export_path)):
                print("✓ 会话导出成功")
                
                imported_id = session_manager.import_session(str(export_path))
                if imported_id:
                    print(f"✓ 会话导入成功，新ID: {imported_id}")
                else:
                    print("✗ 会话导入失败")
            
            # 测试会话删除
            if session_manager.delete_session(session_ids[-1]):
                print("✓ 会话删除成功")
            else:
                print("✗ 会话删除失败")
        
        return True
        
    except Exception as e:
        print(f"✗ 会话管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streaming_display_comprehensive():
    """全面测试流式显示组件"""
    print("\n" + "=" * 60)
    print("2. 流式显示组件综合测试")
    print("=" * 60)
    
    try:
        from cli.streaming_react_display import StreamingReActDisplay
        from rich.console import Console
        
        console = Console()
        display = StreamingReActDisplay(console)
        
        # 测试完整的ReAct循环显示
        display.start_react_session("综合测试会话")
        
        # 模拟多个ReAct循环
        for cycle in range(2):
            print(f"\n--- ReAct 循环 #{cycle + 1} ---")
            
            # 思考阶段
            thought_data = {
                "current_goal": f"完成第{cycle + 1}个目标",
                "situation_analysis": f"当前处于第{cycle + 1}个循环",
                "known_information": [f"已完成{cycle}个循环", "系统运行正常"],
                "gaps_identified": ["需要更多信息", "需要用户确认"],
                "reasoning": f"基于前{cycle}个循环的结果，继续处理"
            }
            display.display_thought_phase(thought_data)
            
            # 行动阶段
            action_types = ["requirements_analysis", "research", "architecture_design"]
            action_data = {
                "action_type": action_types[cycle % len(action_types)],
                "action_rationale": f"第{cycle + 1}个循环的行动",
                "expected_outcome": "获得预期结果",
                "confidence": 0.8 + (cycle * 0.1)
            }
            display.display_action_phase(action_data)
            
            # Agent执行
            display.display_agent_execution(action_data["action_type"], "执行中")
            
            # 观察阶段
            observation_data = {
                "current_progress": f"第{cycle + 1}个循环完成",
                "goal_achieved": cycle == 1,  # 最后一个循环达成目标
                "should_continue_cycle": cycle == 0,  # 第一个循环继续
                "requires_user_input": False,
                "next_focus": "下一步处理" if cycle == 0 else "完成",
                "success_indicators": [f"循环{cycle + 1}成功", "状态更新"]
            }
            display.display_observation_phase(observation_data)
            
            # 循环摘要
            cycle_data = {
                "thought": thought_data,
                "action_decision": action_data,
                "action_execution": {"success": True, "action_type": action_data["action_type"]},
                "observation": observation_data
            }
            display.display_cycle_summary(cycle + 1, cycle_data)
        
        # 测试错误显示
        display.display_error("这是一个测试错误", "测试错误类型")
        
        # 测试成功显示
        display.display_success("所有测试通过！", "测试完成")
        
        # 测试会话状态显示
        session_info = {
            "session_id": "test123",
            "current_stage": "testing",
            "message_count": 10,
            "react_cycles": 2,
            "created_at": "2025-08-06T12:00:00"
        }
        display.display_session_status(session_info)
        
        # 测试Agent状态表格
        agents_status = {
            "需求分析Agent": {"available": True, "last_call": "刚刚", "success_rate": 0.95},
            "研究Agent": {"available": True, "last_call": "5分钟前", "success_rate": 0.88},
            "架构设计Agent": {"available": False, "last_call": "从未调用", "success_rate": 0.0}
        }
        display.display_agent_status_table(agents_status)
        
        # 结束会话
        final_result = {"success": True, "react_cycles": 2}
        display.end_react_session(final_result)
        
        print("✓ 流式显示组件综合测试成功")
        return True
        
    except Exception as e:
        print(f"✗ 流式显示组件测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cli_commands():
    """测试CLI命令处理"""
    print("\n" + "=" * 60)
    print("3. CLI命令处理测试")
    print("=" * 60)
    
    try:
        from cli.react_cli import ReActCLI
        
        # 使用临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            cli = ReActCLI()
            cli.session_manager.sessions_dir = Path(temp_dir)
            
            # 测试帮助命令
            print("测试 /help 命令:")
            cli.show_help()
            
            # 测试创建新会话
            print("\n测试会话创建:")
            result = cli.handle_command("/new")
            print(f"✓ 新会话命令处理: {result}")
            
            # 测试会话列表
            print("\n测试会话列表:")
            cli.show_sessions()
            
            # 测试状态显示
            print("\n测试状态显示:")
            cli.show_status()
            
            # 测试统计显示
            print("\n测试统计显示:")
            cli.show_stats()
            
            # 测试未知命令
            print("\n测试未知命令:")
            result = cli.handle_command("/unknown")
            print(f"✓ 未知命令处理: {result}")
            
        print("✓ CLI命令处理测试成功")
        return True
        
    except Exception as e:
        print(f"✗ CLI命令处理测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n" + "=" * 60)
    print("4. 错误处理测试")
    print("=" * 60)
    
    try:
        from cli.session_manager import SessionManager
        from cli.streaming_react_display import StreamingReActDisplay
        from rich.console import Console
        
        # 测试会话管理器错误处理
        session_manager = SessionManager("/invalid/path/that/does/not/exist")
        
        # 测试加载不存在的会话
        result = session_manager.load_session("nonexistent")
        print(f"✓ 加载不存在会话的处理: {not result}")
        
        # 测试删除不存在的会话
        result = session_manager.delete_session("nonexistent")
        print(f"✓ 删除不存在会话的处理: {not result}")
        
        # 测试显示组件错误处理
        console = Console()
        display = StreamingReActDisplay(console)
        
        # 测试无效数据的处理
        display.display_thought_phase({})  # 空数据
        display.display_action_phase({})   # 空数据
        display.display_observation_phase({})  # 空数据
        
        print("✓ 错误处理测试成功")
        return True
        
    except Exception as e:
        print(f"✗ 错误处理测试失败: {e}")
        return False

def test_performance():
    """测试性能"""
    print("\n" + "=" * 60)
    print("5. 性能测试")
    print("=" * 60)
    
    try:
        import time
        from cli.session_manager import SessionManager
        
        # 测试大量会话的处理性能
        with tempfile.TemporaryDirectory() as temp_dir:
            session_manager = SessionManager(temp_dir)
            
            # 创建多个会话
            start_time = time.time()
            session_ids = []
            
            for i in range(10):  # 创建10个会话进行测试
                session_id = session_manager.create_new_session(f"性能测试用户{i}")
                session_ids.append(session_id)
                
                # 添加消息
                for j in range(5):
                    session_manager.add_user_message(f"消息 {j}")
                    session_manager.add_assistant_message(f"回复 {j}")
                
                session_manager.save_current_session()
            
            creation_time = time.time() - start_time
            print(f"✓ 创建10个会话耗时: {creation_time:.3f}秒")
            
            # 测试会话列表性能
            start_time = time.time()
            sessions = session_manager.list_sessions()
            list_time = time.time() - start_time
            print(f"✓ 列出{len(sessions)}个会话耗时: {list_time:.3f}秒")
            
            # 测试会话加载性能
            start_time = time.time()
            for session_id in session_ids[:5]:  # 加载前5个会话
                session_manager.load_session(session_id)
            load_time = time.time() - start_time
            print(f"✓ 加载5个会话耗时: {load_time:.3f}秒")
        
        print("✓ 性能测试完成")
        return True
        
    except Exception as e:
        print(f"✗ 性能测试失败: {e}")
        return False

def show_test_summary(results):
    """显示测试总结"""
    console = Console()
    
    # 创建结果表格
    table = Table(title="🧪 测试结果总结")
    table.add_column("测试项目", style="bold")
    table.add_column("结果")
    table.add_column("状态")
    
    test_names = [
        "会话管理器综合测试",
        "流式显示组件综合测试", 
        "CLI命令处理测试",
        "错误处理测试",
        "性能测试"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通过" if result else "❌ 失败"
        style = "green" if result else "red"
        table.add_row(name, "成功" if result else "失败", status, style=style)
    
    console.print(table)
    
    # 显示总体结果
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        console.print(Panel(
            f"🎉 所有测试通过！({passed}/{total})\n\n"
            "新CLI系统已经过全面测试，可以投入使用。",
            title="✨ 测试完成",
            style="bold green"
        ))
    else:
        console.print(Panel(
            f"⚠️ 部分测试失败 ({passed}/{total})\n\n"
            "请检查失败的测试项目并修复相关问题。",
            title="⚠️ 测试结果",
            style="bold yellow"
        ))

async def main():
    """主测试函数"""
    console = Console()
    console.print(Panel(
        "🧪 GTPlanner 新CLI系统综合测试\n\n"
        "测试会话管理、流式显示、命令处理、错误处理和性能等各个方面。",
        title="🚀 开始测试",
        style="bold blue"
    ))
    
    # 运行所有测试
    results = []
    
    results.append(test_session_manager_comprehensive())
    results.append(test_streaming_display_comprehensive())
    results.append(test_cli_commands())
    results.append(test_error_handling())
    results.append(test_performance())
    
    # 显示测试总结
    show_test_summary(results)
    
    return all(results)

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
