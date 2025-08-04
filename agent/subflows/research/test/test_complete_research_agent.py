"""
Research Agent 完整测试

基于pocketflow最佳实践的完整测试，验证Research Agent的所有功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from agent.subflows.research import (
    ProcessResearch,
    ResearchFlow,
    create_keyword_research_subflow,
    LLMAnalysisNode,
    ResultAssemblyNode,
    ResearchAggregator
)
from utils.config_manager import get_jina_api_key, get_all_config


def test_config_and_imports():
    """测试配置和导入"""
    print("🔍 测试配置和导入...")
    
    # 测试JINA API密钥
    jina_key = get_jina_api_key()
    if jina_key:
        print(f"✅ JINA API密钥已配置: {jina_key[:10]}...")
    else:
        print("❌ JINA API密钥未配置")
        return False
    
    # 测试组件导入
    try:
        process_node = ProcessResearch()
        research_flow = ResearchFlow()
        subflow = create_keyword_research_subflow()
        aggregator = ResearchAggregator()
        llm_node = LLMAnalysisNode()
        assembly_node = ResultAssemblyNode()
        
        print("✅ 所有Research Agent组件导入和实例化成功")
        return True
    except Exception as e:
        print(f"❌ 组件导入失败: {e}")
        return False


def test_process_research_prep():
    """测试ProcessResearch的prep方法"""
    print("\n🔍 测试ProcessResearch的prep方法...")
    
    # 创建模拟的pocketflow字典共享变量
    mock_shared = {
        "user_intent": {
            "extracted_keywords": ["Python", "机器学习", "API"]
        },
        "structured_requirements": {
            "project_overview": {
                "title": "智能数据分析平台",
                "description": "基于机器学习的数据分析平台",
                "objectives": ["提高数据处理效率", "实现智能分析"]
            },
            "functional_requirements": {
                "core_features": [
                    {"name": "数据导入"},
                    {"name": "模型训练"}
                ]
            }
        }
    }
    
    try:
        process_node = ProcessResearch()
        prep_result = process_node.prep(mock_shared)
        
        print(f"✅ prep方法执行成功")
        print(f"   提取的关键词: {prep_result['research_keywords']}")
        print(f"   关键词数量: {prep_result['total_keywords']}")
        
        # 验证结果
        assert "research_keywords" in prep_result
        assert "requirements" in prep_result
        assert "total_keywords" in prep_result
        assert len(prep_result["research_keywords"]) > 0
        
        return prep_result
        
    except Exception as e:
        print(f"❌ ProcessResearch prep方法测试失败: {e}")
        return None


def test_keyword_subflow():
    """测试单个关键词的子流程"""
    print("\n🔍 测试单个关键词的子流程...")
    
    try:
        # 创建子流程
        subflow = create_keyword_research_subflow()
        
        # 准备子流程的共享变量（pocketflow字典格式）
        subflow_shared = {
            "current_keyword": "Python编程",
            "analysis_requirements": "重点关注Python编程的基础概念和应用场景",
            "search_keywords": ["Python编程"],
            "max_search_results": 3,
            
            # 用于存储流程中的数据
            "first_search_result": {},
            "all_search_results": [],
            "url_content": "",
            "url_title": "",
            "url_metadata": {},
            "llm_analysis": {},
            "analyzed_keyword": "",
            "keyword_report": {}
        }
        
        print("   执行子流程...")
        flow_result = subflow.run(subflow_shared)
        
        # 检查结果
        keyword_report = subflow_shared.get("keyword_report", {})
        
        if flow_result and keyword_report:
            print("✅ 子流程执行成功")
            print(f"   关键词: {keyword_report.get('keyword')}")
            print(f"   URL: {keyword_report.get('url', '')[:50]}...")
            print(f"   内容长度: {len(keyword_report.get('content', ''))}")
            
            analysis = keyword_report.get('analysis', {})
            if analysis:
                print(f"   相关性分数: {analysis.get('relevance_score', 0)}")
                insights = analysis.get('key_insights', [])
                print(f"   洞察数量: {len(insights)}")
                if insights:
                    print(f"   第一个洞察: {insights[0][:50]}...")
            
            return keyword_report
        else:
            print("❌ 子流程执行失败或无结果")
            print(f"   flow_result: {flow_result}")
            print(f"   keyword_report keys: {list(keyword_report.keys()) if keyword_report else 'None'}")
            return None
            
    except Exception as e:
        print(f"❌ 子流程测试出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_research_flow_concurrent():
    """测试并发研究流程"""
    print("\n🔍 测试并发研究流程...")
    
    try:
        research_flow = ResearchFlow()
        
        # 测试多个关键词的并发处理
        test_keywords = ["Python编程", "机器学习"]
        analysis_requirements = "重点关注技术实现方案、最佳实践、相关工具和框架"
        
        print(f"   并发处理关键词: {test_keywords}")
        
        result = research_flow.process_research_keywords(test_keywords, analysis_requirements)
        
        if result.get("success"):
            research_report = result.get("research_report", [])
            aggregated_summary = result.get("aggregated_summary", {})
            
            print(f"✅ 并发处理成功，获得 {len(research_report)} 个结果")
            print(f"   成功关键词: {result.get('successful_keywords')}/{result.get('total_keywords')}")
            
            if research_report:
                print(f"   第一个结果关键词: {research_report[0].get('keyword')}")
                print(f"   第一个结果URL: {research_report[0].get('url', '')[:50]}...")
            
            if aggregated_summary:
                coverage = aggregated_summary.get('coverage_analysis', {})
                print(f"   平均相关性: {coverage.get('average_relevance', 0)}")
                print(f"   高质量结果: {coverage.get('high_quality_results', 0)}")
            
            return result
        else:
            print(f"❌ 并发处理失败: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ 并发研究流程测试出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_process_research_complete():
    """测试ProcessResearch的完整流程"""
    print("\n🔍 测试ProcessResearch的完整流程...")
    
    # 创建完整的模拟共享状态
    mock_shared = {
        "user_intent": {
            "extracted_keywords": ["Python", "机器学习", "API"]
        },
        "structured_requirements": {
            "project_overview": {
                "title": "智能数据分析平台",
                "description": "基于机器学习的数据分析平台",
                "objectives": ["提高数据处理效率", "实现智能分析"]
            },
            "functional_requirements": {
                "core_features": [
                    {"name": "数据导入"},
                    {"name": "模型训练"}
                ]
            }
        },
        "current_stage": "requirements_completed",
        "system_messages": [],
        "metadata": {
            "processing_stages": ["requirements_analysis"],
            "total_processing_time": 100.0
        }
    }
    
    try:
        process_node = ProcessResearch()
        
        # 执行prep
        prep_result = process_node.prep(mock_shared)
        print(f"   prep完成，关键词: {prep_result['research_keywords']}")
        
        # 执行exec
        exec_result = process_node.exec(prep_result)
        print(f"   exec完成，成功: {exec_result.get('processing_success')}")
        
        # 执行post
        post_result = process_node.post(mock_shared, prep_result, exec_result)
        print(f"   post完成，返回: {post_result}")
        
        # 检查共享状态的变化
        print(f"   当前阶段: {mock_shared.get('current_stage')}")
        print(f"   研究发现: {'已创建' if mock_shared.get('research_findings') else '未创建'}")
        print(f"   系统消息数量: {len(mock_shared.get('system_messages', []))}")
        
        research_findings = mock_shared.get('research_findings', {})
        if research_findings:
            research_report = research_findings.get('research_report', [])
            print(f"   研究报告数量: {len(research_report)}")
            
            metadata = research_findings.get('research_metadata', {})
            print(f"   成功率: {metadata.get('success_rate', 0):.2f}")
        
        return post_result == "success"
        
    except Exception as e:
        print(f"❌ ProcessResearch完整流程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("🚀 开始运行Research Agent完整测试...")
    print("=" * 60)
    
    test_results = []
    
    # 1. 配置和导入测试
    test_results.append(test_config_and_imports())
    
    # 2. ProcessResearch prep测试
    prep_result = test_process_research_prep()
    test_results.append(prep_result is not None)
    
    # 3. 单个关键词子流程测试
    subflow_result = test_keyword_subflow()
    test_results.append(subflow_result is not None)
    
    # 4. 并发研究流程测试
    concurrent_result = test_research_flow_concurrent()
    test_results.append(concurrent_result is not None)
    
    # 5. ProcessResearch完整流程测试
    complete_result = test_process_research_complete()
    test_results.append(complete_result)
    
    # 统计结果
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 60)
    print(f"🎯 测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Research Agent工作正常。")
        print("\n✅ 验证的功能:")
        print("   - 配置管理和组件导入")
        print("   - ProcessResearch节点的prep/exec/post方法")
        print("   - 单个关键词的完整子流程")
        print("   - 多关键词的并发处理")
        print("   - pocketflow字典共享变量的正确使用")
        print("   - 真实API调用和数据流")
    else:
        print("⚠️ 部分测试失败，请检查错误信息。")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
