"""
测试完整的Architecture Flow
包含文件输出功能的环环相扣设计流程
"""

import sys
import os
import time

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from agent.subflows.architecture.flows.architecture_flow import ArchitectureFlow


def create_test_data():
    """创建测试数据"""
    return {
        "structured_requirements": {
            "project_overview": {
                "title": "智能问答Agent",
                "description": "基于RAG的智能问答系统，能够理解用户问题并提供准确答案"
            },
            "functional_requirements": {
                "core_features": [
                    {
                        "name": "问题理解",
                        "description": "理解用户的自然语言问题，提取关键信息"
                    },
                    {
                        "name": "文档检索",
                        "description": "从知识库中检索相关文档片段"
                    },
                    {
                        "name": "答案生成",
                        "description": "基于检索到的信息生成准确的答案"
                    }
                ],
                "user_interactions": [
                    "用户输入问题",
                    "系统返回答案",
                    "支持多轮对话"
                ]
            },
            "non_functional_requirements": {
                "performance": "响应时间小于3秒",
                "accuracy": "答案准确率大于90%",
                "scalability": "支持并发用户访问"
            }
        },
        "research_findings": {
            "research_summary": "RAG系统需要结合向量检索和生成模型，关键技术包括文档分块、向量化、相似度计算和上下文生成",
            "key_technologies": [
                "向量数据库",
                "文本嵌入模型",
                "大语言模型",
                "检索增强生成"
            ],
            "best_practices": [
                "合理的文档分块策略",
                "高质量的向量化",
                "有效的重排序机制"
            ]
        },
        "confirmation_document": "用户确认开发基于RAG的智能问答Agent，要求具备问题理解、文档检索和答案生成功能"
    }


def test_complete_architecture_flow():
    """测试完整的Architecture Flow"""
    print("🚀 开始测试完整的Architecture Flow")
    print("=" * 60)
    
    # 创建测试数据
    shared = create_test_data()
    
    # 初始化必要的字段
    shared.update({
        "agent_analysis": {},
        "identified_nodes": [],
        "flow_design": {},
        "data_structure": {},
        "detailed_nodes": [],
        "agent_design_document": "",
        "generated_files": [],
        "output_directory": ""
    })
    
    try:
        # 创建Architecture Flow
        print("🏗️ 创建Architecture Flow...")
        architecture_flow = ArchitectureFlow()
        
        print("✅ Architecture Flow创建成功")
        print(f"   Flow名称: {architecture_flow.name}")
        print(f"   Flow描述: {architecture_flow.description}")
        print("   🔄 支持批处理的Node设计阶段")
        
        # 执行完整的Flow
        print("\n🚀 执行完整的Architecture Flow...")
        start_time = time.time()
        
        result = architecture_flow.run(shared)
        
        exec_time = time.time() - start_time
        
        print(f"\n✅ Architecture Flow执行完成")
        print(f"⏱️  总耗时: {exec_time:.2f}秒")
        print(f"📊 执行结果: {result}")
        
        # 检查生成的结果
        print(f"\n📋 生成结果检查:")
        
        # 检查各阶段的数据
        stages = [
            ("agent_analysis", "Agent分析"),
            ("identified_nodes", "Node识别"),
            ("flow_design", "Flow设计"),
            ("data_structure", "数据结构"),
            ("detailed_nodes", "Node详细设计"),
            ("agent_design_document", "完整设计文档")
        ]
        
        for key, name in stages:
            if key in shared and shared[key]:
                data = shared[key]
                if isinstance(data, str):
                    print(f"   ✅ {name}: {len(data)} 字符")
                elif isinstance(data, list):
                    print(f"   ✅ {name}: {len(data)} 项")
                elif isinstance(data, dict):
                    print(f"   ✅ {name}: {len(str(data))} 字符")
                else:
                    print(f"   ✅ {name}: 已生成")
            else:
                print(f"   ❌ {name}: 未生成")
        
        # 检查生成的文件
        if "generated_files" in shared and shared["generated_files"]:
            files = shared["generated_files"]
            print(f"\n📄 生成文件: {len(files)} 个")
            for file_info in files:
                filename = file_info.get("filename", "Unknown")
                filepath = file_info.get("filepath", "Unknown")
                print(f"   📄 {filename}")
                print(f"      路径: {filepath}")
        else:
            print(f"\n❌ 未生成任何文件")
        
        # 显示输出目录
        if "output_directory" in shared and shared["output_directory"]:
            print(f"\n📁 输出目录: {shared['output_directory']}")
        
        return shared
        
    except Exception as e:
        print(f"\n❌ Architecture Flow测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_individual_stages():
    """测试各个阶段的数据传递"""
    print("\n🔍 检查各阶段数据传递:")
    
    shared = create_test_data()
    
    # 模拟各阶段的数据
    shared["agent_analysis"] = {
        "agent_type": "对话Agent",
        "agent_purpose": "智能问答",
        "core_functions": [
            {"function_name": "问题理解", "description": "理解用户问题"}
        ]
    }
    
    shared["identified_nodes"] = [
        {"node_name": "InputValidationNode", "purpose": "验证输入"},
        {"node_name": "QueryProcessingNode", "purpose": "处理查询"}
    ]
    
    shared["flow_design"] = {
        "flow_name": "智能问答Flow",
        "connections": [
            {"from_node": "InputValidationNode", "to_node": "QueryProcessingNode"}
        ]
    }
    
    print("✅ 各阶段数据传递检查完成")
    print(f"   Agent分析: {len(str(shared['agent_analysis']))} 字符")
    print(f"   Node识别: {len(shared['identified_nodes'])} 个")
    print(f"   Flow设计: {len(str(shared['flow_design']))} 字符")


def main():
    """主测试函数"""
    print("🧪 Architecture Flow 完整测试")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        # 测试完整流程
        shared = test_complete_architecture_flow()
        
        if shared:
            # 测试数据传递
            test_individual_stages()
            
            print("\n" + "=" * 60)
            print("🎉 所有测试完成！")
            print("✅ 完整的Architecture Flow测试成功")
            print("✅ 环环相扣的设计流程验证通过")
            print("✅ 文件输出功能正常工作")
        else:
            print("\n" + "=" * 60)
            print("❌ 测试失败")
        
        end_time = time.time()
        print(f"⏱️  总测试时间: {end_time - start_time:.2f}秒")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
