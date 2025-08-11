#!/usr/bin/env python3
"""
GTPlanner Tracing 测试脚本

测试GTPlanner中各个Flow的tracing功能是否正常工作。
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

from pocketflow_tracing import TracingConfig


async def test_tracing_config():
    """测试tracing配置"""
    print("🔧 测试Tracing配置...")
    
    try:
        config = TracingConfig.from_env()
        
        print(f"   Langfuse Host: {config.langfuse_host}")
        print(f"   Debug模式: {config.debug}")
        print(f"   追踪输入: {config.trace_inputs}")
        print(f"   追踪输出: {config.trace_outputs}")
        
        if config.validate():
            print("✅ Tracing配置验证成功")
            return True
        else:
            print("❌ Tracing配置验证失败")
            print("   请检查.env文件中的LANGFUSE_*配置项")
            return False
            
    except Exception as e:
        print(f"❌ Tracing配置错误: {e}")
        return False


async def test_short_planning_flow():
    """测试短规划流程的tracing"""
    print("\n📋 测试ShortPlanningFlow tracing...")
    
    try:
        from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow
        
        # 创建Flow实例
        flow = ShortPlanningFlow()
        
        # 准备测试数据
        shared = {
            "structured_requirements": {
                "project_overview": {
                    "title": "在线教育平台",
                    "description": "一个包含用户管理、课程管理、在线学习等功能的教育平台"
                },
                "functional_requirements": {
                    "core_features": [
                        "用户注册登录",
                        "课程浏览",
                        "在线学习",
                        "进度跟踪"
                    ]
                }
            }
        }
        
        print("   运行短规划流程...")
        result = await flow.run_async(shared)
        
        print(f"✅ ShortPlanningFlow测试成功")
        print(f"   结果: {result}")
        
        # 检查流程元数据
        if "flow_metadata" in shared:
            metadata = shared["flow_metadata"]
            print(f"   执行时长: {metadata.get('duration', 0):.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ ShortPlanningFlow测试失败: {e}")
        return False


async def test_research_flow():
    """测试研究流程的tracing"""
    print("\n🔍 测试ResearchFlow tracing...")
    
    try:
        from agent.subflows.research.flows.research_flow import ResearchFlow
        
        # 创建Flow实例
        flow = ResearchFlow()
        
        # 准备测试数据
        shared = {
            "structured_requirements": {
                "project_overview": {
                    "title": "电商平台",
                    "description": "一个完整的电商平台，包含商品管理、订单处理、支付系统等功能"
                }
            }
        }
        
        print("   运行研究调研流程...")
        result = await flow.run_async(shared)
        
        print(f"✅ ResearchFlow测试成功")
        print(f"   结果: {result}")
        
        # 检查流程元数据
        if "flow_metadata" in shared:
            metadata = shared["flow_metadata"]
            print(f"   执行时长: {metadata.get('duration', 0):.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ ResearchFlow测试失败: {e}")
        return False


async def test_architecture_flow():
    """测试架构流程的tracing"""
    print("\n🏗️ 测试ArchitectureFlow tracing...")
    
    try:
        from agent.subflows.architecture.flows.architecture_flow import create_architecture_flow
        
        # 创建Flow实例
        flow = create_architecture_flow()
        
        # 准备测试数据
        shared = {
            "structured_requirements": {
                "project_overview": {
                    "title": "内容管理系统",
                    "description": "一个灵活的内容管理系统，支持多种内容类型和用户权限管理"
                },
                "functional_requirements": {
                    "core_features": [
                        "内容创建编辑",
                        "用户权限管理",
                        "内容发布",
                        "搜索功能"
                    ]
                }
            }
        }
        
        print("   运行架构设计流程...")
        result = await flow.run_async(shared)
        
        print(f"✅ ArchitectureFlow测试成功")
        print(f"   结果: {result}")
        
        # 检查流程元数据
        if "flow_metadata" in shared:
            metadata = shared["flow_metadata"]
            print(f"   执行时长: {metadata.get('duration', 0):.2f}秒")
        
        return True
        
    except Exception as e:
        print(f"❌ ArchitectureFlow测试失败: {e}")
        return False


async def main():
    """运行所有tracing测试"""
    print("🎯 GTPlanner Tracing 功能测试")
    print("=" * 50)
    
    # 测试配置
    config_ok = await test_tracing_config()
    
    if not config_ok:
        print("\n⚠️  Tracing配置有问题，但仍会继续测试Flow功能")
    
    # 测试各个Flow
    test_results = []
    
    # 测试短规划流程
    result1 = await test_short_planning_flow()
    test_results.append(("ShortPlanningFlow", result1))
    
    # 测试研究流程
    result2 = await test_research_flow()
    test_results.append(("ResearchFlow", result2))
    
    # 测试架构流程
    result3 = await test_architecture_flow()
    test_results.append(("ArchitectureFlow", result3))
    
    # 显示测试结果
    print("\n📊 测试结果汇总:")
    print("-" * 30)
    
    success_count = 0
    for flow_name, success in test_results:
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {flow_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n总计: {success_count}/{len(test_results)} 个Flow测试通过")
    
    if config_ok and success_count > 0:
        print("\n🎉 Tracing功能测试完成！")
        langfuse_host = os.getenv("LANGFUSE_HOST", "your-langfuse-host")
        print(f"   查看详细trace: {langfuse_host}")
        print("   在Langfuse仪表板中可以看到完整的执行轨迹")
    elif success_count > 0:
        print("\n⚠️  Flow功能正常，但Tracing配置需要检查")
    else:
        print("\n❌ 测试失败，请检查代码和配置")


if __name__ == "__main__":
    asyncio.run(main())
