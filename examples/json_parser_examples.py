#!/usr/bin/env python3
"""
JSON流式解析器使用示例

展示各种使用场景和最佳实践
"""

import sys
import json
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.json_stream_parser import JSONStreamParser


def example_basic_usage():
    """示例1: 基本使用"""
    print("=" * 60)
    print("示例1: 基本使用")
    print("=" * 60)
    
    # 一次性解析
    parser = JSONStreamParser()
    result = parser.parse('{"name": "张三", "age": 25, "city": "北京"}')
    print(f"一次性解析结果: {result}")
    
    # 增量解析
    parser = JSONStreamParser()
    chunks = ['{"name":', ' "李四",', ' "age": 30,', ' "city": "上海"}']
    
    print("\n增量解析过程:")
    for i, chunk in enumerate(chunks, 1):
        result = parser.add_chunk(chunk)
        print(f"  块{i}: '{chunk}' -> {result}")
    
    final_result = parser.get_result()
    print(f"最终结果: {final_result}")


def example_template_usage():
    """示例2: 模板使用"""
    print("\n" + "=" * 60)
    print("示例2: 结构化模板解析")
    print("=" * 60)
    
    # 定义用户信息模板
    user_template = {
        "user": {
            "id": int,
            "name": str,
            "email": str,
            "age": int
        },
        "preferences": {
            "theme": str,
            "language": str,
            "notifications": bool
        },
        "activity": [
            {
                "date": str,
                "action": str,
                "score": float
            }
        ]
    }
    
    # 测试数据
    user_data = {
        "user": {
            "id": 12345,
            "name": "王小明",
            "email": "wang@example.com",
            "age": 28
        },
        "preferences": {
            "theme": "dark",
            "language": "zh-CN",
            "notifications": True
        },
        "activity": [
            {"date": "2024-01-01", "action": "login", "score": 10.0},
            {"date": "2024-01-02", "action": "purchase", "score": 50.5}
        ]
    }
    
    json_str = json.dumps(user_data, ensure_ascii=False)
    print(f"原始JSON: {json_str}")
    
    # 使用模板解析
    parser = JSONStreamParser(template=user_template)
    result = parser.parse(json_str)
    
    print(f"\n解析结果: {result}")
    
    # 获取模板信息
    completion = parser.get_completion_status()
    print(f"\n模板状态:")
    print(f"  完成度: {completion['completion_percentage']:.1f}%")
    print(f"  已完成字段: {completion['completed_fields']}/{completion['total_required_fields']}")
    
    # 验证结构
    validation = parser.validate_result()
    print(f"  结构验证: {'✓ 通过' if validation['valid'] else '✗ 失败'}")


def example_streaming_processing():
    """示例3: 流式处理"""
    print("\n" + "=" * 60)
    print("示例3: 流式处理大型JSON")
    print("=" * 60)
    
    # 生成大型JSON数据
    large_data = {
        "metadata": {"total": 100, "version": "1.0"},
        "items": [
            {
                "id": i,
                "title": f"商品_{i}",
                "price": round(i * 12.5, 2),
                "category": f"分类_{i % 5}",
                "available": i % 3 != 0
            }
            for i in range(100)
        ]
    }
    
    json_str = json.dumps(large_data, ensure_ascii=False)
    print(f"JSON大小: {len(json_str):,} 字符")
    
    # 定义商品模板
    product_template = {
        "metadata": {
            "total": int,
            "version": str
        },
        "items": [
            {
                "id": int,
                "title": str,
                "price": float,
                "category": str,
                "available": bool
            }
        ]
    }
    
    # 流式解析
    parser = JSONStreamParser(template=product_template)
    chunk_size = 200
    chunks = [json_str[i:i+chunk_size] for i in range(0, len(json_str), chunk_size)]
    
    print(f"\n流式解析 ({len(chunks)} 个块):")
    
    start_time = time.time()
    for i, chunk in enumerate(chunks):
        result = parser.add_chunk(chunk)
        
        # 每10个块显示一次进度
        if (i + 1) % 10 == 0 or i == len(chunks) - 1:
            completion = parser.get_completion_status()
            items_count = len(result.get('items', []))
            print(f"  块 {i+1:3d}/{len(chunks)}: 完成度 {completion['completion_percentage']:5.1f}%, 商品数 {items_count:3d}")
    
    parse_time = time.time() - start_time
    
    final_result = parser.get_result()
    final_items = len(final_result.get('items', []))
    
    print(f"\n流式解析完成:")
    print(f"  耗时: {parse_time:.3f}秒")
    print(f"  解析商品数: {final_items}")
    print(f"  解析速度: {len(json_str) / parse_time / 1000:.1f} KB/s")


