#!/usr/bin/env python3
"""
测试修复后的short_planning工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_short_planning_fix():
    """测试修复后的short_planning工具"""
    print("🔧 测试修复后的short_planning工具")
    print("=" * 50)
    
    # 1. 测试工具调用
    print("\n📝 测试1: 直接调用short_planning工具")
    from agent.function_calling.agent_tools import execute_agent_tool
    
    arguments = {
        "user_requirements": "我需要一个可以解析YouTube视频的智能体，用户只需要提供一个URL就可以了。"
    }
    
    try:
        result = await execute_agent_tool("short_planning", arguments)
        
        print(f"   执行成功: {result.get('success', False)}")
        if result.get('success'):
            print(f"   工具名称: {result.get('tool_name')}")
            planning_doc = result.get('result', {})
            if isinstance(planning_doc, str):
                print(f"   规划文档长度: {len(planning_doc)} 字符")
                print(f"   规划文档预览: {planning_doc[:100]}...")
            else:
                print(f"   规划文档类型: {type(planning_doc)}")
        else:
            print(f"   错误信息: {result.get('error')}")
            
    except Exception as e:
        print(f"   异常: {e}")
        import traceback
        traceback.print_exc()
    
    # 2. 测试便捷函数
    print("\n🚀 测试2: 使用便捷函数")
    from agent.function_calling.agent_tools import call_short_planning
    
    try:
        result = await call_short_planning(
            user_requirements="创建一个简单的Python Web应用"
        )
        
        print(f"   便捷函数执行成功: {result.get('success', False)}")
        if result.get('success'):
            planning_doc = result.get('result', {})
            if isinstance(planning_doc, str):
                print(f"   规划文档长度: {len(planning_doc)} 字符")
            else:
                print(f"   规划文档类型: {type(planning_doc)}")
        else:
            print(f"   错误信息: {result.get('error')}")
            
    except Exception as e:
        print(f"   异常: {e}")
    
    # 3. 测试参数验证
    print("\n❌ 测试3: 参数验证")
    
    try:
        # 测试缺少必需参数
        result = await execute_agent_tool("short_planning", {})
        print(f"   缺少参数测试: {result.get('success', False)}")
        print(f"   错误信息: {result.get('error')}")
        
    except Exception as e:
        print(f"   异常: {e}")
    
    print(f"\n🎉 short_planning工具测试完成！")


if __name__ == "__main__":
    asyncio.run(test_short_planning_fix())
