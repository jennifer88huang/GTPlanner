#!/usr/bin/env python3
"""
测试修复后的工具
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_fixed_tools():
    """测试修复后的工具"""
    print("🔧 测试修复后的工具")
    print("=" * 50)
    
    # 1. 测试short_planning工具
    print("\n📝 测试1: short_planning工具")
    from agent.function_calling.agent_tools import execute_agent_tool
    
    try:
        result = await execute_agent_tool("short_planning", {
            "user_requirements": "我需要一个YouTube视频解析智能体"
        })
        
        print(f"   short_planning成功: {result.get('success', False)}")
        if result.get('success'):
            planning_doc = result.get('result', '')
            print(f"   规划文档长度: {len(planning_doc)} 字符")
        else:
            print(f"   错误: {result.get('error')}")
            
    except Exception as e:
        print(f"   异常: {e}")
    
    # 2. 测试architecture_design工具（使用明确的字段结构）
    print("\n🏗️ 测试2: architecture_design工具")
    
    try:
        result = await execute_agent_tool("architecture_design", {
            "structured_requirements": {
                "project_name": "YouTube视频解析智能体",
                "main_functionality": "解析YouTube视频内容并提取信息",
                "input_format": "YouTube URL",
                "output_format": "视频信息和内容摘要",
                "technical_requirements": ["Python", "YouTube API", "视频处理"]
            }
        })
        
        print(f"   architecture_design成功: {result.get('success', False)}")
        if result.get('success'):
            design_doc = result.get('result', {})
            print(f"   设计文档类型: {type(design_doc)}")
        else:
            print(f"   错误: {result.get('error')}")
            
    except Exception as e:
        print(f"   异常: {e}")
    
    # 3. 测试research工具
    print("\n🔍 测试3: research工具")
    
    try:
        result = await execute_agent_tool("research", {
            "keywords": ["YouTube API", "视频处理", "Python"],
            "focus_areas": ["技术选型", "最佳实践"],
            "project_context": "YouTube视频解析智能体项目"
        })
        
        print(f"   research成功: {result.get('success', False)}")
        if result.get('success'):
            research_findings = result.get('result', {})
            print(f"   调研结果类型: {type(research_findings)}")
            print(f"   处理的关键词数: {result.get('keywords_processed', 0)}")
        else:
            print(f"   错误: {result.get('error')}")
            
    except Exception as e:
        print(f"   异常: {e}")
    
    print(f"\n🎉 工具测试完成！")


if __name__ == "__main__":
    asyncio.run(test_fixed_tools())
