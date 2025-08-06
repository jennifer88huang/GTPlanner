#!/usr/bin/env python3
"""
GTPlanner ReAct主控制器演示脚本

展示基于单体LLM的ReAct（Reasoning and Acting）闭环模式的工作流程：
1. 思考阶段（Thought）：分析当前状态，决定下一步行动策略
2. 行动阶段（Action）：执行具体操作（调用专业Agent、用户交互等）
3. 观察阶段（Observation）：收集结果，更新状态，评估是否继续循环

演示完整的GTPlanner系统架构和ReAct主控制器的核心功能。
"""

import sys
import os
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def demo_basic_functionality():
    """演示基本功能"""
    print("=" * 80)
    print("GTPlanner ReAct主控制器演示")
    print("=" * 80)
    
    try:
        # 导入必要的模块
        from agent.gtplanner import GTPlanner
        from agent.shared import get_shared_state
        from agent.flows.orchestrator_react_flow import OrchestratorReActFlow
        from agent.flows.react_orchestrator_node import ReActOrchestratorNode
        from agent.flows.agent_dispatcher import AgentDispatcher
        
        print("✓ 所有模块导入成功")
        
        # 1. 创建GTPlanner实例
        print("\n1. 创建GTPlanner实例...")
        planner = GTPlanner()
        shared_state = get_shared_state()
        
        print(f"   会话ID: {shared_state.session_id}")
        print(f"   当前阶段: {shared_state.current_stage}")
        
        # 2. 添加用户输入
        print("\n2. 添加用户输入...")
        user_input = "我需要设计一个用户管理系统，包括用户注册、登录、权限管理等功能"
        shared_state.add_user_message(user_input)
        print(f"   用户输入: {user_input}")
        
        # 3. 演示Agent调度器
        print("\n3. 演示Agent调度器...")
        dispatcher = AgentDispatcher()
        status = dispatcher.get_status()
        print(f"   Agent初始化状态: {status['agents_initialized']}")
        print(f"   可用Agent: {status.get('available_agents', [])}")
        
        available_actions = dispatcher.get_available_actions(shared_state.data)
        print(f"   当前可用行动: {available_actions}")
        
        # 4. 演示ReAct节点
        print("\n4. 演示ReAct节点...")
        react_node = ReActOrchestratorNode()
        
        # Prep阶段
        prep_result = react_node.prep(shared_state.data)
        print(f"   Prep阶段成功: {prep_result['success']}")
        
        if prep_result["success"]:
            context = prep_result["react_context"]
            print(f"   当前阶段: {context['current_stage']}")
            print(f"   ReAct循环次数: {context['react_cycle_count']}")
            print(f"   可用行动: {context['available_actions']}")
            
            # 显示完成状态
            completion_status = context['completion_status']
            print("   完成状态:")
            for key, value in completion_status.items():
                status_icon = "✓" if value else "○"
                print(f"     {status_icon} {key}: {value}")
        
        # 5. 演示主控制器流程
        print("\n5. 演示主控制器流程...")
        orchestrator = OrchestratorReActFlow()
        
        flow_info = orchestrator.get_flow_info()
        print(f"   流程名称: {flow_info['name']}")
        print(f"   流程类型: {flow_info['flow_type']}")
        print(f"   支持的行动: {flow_info['supported_actions']}")
        print(f"   流程特性: {flow_info['flow_features']}")
        
        # 获取当前状态
        current_status = orchestrator.get_status(shared_state.data)
        print(f"   当前状态: {current_status}")
        
        # 6. 演示ReAct提示词构建
        print("\n6. 演示ReAct提示词构建...")
        if prep_result["success"]:
            prompt = react_node._build_react_prompt(context)
            print(f"   提示词长度: {len(prompt)} 字符")
            print("   提示词预览:")
            print("   " + "-" * 60)
            # 显示提示词的前500个字符
            preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
            for line in preview.split('\n')[:10]:  # 只显示前10行
                print(f"   {line}")
            if len(prompt) > 500:
                print("   ...")
            print("   " + "-" * 60)
        
        # 7. 演示响应解析
        print("\n7. 演示响应解析...")
        sample_response = '''
        {
            "thought": {
                "current_goal": "分析用户需求并生成结构化需求文档",
                "situation_analysis": "用户提供了用户管理系统的基本需求",
                "known_information": ["用户需要用户管理系统", "包含注册、登录、权限管理功能"],
                "gaps_identified": ["需要详细的功能需求", "需要非功能性需求", "需要技术约束"],
                "reasoning": "首先需要进行详细的需求分析，提取结构化的需求信息"
            },
            "action_decision": {
                "should_act": true,
                "action_type": "requirements_analysis",
                "action_rationale": "需要将用户的自然语言需求转换为结构化的需求文档",
                "expected_outcome": "获得包含功能需求、非功能需求和约束条件的结构化文档",
                "confidence": 0.9
            },
            "observation": {
                "current_progress": "开始需求分析阶段",
                "goal_achieved": false,
                "should_continue_cycle": true,
                "requires_user_input": false,
                "next_focus": "需求分析和结构化",
                "success_indicators": ["生成结构化需求文档", "识别核心功能模块", "明确技术约束"]
            }
        }
        '''
        
        parsed_result = react_node._parse_react_response(sample_response)
        print("   解析结果:")
        print(f"     思考目标: {parsed_result['thought'].get('current_goal', 'N/A')}")
        print(f"     行动类型: {parsed_result['action_decision'].get('action_type', 'N/A')}")
        print(f"     置信度: {parsed_result['action_decision'].get('confidence', 'N/A')}")
        print(f"     是否继续循环: {parsed_result['observation'].get('should_continue_cycle', 'N/A')}")
        
        # 8. 显示系统架构总结
        print("\n8. 系统架构总结...")
        print("   ✓ SharedState: 统一的状态管理")
        print("   ✓ AgentDispatcher: 专业Agent调度")
        print("   ✓ ReActOrchestratorNode: 单体LLM ReAct循环")
        print("   ✓ OrchestratorReActFlow: 主控制器流程")
        print("   ✓ 错误处理和恢复机制")
        print("   ✓ 用户交互管理")
        
        print("\n" + "=" * 80)
        print("🎉 GTPlanner ReAct主控制器演示完成！")
        print("系统已成功实现基于单体LLM的ReAct闭环模式。")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def demo_react_cycle_simulation():
    """模拟ReAct循环过程"""
    print("\n" + "=" * 80)
    print("ReAct循环过程模拟")
    print("=" * 80)
    
    try:
        from agent.flows.react_orchestrator_node import ReActOrchestratorNode
        from agent.shared import SharedState
        
        # 创建测试环境
        shared_state = SharedState()
        shared_state.add_user_message("我需要设计一个电商系统")
        react_node = ReActOrchestratorNode()
        
        print("模拟ReAct循环的三个阶段：")
        print("\n1. 思考阶段（Thought）:")
        print("   - 分析当前状态和目标")
        print("   - 评估已知信息和缺失信息")
        print("   - 决定下一步最佳行动策略")
        
        print("\n2. 行动阶段（Action）:")
        print("   - 执行思考阶段决定的具体操作")
        print("   - 可能的行动类型:")
        print("     • requirements_analysis: 需求分析")
        print("     • short_planning: 短规划生成")
        print("     • research: 信息研究")
        print("     • architecture_design: 架构设计")
        print("     • user_interaction: 用户交互")
        print("     • complete: 完成处理")
        
        print("\n3. 观察阶段（Observation）:")
        print("   - 收集行动执行结果")
        print("   - 更新共享状态")
        print("   - 评估是否达成目标")
        print("   - 决定是否继续循环")
        
        # 演示状态分析
        prep_result = react_node.prep(shared_state.data)
        if prep_result["success"]:
            context = prep_result["react_context"]
            print(f"\n当前系统状态分析:")
            print(f"   处理阶段: {context['current_stage']}")
            print(f"   错误计数: {context['error_count']}")
            print(f"   可用行动: {context['available_actions']}")
            
            completion_status = context['completion_status']
            print("   各阶段完成状态:")
            for stage, completed in completion_status.items():
                icon = "✅" if completed else "⏳"
                print(f"     {icon} {stage}")
        
        print("\n" + "=" * 80)
        print("ReAct循环模拟完成")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"❌ 模拟过程中出现错误: {e}")
        return False

def main():
    """主函数"""
    print("GTPlanner ReAct主控制器完整演示")
    print("基于单体LLM实现的Reasoning and Acting闭环模式")
    print()
    
    # 运行基本功能演示
    success1 = demo_basic_functionality()
    
    # 运行ReAct循环模拟
    success2 = demo_react_cycle_simulation()
    
    if success1 and success2:
        print("\n🎊 所有演示成功完成！")
        print("\nGTPlanner ReAct主控制器特性总结:")
        print("✅ 单体LLM实现完整ReAct循环")
        print("✅ 智能Agent调度和协调")
        print("✅ 统一的状态管理")
        print("✅ 完善的错误处理机制")
        print("✅ 用户交互管理")
        print("✅ 与现有专业Agent无缝集成")
        print("✅ 支持多轮ReAct循环")
        print("✅ 结构化的思考-行动-观察流程")
        
        return True
    else:
        print("\n⚠️ 部分演示失败，请检查系统配置")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
