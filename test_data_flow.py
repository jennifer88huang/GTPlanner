#!/usr/bin/env python3
"""
测试优化后的单向数据流

验证：统一消息管理层 → Agent层(工厂创建) → pocketflow
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_data_flow():
    """测试单向数据流"""
    print("🔄 测试优化后的单向数据流")
    print("=" * 50)
    
    # 1. 模拟CLI层：只与统一消息管理层交互
    print("\n📱 步骤1: CLI层 → 统一消息管理层")
    from core.unified_context import get_context
    context = get_context()
    
    session_id = context.create_session("数据流测试")
    context.add_user_message("测试单向数据流")
    
    print(f"   会话ID: {session_id}")
    print(f"   统一消息管理层消息数: {len(context.messages)}")
    print(f"   统一消息管理层LLM上下文数: {len(context.llm_context)}")
    
    # 2. 模拟Agent层：使用工厂模式从统一消息管理层获取数据
    print("\n🤖 步骤2: Agent层 ← 统一消息管理层（工厂模式）")
    from agent.shared import SharedStateFactory
    
    # 使用工厂模式创建独立实例
    shared_state = SharedStateFactory.create_from_unified_context()
    
    print(f"   SharedState会话ID: {shared_state.session_id}")
    print(f"   SharedState消息数: {len(shared_state.get_dialogue_history().get('messages', []))}")
    
    # 3. 转换为pocketflow格式
    print("\n⚙️ 步骤3: Agent层 → pocketflow")
    pocketflow_data = shared_state.to_pocketflow_shared({"_stream_callback": None})
    
    print(f"   pocketflow消息数: {len(pocketflow_data.get('dialogue_history', {}).get('messages', []))}")
    print(f"   pocketflow当前阶段: {pocketflow_data.get('current_stage')}")
    
    # 4. 验证数据一致性
    print("\n✅ 步骤4: 验证数据一致性")
    original_msg_count = len(context.llm_context)
    shared_msg_count = len(shared_state.get_dialogue_history().get('messages', []))
    pocketflow_msg_count = len(pocketflow_data.get('dialogue_history', {}).get('messages', []))
    
    print(f"   统一消息管理层: {original_msg_count} 条消息")
    print(f"   SharedState: {shared_msg_count} 条消息")
    print(f"   pocketflow: {pocketflow_msg_count} 条消息")
    
    consistency_check = (original_msg_count == shared_msg_count == pocketflow_msg_count)
    print(f"   数据一致性: {'✅ 通过' if consistency_check else '❌ 失败'}")
    
    # 5. 测试Agent Flow完整流程
    print("\n🚀 步骤5: 完整Agent Flow测试")
    from agent.flows.react_orchestrator_refactored import ReActOrchestratorFlow
    
    orchestrator = ReActOrchestratorFlow()
    
    try:
        result = await orchestrator.run_async({"_stream_callback": None})
        print(f"   Agent Flow结果: {result}")
        print("   ✅ 单向数据流完整测试通过")
    except Exception as e:
        print(f"   ❌ Agent Flow测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 6. 验证最终状态
    print("\n📊 步骤6: 最终状态验证")
    final_msg_count = len(context.messages)
    final_llm_count = len(context.llm_context)
    
    print(f"   最终完整消息数: {final_msg_count}")
    print(f"   最终LLM上下文数: {final_llm_count}")
    print(f"   消息增长: {'✅ 正常' if final_msg_count > original_msg_count else '❌ 异常'}")


if __name__ == "__main__":
    asyncio.run(test_data_flow())