def example_react_parsing():
    """示例4: ReAct响应解析"""
    print("\n" + "=" * 60)
    print("示例4: ReAct响应解析")
    print("=" * 60)
    
    # ReAct模板
    react_template = {
        "thought": {
            "reasoning": str,
            "current_goal": str,
            "known_information": [str],
            "gaps_identified": [str]
        },
        "action_decision": {
            "should_act": bool,
            "action_type": str,
            "action_rationale": str,
            "confidence": float
        },
        "observation": {
            "should_continue_cycle": bool,
            "goal_achieved": bool,
            "requires_user_input": bool,
            "current_progress": str
        }
    }
    
    # 模拟ReAct响应
    react_response = {
        "thought": {
            "reasoning": "用户询问如何优化JSON解析性能，我需要分析当前的解析方法并提供改进建议",
            "current_goal": "提供JSON解析性能优化方案",
            "known_information": [
                "用户使用标准JSON解析",
                "处理大型JSON文件",
                "需要实时处理能力"
            ],
            "gaps_identified": [
                "具体的性能瓶颈",
                "数据结构特点",
                "硬件资源限制"
            ]
        },
        "action_decision": {
            "should_act": True,
            "action_type": "provide_solution",
            "action_rationale": "基于已知信息可以提供流式解析方案",
            "confidence": 0.85
        },
        "observation": {
            "should_continue_cycle": True,
            "goal_achieved": False,
            "requires_user_input": False,
            "current_progress": "已分析问题，准备提供解决方案"
        }
    }
    
    json_str = json.dumps(react_response, ensure_ascii=False, indent=2)
    print(f"ReAct响应JSON:\n{json_str}")
    
    # 模拟流式接收ReAct响应
    parser = JSONStreamParser(template=react_template)
    chunk_size = 50
    chunks = [json_str[i:i+chunk_size] for i in range(0, len(json_str), chunk_size)]
    
    print(f"\n模拟流式接收 ({len(chunks)} 个块):")
    
    for i, chunk in enumerate(chunks):
        result = parser.add_chunk(chunk)
        completion = parser.get_completion_status()
        
        # 显示关键进度点
        if completion['completion_percentage'] >= 25 and i % 5 == 0:
            print(f"  块 {i+1:2d}: 完成度 {completion['completion_percentage']:5.1f}%")
            
            # 显示已解析的关键信息
            if 'thought' in result and result['thought']:
                goal = result['thought'].get('current_goal', '')
                if goal:
                    print(f"    当前目标: {goal}")
            
            if 'action_decision' in result and result['action_decision']:
                action = result['action_decision'].get('action_type', '')
                if action:
                    print(f"    行动类型: {action}")
    
    final_result = parser.get_result()
    validation = parser.validate_result()
    
    print(f"\nReAct解析完成:")
    print(f"  结构验证: {'✓ 通过' if validation['valid'] else '✗ 失败'}")
    print(f"  思考目标: {final_result['thought']['current_goal']}")
    print(f"  行动决策: {final_result['action_decision']['action_type']}")
    print(f"  置信度: {final_result['action_decision']['confidence']}")


def example_error_handling():
    """示例5: 错误处理"""
    print("\n" + "=" * 60)
    print("示例5: 错误处理和修复")
    print("=" * 60)
    
    # 测试各种错误情况
    error_cases = [
        ('不完整JSON', '{"name": "test", "age": 25'),
        ('缺少引号', '{"name": test, "age": 25}'),
        ('截断字符串', '{"name": "incomplete'),
        ('嵌套不完整', '{"user": {"name": "test", "data": [1, 2')
    ]
    
    for case_name, broken_json in error_cases:
        print(f"\n测试: {case_name}")
        print(f"输入: {broken_json}")
        
        try:
            parser = JSONStreamParser()
            result = parser.parse(broken_json)
            print(f"修复结果: {result}")
            print(f"结果类型: {type(result)}")
            
            if isinstance(result, dict):
                print(f"提取字段数: {len(result)}")
            
        except Exception as e:
            print(f"解析失败: {e}")


def main():
    """运行所有示例"""
    print("JSON流式解析器使用示例")
    print("展示各种使用场景和最佳实践")
    
    examples = [
        example_basic_usage,
        example_template_usage,
        example_streaming_processing,
        example_react_parsing,
        example_error_handling
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"示例执行出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)
    print("\n主要特性总结:")
    print("✅ 真正的增量解析 - 只处理新增字符")
    print("✅ 结构化模板支持 - 任意JSON结构定义")
    print("✅ 实时进度跟踪 - 显示解析完成度")
    print("✅ 自动错误修复 - 处理不完整JSON")
    print("✅ 高性能处理 - 模板开销几乎为零")
    print("✅ Unicode支持 - 完美支持中文")


if __name__ == "__main__":
    main()
