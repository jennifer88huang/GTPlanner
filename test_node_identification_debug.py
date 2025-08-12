#!/usr/bin/env python3
"""
测试Node识别的调试信息
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_node_identification_debug():
    """测试Node识别的调试信息"""
    print("🔍 测试Node识别调试信息")
    print("=" * 50)
    
    try:
        # 测试architecture_design工具
        from agent.function_calling.agent_tools import execute_agent_tool
        
        # 准备测试数据
        arguments = {
            "structured_requirements": {
                "project_name": "YouTube视频解析智能体",
                "main_functionality": "解析YouTube视频内容",
                "input_format": "YouTube URL",
                "output_format": "视频信息和内容摘要"
            }
        }
        
        print("   开始执行architecture_design工具...")
        result = await execute_agent_tool("architecture_design", arguments)
        
        print(f"\n📊 最终结果:")
        print(f"   执行成功: {result.get('success', False)}")
        if result.get('success'):
            print(f"   工具名称: {result.get('tool_name')}")
            design_doc = result.get('result', {})
            print(f"   设计文档类型: {type(design_doc)}")
        else:
            print(f"   错误信息: {result.get('error')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_node_identification_debug())
