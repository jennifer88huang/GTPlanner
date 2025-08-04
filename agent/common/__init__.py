"""
Agent通用模块

提供统一的导入接口，避免复杂的相对路径导入
"""

# 重新导出常用的工具函数
try:
    from utils.call_llm import call_llm_async
except ImportError:
    # 如果直接导入失败，尝试相对路径
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
    from call_llm import call_llm_async

__all__ = ['call_llm_async']
