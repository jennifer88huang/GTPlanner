"""
Requirements Analysis Agent 完整测试

基于pocketflow最佳实践的完整测试，验证Requirements Analysis Agent的所有功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from agent.subflows.requirements_analysis import (
    RequirementsAnalysisFlow,
    ProcessRequirementsNode,
    LLMStructureNode,
    ValidationNode
)
from agent.nodes.node_req import NodeReq


def test_imports_and_initialization():
    """测试导入和初始化"""
    print("🔍 测试导入和初始化...")
    
    try:
        # 测试组件导入和实例化
        requirements_flow = RequirementsAnalysisFlow()
        process_node = ProcessRequirementsNode()
        llm_node = LLMStructureNode()
        validation_node = ValidationNode()
        req_node = NodeReq()
        
        print("✅ 所有Requirements Analysis Agent组件导入和实例化成功")
        return True
    except Exception as e:
        print(f"❌ 组件导入失败: {e}")
        return False


def test_llm_structure_node():
    """测试LLM结构化节点"""
    print("\n🔍 测试LLM结构化节点...")
    
    # 创建模拟的共享变量
    mock_shared = {
        "extracted_requirements": {
            "project_type": "web_application",
            "main_features": ["用户管理", "项目管理", "任务跟踪"],
            "technologies": ["Python", "React"],
            "complexity": "medium"
        },
        "dialogue_history": "用户希望开发一个项目管理系统，支持多用户协作，包含任务分配和进度跟踪功能。",
        "user_intent": {
            "original_request": "开发项目管理系统",
            "extracted_keywords": ["项目管理", "多用户", "任务分配"]
        }
    }
    
    try:
        llm_node = LLMStructureNode()
        
        # 执行prep
        prep_result = llm_node.prep(mock_shared)
        print(f"   prep完成，提取的信息: {len(prep_result['extracted_info'])} 个字段")
        
        # 执行exec
        exec_result = llm_node.exec(prep_result)
        print(f"   exec完成，处理成功: {exec_result.get('processing_success')}")
        
        # 执行post
        post_result = llm_node.post(mock_shared, prep_result, exec_result)
        print(f"   post完成，返回: {post_result}")
        
        # 检查结果
        structured_requirements = mock_shared.get("structured_requirements", {})
        if structured_requirements:
            project_title = structured_requirements.get("project_overview", {}).get("title", "")
            core_features = structured_requirements.get("functional_requirements", {}).get("core_features", [])
            print(f"   项目标题: {project_title}")
            print(f"   核心功能数量: {len(core_features)}")
            return True
        else:
            print("❌ 未生成结构化需求")
            return False
            
    except Exception as e:
        print(f"❌ LLM结构化节点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_node():
    """测试验证节点"""
    print("\n🔍 测试验证节点...")
    
    # 创建模拟的结构化需求
    mock_shared = {
        "structured_requirements": {
            "project_overview": {
                "title": "智能项目管理系统",
                "description": "基于AI的项目管理和协作平台",
                "objectives": ["提高项目管理效率", "增强团队协作"],
                "target_users": ["项目经理", "团队成员"],
                "success_criteria": ["项目交付效率提升30%"]
            },
            "functional_requirements": {
                "core_features": [
                    {
                        "name": "项目创建与管理",
                        "description": "创建、编辑、删除项目",
                        "priority": "high",
                        "acceptance_criteria": ["支持项目模板"]
                    }
                ],
                "user_stories": [
                    {
                        "role": "项目经理",
                        "goal": "快速创建项目",
                        "benefit": "提高效率"
                    }
                ]
            },
            "non_functional_requirements": {
                "performance": {
                    "response_time": "< 2秒",
                    "throughput": "1000并发用户"
                },
                "security": {
                    "authentication": "多因素认证",
                    "authorization": "基于角色的权限控制"
                }
            },
            "technical_requirements": {
                "programming_languages": ["Python", "JavaScript"],
                "frameworks": ["Django", "React"],
                "databases": ["PostgreSQL"]
            }
        }
    }
    
    try:
        validation_node = ValidationNode()
        
        # 执行prep
        prep_result = validation_node.prep(mock_shared)
        print(f"   prep完成，待验证需求字段数: {len(prep_result['structured_requirements'])}")
        
        # 执行exec
        exec_result = validation_node.exec(prep_result)
        print(f"   exec完成，验证成功: {exec_result.get('validation_success')}")
        
        # 执行post
        post_result = validation_node.post(mock_shared, prep_result, exec_result)
        print(f"   post完成，返回: {post_result}")
        
        # 检查验证报告
        validation_report = mock_shared.get("validation_report", {})
        if validation_report:
            overall_score = validation_report.get("overall_score", 0)
            grade = validation_report.get("quality_assessment", {}).get("grade", "")
            print(f"   质量评分: {overall_score}")
            print(f"   质量等级: {grade}")
            return True
        else:
            print("❌ 未生成验证报告")
            return False
            
    except Exception as e:
        print(f"❌ 验证节点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_node_req_standalone():
    """单独测试NodeReq节点"""
    print("\n🔍 测试NodeReq节点...")

    try:
        req_node = NodeReq()

        # 准备测试数据 - 使用正确的字典格式
        shared = {
            "dialogue_history": {
                "session_id": "test-session",
                "start_time": "2024-12-01T10:00:00",
                "messages": [
                    {
                        "timestamp": "2024-12-01T10:00:00",
                        "role": "user",
                        "content": "用户希望开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能。",
                        "message_type": "text",
                        "metadata": {}
                    }
                ],
                "total_messages": 1,
                "last_activity": "2024-12-01T10:00:00"
            },
            "user_intent": {
                "original_request": "开发在线教育平台"
            }
        }

        # 执行prep
        prep_result = req_node.prep(shared)
        print(f"   prep完成: {prep_result is not None}")

        # 执行exec
        exec_result = req_node.exec(prep_result)
        print(f"   exec完成: {exec_result is not None}")

        # 执行post
        post_result = req_node.post(shared, prep_result, exec_result)
        print(f"   post完成，返回: {post_result}")

        # 检查结果
        extracted_requirements = shared.get("extracted_requirements", {})
        print(f"   提取的需求: {len(extracted_requirements)} 个字段")

        return post_result == "success"

    except Exception as e:
        print(f"❌ NodeReq测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_requirements_analysis_flow():
    """测试需求分析流程"""
    print("\n🔍 测试需求分析流程...")

    try:
        requirements_flow = RequirementsAnalysisFlow()

        # 准备测试数据 - 使用正确的字典格式
        shared = {
            "dialogue_history": {
                "session_id": "test-session-2",
                "start_time": "2024-12-01T11:00:00",
                "messages": [
                    {
                        "timestamp": "2024-12-01T11:00:00",
                        "role": "user",
                        "content": "用户希望开发一个在线教育平台，支持视频课程、在线考试、学习进度跟踪等功能。需要支持多种用户角色：学生、教师、管理员。",
                        "message_type": "text",
                        "metadata": {}
                    }
                ],
                "total_messages": 1,
                "last_activity": "2024-12-01T11:00:00"
            },
            "user_intent": {
                "original_request": "开发在线教育平台",
                "extracted_keywords": ["在线教育", "视频课程", "在线考试", "学习进度"]
            },

            # 用于存储流程中的数据
            "extracted_requirements": {},
            "structured_requirements": {},
            "validation_report": {}
        }

        print("   执行需求分析流程...")
        try:
            flow_result = requirements_flow.run(shared)
            print(f"   流程执行结果: {flow_result}")
        except Exception as e:
            print(f"   流程执行异常: {e}")
            import traceback
            traceback.print_exc()
            flow_result = False

        if flow_result:
            print("✅ 需求分析流程执行成功")
            
            # 检查结果
            structured_requirements = shared.get("structured_requirements", {})
            validation_report = shared.get("validation_report", {})
            
            if structured_requirements:
                project_title = structured_requirements.get("project_overview", {}).get("title", "")
                core_features = structured_requirements.get("functional_requirements", {}).get("core_features", [])
                print(f"   项目标题: {project_title}")
                print(f"   核心功能数量: {len(core_features)}")
            
            if validation_report:
                overall_score = validation_report.get("overall_score", 0)
                print(f"   质量评分: {overall_score}")
            
            return True
        else:
            print("❌ 需求分析流程执行失败")
            return False
            
    except Exception as e:
        print(f"❌ 需求分析流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_process_requirements_node():
    """测试ProcessRequirements主节点"""
    print("\n🔍 测试ProcessRequirements主节点...")
    
    # 创建完整的模拟主Agent共享状态
    mock_shared = {
        "dialogue_history": {
            "session_id": "test-session-3",
            "start_time": "2024-12-01T12:00:00",
            "messages": [
                {
                    "timestamp": "2024-12-01T12:00:00",
                    "role": "user",
                    "content": "用户希望开发一个电商平台，包含商品管理、订单处理、支付集成、用户评价等功能。需要支持移动端和PC端。",
                    "message_type": "text",
                    "metadata": {}
                }
            ],
            "total_messages": 1,
            "last_activity": "2024-12-01T12:00:00"
        },
        "user_intent": {
            "original_request": "开发电商平台",
            "extracted_keywords": ["电商", "商品管理", "订单处理", "支付"]
        },
        "current_stage": "user_input_completed",
        "system_messages": [],
        "metadata": {
            "processing_stages": [],
            "total_processing_time": 0.0
        }
    }
    
    try:
        process_node = ProcessRequirementsNode()
        
        # 执行prep
        prep_result = process_node.prep(mock_shared)
        print(f"   prep完成，对话历史长度: {len(prep_result['dialogue_history'])}")
        
        # 执行exec
        exec_result = process_node.exec(prep_result)
        print(f"   exec完成，处理成功: {exec_result.get('processing_success')}")
        
        # 执行post
        post_result = process_node.post(mock_shared, prep_result, exec_result)
        print(f"   post完成，返回: {post_result}")
        
        # 检查主Agent共享状态的变化
        print(f"   当前阶段: {mock_shared.get('current_stage')}")
        print(f"   结构化需求: {'已创建' if mock_shared.get('structured_requirements') else '未创建'}")
        print(f"   系统消息数量: {len(mock_shared.get('system_messages', []))}")
        
        structured_requirements = mock_shared.get('structured_requirements', {})
        if structured_requirements:
            project_title = structured_requirements.get('project_overview', {}).get('title', '')
            core_features = structured_requirements.get('functional_requirements', {}).get('core_features', [])
            print(f"   项目标题: {project_title}")
            print(f"   核心功能数量: {len(core_features)}")
        
        requirements_metadata = mock_shared.get('requirements_metadata', {})
        if requirements_metadata:
            quality_score = requirements_metadata.get('quality_score', 0)
            print(f"   质量评分: {quality_score}")
        
        return post_result == "success"
        
    except Exception as e:
        print(f"❌ ProcessRequirements主节点测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行Requirements Analysis Agent完整测试...")
    print("=" * 60)
    
    test_results = []
    
    # 1. 导入和初始化测试
    test_results.append(test_imports_and_initialization())
    
    # 2. NodeReq节点测试
    test_results.append(test_node_req_standalone())

    # 3. LLM结构化节点测试
    test_results.append(test_llm_structure_node())

    # 4. 验证节点测试
    test_results.append(test_validation_node())

    # 5. 需求分析流程测试
    test_results.append(test_requirements_analysis_flow())

    # 6. ProcessRequirements主节点测试
    test_results.append(test_process_requirements_node())
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"🎯 测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Requirements Analysis Agent工作正常。")
        print("\n✅ 验证的功能:")
        print("   - 组件导入和初始化")
        print("   - LLM结构化处理")
        print("   - 需求验证和质量评估")
        print("   - 完整的需求分析流程")
        print("   - 主Agent共享状态更新")
        print("   - pocketflow字典共享变量的正确使用")
    else:
        print("⚠️ 部分测试失败，请检查错误信息。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
