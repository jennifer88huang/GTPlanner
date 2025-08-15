#!/usr/bin/env python3
"""
调试消息格式问题

检查数据库中的消息格式，找出为什么会出现<tool_call>格式的消息。
"""

import sys
import os
import sqlite3

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def debug_message_format():
    """调试消息格式"""
    print("🔍 调试消息格式...")
    
    try:
        # 连接到默认数据库
        db_path = "gtplanner_conversations.db"
        if not os.path.exists(db_path):
            print(f"❌ 数据库文件不存在: {db_path}")
            return False
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # 获取最近的会话
        cursor = conn.execute("""
            SELECT session_id, title, created_at
            FROM sessions 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        sessions = cursor.fetchall()
        print(f"✅ 找到 {len(sessions)} 个最近的会话")
        
        for i, session in enumerate(sessions):
            print(f"\n📋 会话{i+1}: {session['title']} ({session['session_id'][:8]}...)")
            
            # 获取该会话的消息
            cursor = conn.execute("""
                SELECT role, content, tool_calls, tool_call_id, timestamp
                FROM messages 
                WHERE session_id = ?
                ORDER BY timestamp
            """, (session['session_id'],))
            
            messages = cursor.fetchall()
            print(f"   消息数量: {len(messages)}")
            
            for j, msg in enumerate(messages):
                role = msg['role']
                content = msg['content']
                tool_calls = msg['tool_calls']
                tool_call_id = msg['tool_call_id']
                
                print(f"   消息{j+1}: {role}")
                
                # 检查是否包含<tool_call>格式
                if '<tool_call>' in content:
                    print(f"     ⚠️ 发现<tool_call>格式: {content[:100]}...")
                
                # 检查tool消息的tool_call_id
                if role == 'tool':
                    if not tool_call_id:
                        print(f"     ❌ tool消息缺少tool_call_id")
                    else:
                        print(f"     ✅ tool消息有tool_call_id: {tool_call_id}")
                
                # 检查assistant消息的tool_calls
                if role == 'assistant' and tool_calls:
                    print(f"     ✅ assistant消息有tool_calls: {tool_calls[:100]}...")
                
                # 显示内容摘要
                if len(content) > 100:
                    print(f"     内容: {content[:100]}...")
                else:
                    print(f"     内容: {content}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_pocketflow_factory():
    """检查PocketFlowSharedFactory的消息格式"""
    print("\n🔍 检查PocketFlowSharedFactory的消息格式...")
    
    try:
        from agent.context_types import create_user_message, create_assistant_message, create_tool_message
        from agent.pocketflow_factory import PocketFlowSharedFactory
        from agent.context_types import AgentContext
        
        # 创建模拟的消息历史
        dialogue_history = [
            create_user_message("你好"),
            create_assistant_message("你好！", tool_calls=[{
                "id": "call_123", 
                "type": "function", 
                "function": {"name": "test_tool", "arguments": "{}"}
            }]),
            create_tool_message('{"success": true, "result": "测试结果"}', "call_123"),
            create_assistant_message("完成了")
        ]
        
        context = AgentContext(
            session_id="test-session",
            dialogue_history=dialogue_history,
            tool_execution_results={},
            session_metadata={}
        )
        
        # 创建shared字典
        shared = PocketFlowSharedFactory.create_shared_dict("新的用户输入", context)
        
        # 检查消息格式
        messages = shared["dialogue_history"]["messages"]
        print(f"✅ 生成的消息数量: {len(messages)}")
        
        for i, msg in enumerate(messages):
            print(f"   消息{i+1}: {msg['role']}")
            
            # 检查是否有<tool_call>格式
            if '<tool_call>' in msg.get('content', ''):
                print(f"     ❌ 发现<tool_call>格式: {msg['content'][:100]}...")
                return False
            
            # 检查OpenAI标准字段
            if msg['role'] == 'assistant' and 'tool_calls' in msg:
                print(f"     ✅ assistant消息有tool_calls字段")
            
            if msg['role'] == 'tool' and 'tool_call_id' in msg:
                print(f"     ✅ tool消息有tool_call_id字段: {msg['tool_call_id']}")
            
            print(f"     内容: {msg['content'][:50]}...")
        
        print(f"✅ PocketFlowSharedFactory消息格式正确")
        return True
        
    except Exception as e:
        print(f"❌ PocketFlowSharedFactory检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("🚀 开始消息格式调试")
    print("=" * 60)
    
    tests = [
        ("数据库消息格式检查", debug_message_format),
        ("PocketFlowSharedFactory格式检查", check_pocketflow_factory)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            print(f"{'✅' if result else '❌'} {name}: {'通过' if result else '失败'}")
        except Exception as e:
            print(f"❌ {name}: 异常 - {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 调试总结:")
    
    for name, result in results:
        print(f"   {'✅' if result else '❌'} {name}")
    
    if all(result for _, result in results):
        print("\n🎉 所有检查通过！")
        print("\n💡 如果LLM仍然输出<tool_call>格式，可能的原因:")
        print("   1. 系统提示词中包含了错误的示例")
        print("   2. LLM模型本身的问题")
        print("   3. 需要清理历史会话数据")
    else:
        print("\n⚠️ 发现问题，需要修复")
    
    return all(result for _, result in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
