#!/usr/bin/env python3
"""
测试ASCII Logo显示效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.cli.gtplanner_cli import ModernGTPlannerCLI
from rich.console import Console


def test_ascii_logo():
    """测试ASCII logo显示"""
    console = Console()
    
    console.print("🧪 测试ASCII Logo显示效果")
    console.print("=" * 50)
    
    # 测试不同语言的CLI
    languages = [
        ("zh", "中文"),
        ("en", "English"),
        ("ja", "日本語"),
        ("es", "Español"),
        ("fr", "Français")
    ]
    
    for lang_code, lang_name in languages:
        console.print(f"\n🌍 {lang_name} ({lang_code}) 界面:")
        console.print("-" * 30)
        
        # 创建CLI实例
        cli = ModernGTPlannerCLI(language=lang_code)
        
        # 显示ASCII logo
        cli.show_ascii_logo()
        
        # 显示语言信息
        console.print(f"语言设置: {cli.language}")
        console.print(f"欢迎标题: {cli.text_manager.get_text('welcome_title')}")
        
        console.print("\n" + "=" * 50)


if __name__ == "__main__":
    test_ascii_logo()
