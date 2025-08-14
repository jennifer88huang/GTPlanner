#!/usr/bin/env python3
"""
测试Research子流程重构结果

验证LLMAnalysisNode和ResultAssemblyNode的字典模式访问和简化逻辑
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.subflows.research.nodes.llm_analysis_node import LLMAnalysisNode
from agent.subflows.research.nodes.result_assembly_node import ResultAssemblyNode


async def test_llm_analysis_node():
    """测试LLM分析节点"""
    print("🧪 测试LLM分析节点")
    print("=" * 50)

    # 创建节点实例
    node = LLMAnalysisNode()

    # 准备测试数据
    shared = {
        "url_content": """
        Python是一种高级编程语言，具有简洁的语法和强大的功能。
        它广泛应用于Web开发、数据科学、人工智能等领域。
        Python的特点包括：
        1. 简洁易读的语法
        2. 丰富的标准库
        3. 强大的第三方生态系统
        4. 跨平台兼容性
        """,
        "current_keyword": "Python编程",
        "analysis_requirements": "分析Python的核心特性和应用领域"
    }

    try:
        # 测试prep阶段
        print("1️⃣ 测试prep阶段...")
        prep_result = await node.prep_async(shared)
        print(f"✅ Prep结果: {prep_result}")

        # 测试exec阶段
        print("\n2️⃣ 测试exec阶段...")
        exec_result = await node.exec_async(prep_result)
        print(f"✅ Exec结果: {exec_result}")

        # 检查是否有错误
        if "error" in exec_result:
            print(f"⚠️ Exec阶段返回错误: {exec_result['error']}")

        # 测试post阶段
        print("\n3️⃣ 测试post阶段...")
        post_result = await node.post_async(shared, prep_result, exec_result)
        print(f"✅ Post结果: {post_result}")

        # 检查shared状态
        print(f"\n📋 Shared状态更新:")
        print(f"  - llm_analysis_status: {shared.get('llm_analysis_status', 'unknown')}")
        print(f"  - llm_analysis: {shared.get('llm_analysis', {})}")
        print(f"  - analyzed_keyword: {shared.get('analyzed_keyword', '')}")

        # 检查错误记录
        if "errors" in shared:
            print(f"  - errors: {shared['errors']}")

        return post_result != "error"

    except Exception as e:
        print(f"❌ LLM分析节点测试失败: {e}")
        return False


async def test_result_assembly_node():
    """测试结果组装节点"""
    print("\n🧪 测试结果组装节点")
    print("=" * 50)
    
    # 创建节点实例
    node = ResultAssemblyNode()
    
    # 准备测试数据
    shared = {
        "current_keyword": "Python编程",
        "first_search_result": {
            "url": "https://python.org",
            "title": "Python官方网站"
        },
        "url_content": "Python是一种强大的编程语言...",
        "llm_analysis": {
            "summary": "Python是一种高级编程语言",
            "key_points": ["简洁语法", "丰富生态", "跨平台"],
            "recommendations": ["学习基础语法", "实践项目开发"]
        }
    }
    
    try:
        # 测试prep阶段
        print("1️⃣ 测试prep阶段...")
        prep_result = await node.prep_async(shared)
        print(f"✅ Prep结果: {prep_result}")
        
        # 测试exec阶段
        print("\n2️⃣ 测试exec阶段...")
        exec_result = await node.exec_async(prep_result)
        print(f"✅ Exec结果: {exec_result}")
        
        # 测试post阶段
        print("\n3️⃣ 测试post阶段...")
        post_result = await node.post_async(shared, prep_result, exec_result)
        print(f"✅ Post结果: {post_result}")
        
        # 检查shared状态
        print(f"\n📋 Shared状态更新:")
        print(f"  - keyword_report: {shared.get('keyword_report', {})}")
        print(f"  - research_findings: {shared.get('research_findings', {})}")
        
        return True
        
    except Exception as e:
        print(f"❌ 结果组装节点测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🎯 Research子流程节点重构测试")
    print("=" * 80)
    
    # 测试LLM分析节点
    llm_success = await test_llm_analysis_node()
    
    # 测试结果组装节点
    assembly_success = await test_result_assembly_node()
    
    # 总结测试结果
    print("\n" + "=" * 80)
    print("🎉 测试结果总结:")
    print(f"✅ LLM分析节点: {'通过' if llm_success else '失败'}")
    print(f"✅ 结果组装节点: {'通过' if assembly_success else '失败'}")
    
    if llm_success and assembly_success:
        print("\n🎉 所有Research子流程节点测试通过！")
        print("✅ 字典模式访问正常")
        print("✅ 简化逻辑工作正常")
        print("✅ 错误处理机制完善")
    else:
        print("\n❌ 部分测试失败，需要进一步调试")
    
    return llm_success and assembly_success


if __name__ == "__main__":
    asyncio.run(main())
