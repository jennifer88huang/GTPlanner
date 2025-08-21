#!/usr/bin/env python3
"""
GTPlanner FastAPI 服务启动脚本

启动集成了 SSE GTPlanner API 的 FastAPI 服务器
"""

import uvicorn
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """启动服务器"""
    print("🚀 启动 GTPlanner FastAPI 服务器...")
    print("📍 服务地址: http://localhost:11211")
    print("🎯 测试页面: http://localhost:11211/test")
    print("🔗 API 文档: http://localhost:11211/docs")
    print("📊 健康检查: http://localhost:11211/health")
    print("=" * 50)
    
    try:
        uvicorn.run(
            "fastapi_main:app",
            host="0.0.0.0",
            port=11211,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
