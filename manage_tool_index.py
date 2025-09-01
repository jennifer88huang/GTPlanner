#!/usr/bin/env python3
"""
工具索引管理命令行工具

提供工具索引的创建、更新、状态检查等管理功能。

使用方式：
python scripts/manage_tool_index.py [command] [options]

命令：
- status: 查看索引状态
- create: 创建或重建索引
- refresh: 刷新索引（智能检测是否需要更新）
- force-refresh: 强制重建索引
- info: 显示详细的索引信息
"""

import sys
import os
import asyncio
import argparse
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agent.utils.tool_index_manager import tool_index_manager, ensure_tool_index
from agent.utils.startup_init import initialize_application, get_application_status
from utils.config_manager import get_vector_service_config


async def cmd_status():
    """查看索引状态"""
    print("🔍 检查工具索引状态...")

    # 显示配置信息
    vector_config = get_vector_service_config()
    print(f"\n⚙️ 配置信息:")
    print(f"  向量服务URL: {vector_config.get('base_url', 'N/A')}")
    print(f"  配置的索引名称: {vector_config.get('tools_index_name', 'N/A')}")
    print(f"  请求超时: {vector_config.get('timeout', 'N/A')} 秒")
    print(f"  向量字段: {vector_config.get('vector_field', 'N/A')}")

    status = await get_application_status()

    print("\n📊 应用状态:")
    print(f"  工具索引就绪: {'✅' if status['tool_index']['ready'] else '❌'}")
    print(f"  向量服务可用: {'✅' if status['vector_service']['available'] else '❌'}")

    if status['tool_index']['info']:
        info = status['tool_index']['info']
        print(f"\n📋 索引详情:")
        print(f"  当前索引名称: {info.get('current_index_name', 'N/A')}")
        print(f"  创建状态: {'已创建' if info.get('index_created') else '未创建'}")
        print(f"  最后创建时间: {info.get('last_index_time', 'N/A')}")
        print(f"  工具目录: {info.get('tools_dir', 'N/A')}")

        if info.get('last_tools_dir_mtime'):
            import datetime
            mtime = datetime.datetime.fromtimestamp(info['last_tools_dir_mtime'])
            print(f"  目录最后修改: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

    if not status['vector_service']['available']:
        print(f"\n❌ 向量服务问题: {status['vector_service'].get('error', 'Unknown error')}")


async def cmd_create(tools_dir: str = "tools", force: bool = False):
    """创建或重建索引"""
    print(f"🔨 {'强制重建' if force else '创建'}工具索引...")
    print(f"工具目录: {tools_dir}")
    
    try:
        index_name = await ensure_tool_index(
            tools_dir=tools_dir,
            force_reindex=force
        )
        
        print(f"✅ 索引操作完成: {index_name}")
        
        # 显示索引信息
        info = tool_index_manager.get_index_info()
        print(f"\n📋 索引信息:")
        print(f"  索引名称: {info.get('current_index_name')}")
        print(f"  创建时间: {info.get('last_index_time')}")
        
    except Exception as e:
        print(f"❌ 索引操作失败: {str(e)}")
        return False
    
    return True


async def cmd_refresh(tools_dir: str = "tools"):
    """智能刷新索引"""
    print("🔄 智能刷新工具索引...")
    return await cmd_create(tools_dir, force=False)


async def cmd_force_refresh(tools_dir: str = "tools"):
    """强制重建索引"""
    print("🔥 强制重建工具索引...")
    return await cmd_create(tools_dir, force=True)


async def cmd_info():
    """显示详细信息"""
    print("📋 工具索引详细信息")
    print("=" * 50)
    
    # 应用状态
    status = await get_application_status()
    
    print("🏗️ 应用状态:")
    print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
    
    # 索引管理器信息
    print("\n🔧 索引管理器信息:")
    info = tool_index_manager.get_index_info()
    print(json.dumps(info, indent=2, ensure_ascii=False, default=str))
    
    # 工具目录信息
    tools_dir = "tools"
    if os.path.exists(tools_dir):
        print(f"\n📁 工具目录信息 ({tools_dir}):")
        yaml_files = list(Path(tools_dir).rglob("*.yaml"))
        print(f"  YAML文件数量: {len(yaml_files)}")
        
        if yaml_files:
            print("  文件列表:")
            for file_path in sorted(yaml_files):
                rel_path = file_path.relative_to(tools_dir)
                mtime = file_path.stat().st_mtime
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"    - {rel_path} (修改时间: {mtime_str})")
    else:
        print(f"\n❌ 工具目录不存在: {tools_dir}")


async def cmd_init(tools_dir: str = "tools"):
    """完整的应用初始化"""
    print("🚀 执行完整的应用初始化...")
    
    result = await initialize_application(
        tools_dir=tools_dir,
        preload_index=True
    )
    
    if result["success"]:
        print("✅ 应用初始化成功")
    else:
        print("❌ 应用初始化失败")
        for error in result["errors"]:
            print(f"  - {error}")
    
    print(f"\n📊 初始化结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    
    return result["success"]


def main():
    parser = argparse.ArgumentParser(
        description="工具索引管理命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python scripts/manage_tool_index.py status
  python scripts/manage_tool_index.py create --tools-dir tools
  python scripts/manage_tool_index.py force-refresh
  python scripts/manage_tool_index.py info
        """
    )
    
    parser.add_argument(
        "command",
        choices=["status", "create", "refresh", "force-refresh", "info", "init"],
        help="要执行的命令"
    )
    
    parser.add_argument(
        "--tools-dir",
        default="tools",
        help="工具目录路径 (默认: tools)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制执行操作"
    )
    
    args = parser.parse_args()
    
    # 执行对应的命令
    async def run_command():
        try:
            if args.command == "status":
                await cmd_status()
            elif args.command == "create":
                success = await cmd_create(args.tools_dir, args.force)
                sys.exit(0 if success else 1)
            elif args.command == "refresh":
                success = await cmd_refresh(args.tools_dir)
                sys.exit(0 if success else 1)
            elif args.command == "force-refresh":
                success = await cmd_force_refresh(args.tools_dir)
                sys.exit(0 if success else 1)
            elif args.command == "info":
                await cmd_info()
            elif args.command == "init":
                success = await cmd_init(args.tools_dir)
                sys.exit(0 if success else 1)
        except KeyboardInterrupt:
            print("\n⚠️ 操作被用户中断")
            sys.exit(1)
        except Exception as e:
            print(f"❌ 命令执行失败: {str(e)}")
            sys.exit(1)
    
    # 运行异步命令
    asyncio.run(run_command())


if __name__ == "__main__":
    main()
