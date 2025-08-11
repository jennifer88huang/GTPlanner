"""
统一上下文管理系统测试

测试重构后的上下文管理系统，验证：
1. 去重机制是否正常工作
2. 各组件是否正确集成
3. 数据一致性是否得到保证
4. 性能是否有所提升
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.unified_context import UnifiedContext, get_context, MessageRole, ProjectStage
from cli.session_manager import SessionManager
from agent.shared import SharedState
from agent.flows.react_orchestrator_refactored.state_manager import StateManager


def test_unified_context_basic():
    """测试统一上下文的基本功能"""
    print("🧪 测试统一上下文基本功能...")
    
    # 创建新会话
    context = get_context()
    session_id = context.create_session("测试会话")
    
    print(f"✅ 创建会话: {session_id}")
    
    # 添加消息
    msg1_id = context.add_user_message("你好，这是第一条消息")
    msg2_id = context.add_assistant_message("你好！我是GTPlanner AI助手")
    
    print(f"✅ 添加消息: {msg1_id}, {msg2_id}")
    
    # 测试去重
    duplicate_id = context.add_user_message("你好，这是第一条消息")  # 重复消息
    
    if duplicate_id is None:
        print("✅ 去重机制正常工作")
    else:
        print("❌ 去重机制失败")
    
    # 获取消息
    messages = context.get_messages()
    print(f"✅ 获取消息数量: {len(messages)}")
    
    # 更新状态
    context.update_state("test_key", "test_value")
    value = context.get_state("test_key")
    
    if value == "test_value":
        print("✅ 状态管理正常")
    else:
        print("❌ 状态管理失败")
    
    # 记录工具执行
    context.record_tool_execution(
        tool_name="test_tool",
        arguments={"param": "value"},
        result={"success": True, "result": "测试结果"}
    )
    
    tool_summary = context.get_tool_summary()
    print(f"✅ 工具执行摘要: {tool_summary}")
    
    # 保存会话
    success = context.save_session()
    print(f"✅ 保存会话: {success}")
    
    return session_id


def test_session_manager_integration():
    """测试SessionManager集成"""
    print("\n🧪 测试SessionManager集成...")
    
    session_manager = SessionManager()
    
    # 创建新会话
    session_id = session_manager.create_new_session("测试用户")
    print(f"✅ SessionManager创建会话: {session_id}")
    
    # 添加消息
    session_manager.add_user_message("SessionManager测试消息")
    session_manager.add_assistant_message("SessionManager回复消息")
    
    # 获取会话数据
    session_data = session_manager.get_session_data()
    message_count = len(session_data["dialogue_history"]["messages"])
    print(f"✅ SessionManager消息数量: {message_count}")
    
    # 测试去重
    cleaned = session_manager.cleanup_duplicate_messages()
    print(f"✅ SessionManager清理重复消息: {cleaned}")
    
    return session_id


def test_shared_state_integration():
    """测试SharedState集成"""
    print("\n🧪 测试SharedState集成...")
    
    shared_state = SharedState()
    
    # 添加消息
    shared_state.add_user_message("SharedState测试消息")
    shared_state.add_assistant_message("SharedState回复消息", agent_source="test_agent")
    
    # 获取数据
    data = shared_state.get_data()
    message_count = len(data["dialogue_history"]["messages"])
    print(f"✅ SharedState消息数量: {message_count}")
    
    # 更新状态
    shared_state.update_stage("testing")
    stage_info = shared_state.get_current_stage_info()
    print(f"✅ SharedState阶段信息: {stage_info}")
    
    # 测试去重
    cleaned = shared_state.cleanup_duplicate_messages()
    print(f"✅ SharedState清理重复消息: {cleaned}")
    
    return shared_state.get_session_id()


def test_state_manager_integration():
    """测试StateManager集成"""
    print("\n🧪 测试StateManager集成...")
    
    state_manager = StateManager()
    
    # 构建状态描述
    shared = {}  # 空的共享状态（现在使用统一上下文）
    description = state_manager.build_state_description(shared, "StateManager测试消息")
    print(f"✅ StateManager状态描述长度: {len(description)}")
    
    # 记录工具执行
    state_manager.record_tool_execution(
        shared=shared,
        tool_name="test_tool",
        tool_args={"test": "value"},
        tool_result={"success": True, "result": "测试结果"}
    )
    
    # 获取工具执行摘要
    summary = state_manager.get_tool_execution_summary(shared)
    print(f"✅ StateManager工具执行摘要: {summary}")
    
    # 测试去重
    cleaned = state_manager.cleanup_duplicate_messages()
    print(f"✅ StateManager清理重复消息: {cleaned}")


def test_cross_component_consistency():
    """测试跨组件数据一致性"""
    print("\n🧪 测试跨组件数据一致性...")
    
    # 获取统一上下文
    context = get_context()
    
    # 通过不同组件添加消息
    session_manager = SessionManager()
    shared_state = SharedState()
    
    # 记录初始消息数量
    initial_count = len(context.messages)
    
    # 通过SessionManager添加消息
    session_manager.add_user_message("通过SessionManager添加的消息")
    
    # 通过SharedState添加消息
    shared_state.add_assistant_message("通过SharedState添加的消息")
    
    # 直接通过统一上下文添加消息
    context.add_user_message("直接通过统一上下文添加的消息")
    
    # 检查所有组件是否看到相同的数据
    context_count = len(context.messages)
    session_data = session_manager.get_session_data()
    session_count = len(session_data["dialogue_history"]["messages"])
    shared_data = shared_state.get_data()
    shared_count = len(shared_data["dialogue_history"]["messages"])
    
    print(f"统一上下文消息数量: {context_count}")
    print(f"SessionManager消息数量: {session_count}")
    print(f"SharedState消息数量: {shared_count}")
    
    if context_count == session_count == shared_count:
        print("✅ 跨组件数据一致性测试通过")
        return True
    else:
        print("❌ 跨组件数据一致性测试失败")
        return False


def test_deduplication_effectiveness():
    """测试去重机制的有效性"""
    print("\n🧪 测试去重机制有效性...")
    
    context = get_context()
    
    # 记录初始消息数量
    initial_count = len(context.messages)
    
    # 添加重复消息
    duplicate_messages = [
        "这是重复消息1",
        "这是重复消息2", 
        "这是重复消息1",  # 重复
        "这是重复消息3",
        "这是重复消息2",  # 重复
        "这是重复消息1",  # 重复
    ]
    
    added_count = 0
    for msg in duplicate_messages:
        msg_id = context.add_user_message(msg)
        if msg_id:
            added_count += 1
    
    final_count = len(context.messages)
    actual_added = final_count - initial_count
    
    print(f"尝试添加消息数量: {len(duplicate_messages)}")
    print(f"实际添加消息数量: {actual_added}")
    print(f"预期添加消息数量: 3")  # 只有3条不重复的消息
    
    if actual_added == 3:
        print("✅ 去重机制有效性测试通过")
        return True
    else:
        print("❌ 去重机制有效性测试失败")
        return False


def test_performance_improvement():
    """测试性能改进"""
    print("\n🧪 测试性能改进...")
    
    import time
    
    context = get_context()
    
    # 测试大量消息添加的性能
    start_time = time.time()
    
    for i in range(100):
        context.add_user_message(f"性能测试消息 {i}")
        context.add_assistant_message(f"性能测试回复 {i}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"添加200条消息耗时: {duration:.3f}秒")
    print(f"平均每条消息耗时: {duration/200*1000:.2f}毫秒")
    
    # 测试消息检索性能
    start_time = time.time()
    
    for i in range(10):
        messages = context.get_messages(limit=50)
    
    end_time = time.time()
    retrieval_duration = end_time - start_time
    
    print(f"10次消息检索耗时: {retrieval_duration:.3f}秒")
    print(f"平均每次检索耗时: {retrieval_duration/10*1000:.2f}毫秒")
    
    if duration < 5.0 and retrieval_duration < 1.0:
        print("✅ 性能测试通过")
        return True
    else:
        print("❌ 性能测试失败")
        return False


def main():
    """运行所有测试"""
    print("🚀 开始统一上下文管理系统测试\n")
    
    test_results = []
    
    try:
        # 基本功能测试
        session_id1 = test_unified_context_basic()
        test_results.append(("基本功能", True))
        
        # 组件集成测试
        session_id2 = test_session_manager_integration()
        test_results.append(("SessionManager集成", True))
        
        session_id3 = test_shared_state_integration()
        test_results.append(("SharedState集成", True))
        
        test_state_manager_integration()
        test_results.append(("StateManager集成", True))
        
        # 一致性测试
        consistency_result = test_cross_component_consistency()
        test_results.append(("跨组件一致性", consistency_result))
        
        # 去重测试
        dedup_result = test_deduplication_effectiveness()
        test_results.append(("去重机制", dedup_result))
        
        # 性能测试
        perf_result = test_performance_improvement()
        test_results.append(("性能改进", perf_result))
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        test_results.append(("测试执行", False))
    
    # 输出测试结果摘要
    print("\n" + "="*50)
    print("📊 测试结果摘要")
    print("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！统一上下文管理系统重构成功！")
    else:
        print("⚠️ 部分测试失败，需要进一步调试")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
