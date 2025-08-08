#!/usr/bin/env python3
"""
GTPlanner 启动脚本

快速启动GTPlanner CLI的便捷脚本。

使用方式:
    python gtplanner.py                    # 启动交互式CLI
    python gtplanner.py "设计用户管理系统"   # 直接处理需求
    python gtplanner.py --verbose "需求"    # 详细模式
    python gtplanner.py --load <session_id> # 加载指定会话
"""

import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent
    cli_path = script_dir / "cli" / "gtplanner_cli.py"
    
    # 构建命令
    cmd = [sys.executable, str(cli_path)] + sys.argv[1:]
    
    # 执行CLI
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 用户中断，再见！")
        sys.exit(0)

if __name__ == "__main__":
    main()
