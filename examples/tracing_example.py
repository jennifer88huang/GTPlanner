#!/usr/bin/env python3
"""
GTPlanner Tracing Example

演示如何在GTPlanner的Flow中集成pocketflow-tracing。
这个示例展示了如何为现有的Flow添加tracing功能。
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pocketflow import AsyncFlow, AsyncNode
from pocketflow_tracing import trace_flow, TracingConfig


class ExampleAnalysisNode(AsyncNode):
    """示例分析节点"""
    
    def __init__(self):
        super().__init__()
        self.name = "ExampleAnalysisNode"
        self.description = "分析用户需求并提取关键信息"
    
    async def prep_async(self, shared):
        """准备阶段：提取用户需求"""
        user_requirement = shared.get("user_requirement", "")
        if not user_requirement:
            return {"error": "缺少用户需求"}
        
        return {
            "requirement": user_requirement,
            "analysis_type": "basic"
        }
    
    async def exec_async(self, prep_result):
        """执行阶段：分析需求"""
        if "error" in prep_result:
            return prep_result
        
        requirement = prep_result["requirement"]
        
        # 模拟分析过程
        await asyncio.sleep(0.1)
        
        analysis_result = {
            "project_type": "web_application",
            "complexity": "medium",
            "estimated_duration": "2-3 months",
            "key_features": [
                "用户管理",
                "数据存储",
                "API接口"
            ],
            "technology_stack": [
                "Python",
                "FastAPI",
                "PostgreSQL"
            ]
        }
        
        return {
            "analysis": analysis_result,
            "confidence": 0.85,
            "status": "success"
        }
    
    async def post_async(self, shared, prep_result, exec_result):
        """后处理阶段：保存分析结果"""
        if "error" in exec_result:
            shared["analysis_error"] = exec_result["error"]
            return "error"
        
        shared["requirement_analysis"] = exec_result["analysis"]
        shared["analysis_confidence"] = exec_result["confidence"]
        
        print(f"✅ 需求分析完成，置信度: {exec_result['confidence']}")
        return "analysis_complete"


class ExamplePlanningNode(AsyncNode):
    """示例规划节点"""
    
    def __init__(self):
        super().__init__()
        self.name = "ExamplePlanningNode"
        self.description = "基于分析结果生成项目规划"
    
    async def prep_async(self, shared):
        """准备阶段：获取分析结果"""
        analysis = shared.get("requirement_analysis")
        if not analysis:
            return {"error": "缺少需求分析结果"}
        
        return {
            "analysis": analysis,
            "planning_mode": "detailed"
        }
    
    async def exec_async(self, prep_result):
        """执行阶段：生成规划"""
        if "error" in prep_result:
            return prep_result
        
        analysis = prep_result["analysis"]
        
        # 模拟规划生成过程
        await asyncio.sleep(0.2)
        
        planning_result = {
            "phases": [
                {
                    "name": "需求分析",
                    "duration": "1周",
                    "deliverables": ["需求文档", "原型设计"]
                },
                {
                    "name": "系统设计",
                    "duration": "2周",
                    "deliverables": ["架构设计", "数据库设计"]
                },
                {
                    "name": "开发实现",
                    "duration": "6周",
                    "deliverables": ["核心功能", "API接口"]
                },
                {
                    "name": "测试部署",
                    "duration": "2周",
                    "deliverables": ["测试报告", "部署文档"]
                }
            ],
            "total_duration": analysis.get("estimated_duration", "未知"),
            "risk_assessment": "中等风险",
            "resource_requirements": {
                "developers": 2,
                "designers": 1,
                "testers": 1
            }
        }
        
        return {
            "planning": planning_result,
            "status": "success"
        }
    
    async def post_async(self, shared, prep_result, exec_result):
        """后处理阶段：保存规划结果"""
        if "error" in exec_result:
            shared["planning_error"] = exec_result["error"]
            return "error"
        
        shared["project_planning"] = exec_result["planning"]
        
        print("✅ 项目规划生成完成")
        return "planning_complete"


@trace_flow(flow_name="GTPlannerExampleFlow")
class GTPlannerExampleFlow(AsyncFlow):
    """带有tracing的GTPlanner示例流程"""
    
    async def prep_async(self, shared):
        """流程级准备"""
        print("🚀 启动GTPlanner示例流程...")
        shared["flow_start_time"] = asyncio.get_event_loop().time()
        
        return {
            "flow_id": shared.get("flow_id", "example_flow"),
            "start_time": shared["flow_start_time"]
        }
    
    async def post_async(self, shared, prep_result, exec_result):
        """流程级后处理"""
        flow_duration = asyncio.get_event_loop().time() - prep_result["start_time"]
        
        shared["flow_metadata"] = {
            "flow_id": prep_result["flow_id"],
            "duration": flow_duration,
            "status": "completed",
            "nodes_executed": 2
        }
        
        print(f"✅ 流程完成，耗时: {flow_duration:.2f}秒")
        return exec_result


def create_gtplanner_example_flow():
    """创建GTPlanner示例流程"""
    # 创建节点
    analysis_node = ExampleAnalysisNode()
    planning_node = ExamplePlanningNode()
    
    # 连接节点
    analysis_node - "analysis_complete" >> planning_node
    
    # 创建流程
    flow = GTPlannerExampleFlow()
    flow.start_node = analysis_node
    
    return flow


async def main():
    """运行tracing示例"""
    print("🎯 GTPlanner Tracing 示例")
    print("=" * 50)
    
    # 检查tracing配置
    try:
        config = TracingConfig.from_env()
        if not config.validate():
            print("⚠️  警告: Langfuse配置不完整，tracing可能无法正常工作")
            print("请检查.env文件中的LANGFUSE_*配置项")
        else:
            print("✅ Tracing配置验证成功")
    except Exception as e:
        print(f"⚠️  Tracing配置错误: {e}")
    
    # 创建流程
    flow = create_gtplanner_example_flow()
    
    # 准备测试数据
    shared = {
        "user_requirement": "我需要开发一个在线教育平台，包含用户管理、课程管理、在线学习等功能",
        "flow_id": "gtplanner_example"
    }
    
    print(f"📥 输入需求: {shared['user_requirement']}")
    
    try:
        # 运行流程（会自动进行tracing）
        result = await flow.run_async(shared)
        
        print(f"\n📤 流程结果: {result}")
        
        # 显示分析结果
        if "requirement_analysis" in shared:
            analysis = shared["requirement_analysis"]
            print(f"\n📊 需求分析结果:")
            print(f"   项目类型: {analysis['project_type']}")
            print(f"   复杂度: {analysis['complexity']}")
            print(f"   预估时长: {analysis['estimated_duration']}")
            print(f"   关键功能: {', '.join(analysis['key_features'])}")
        
        # 显示规划结果
        if "project_planning" in shared:
            planning = shared["project_planning"]
            print(f"\n📋 项目规划:")
            print(f"   总时长: {planning['total_duration']}")
            print(f"   风险评估: {planning['risk_assessment']}")
            print(f"   阶段数量: {len(planning['phases'])}")
        
        # 显示流程元数据
        if "flow_metadata" in shared:
            metadata = shared["flow_metadata"]
            print(f"\n⏱️  流程元数据:")
            print(f"   流程ID: {metadata['flow_id']}")
            print(f"   执行时长: {metadata['duration']:.2f}秒")
            print(f"   节点数量: {metadata['nodes_executed']}")
        
        print("\n🎉 示例执行成功！")
        
    except Exception as e:
        print(f"❌ 流程执行失败: {e}")
        raise
    
    # 显示tracing信息
    print("\n📊 Tracing信息:")
    langfuse_host = os.getenv("LANGFUSE_HOST", "your-langfuse-host")
    print(f"   查看详细trace: {langfuse_host}")
    print("   在Langfuse仪表板中可以看到完整的执行轨迹")


if __name__ == "__main__":
    asyncio.run(main())
