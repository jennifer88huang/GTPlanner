#!/usr/bin/env python3
"""
测试全局系统提示词功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.openai_client import OpenAIClient, get_openai_client
from config.openai_config import get_openai_config


def test_prepare_messages_with_global_system_prompt():
    """测试消息准备方法"""
    print("🧪 测试全局系统提示词功能...")
    
    # 创建客户端实例
    client = OpenAIClient()
    
    # 测试1: 空消息列表
    print("\n📝 测试1: 空消息列表")
    empty_messages = []
    result = client._prepare_messages_with_global_system_prompt(empty_messages)
    print(f"输入: {empty_messages}")
    print(f"输出: {result}")
    assert len(result) == 1
    assert result[0]["role"] == "system"
    assert "JSON输出" in result[0]["content"]
    print("✅ 测试1通过")
    
    # 测试2: 没有系统消息的列表
    print("\n📝 测试2: 没有系统消息的列表")
    user_messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么可以帮助你的吗？"}
    ]
    result = client._prepare_messages_with_global_system_prompt(user_messages)
    print(f"输入: {user_messages}")
    print(f"输出: {result}")
    assert len(result) == 3
    assert result[0]["role"] == "system"
    assert "JSON输出" in result[0]["content"]
    assert result[1]["role"] == "user"
    assert result[2]["role"] == "assistant"
    print("✅ 测试2通过")
    
    # 测试3: 已有系统消息的列表
    print("\n📝 测试3: 已有系统消息的列表")
    messages_with_system = [
        {"role": "system", "content": "你是一个有用的助手"},
        {"role": "user", "content": "请生成一个JSON格式的响应"}
    ]
    result = client._prepare_messages_with_global_system_prompt(messages_with_system)
    print(f"输入: {messages_with_system}")
    print(f"输出: {result}")
    assert len(result) == 3
    assert result[0]["role"] == "system"
    assert "JSON输出" in result[0]["content"]
    assert result[1]["role"] == "system"
    assert result[1]["content"] == "你是一个有用的助手"
    assert result[2]["role"] == "user"
    print("✅ 测试3通过")
    
    print("\n🎉 所有测试通过！全局系统提示词功能正常工作。")


if __name__ == "__main__":
    test_prepare_messages_with_global_system_prompt()
