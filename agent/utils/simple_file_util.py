"""
简化的文件输出工具

直接将LLM输出的markdown内容写入文件，无需JSON解析和验证。
"""

from typing import Dict, Any
from agent.streaming import (
    emit_processing_status,
    emit_error
)


async def write_file_directly(filename: str, content: str, shared: Dict[str, Any]) -> bool:
    """
    直接将内容写入指定文件

    Args:
        filename: 文件名（如 "01_agent_analysis.md"）
        content: 文件内容
        shared: 共享变量字典

    Returns:
        bool: 是否成功生成文件
    """
    import os

    try:
        if not content or not content.strip():
            await emit_error(shared, f"⚠️ 无内容可写入文件 {filename}")
            return False

        # 创建输出目录
        output_dir = "output"
        os.makedirs(output_dir, exist_ok=True)

        # 构建完整文件路径
        file_path = os.path.join(output_dir, filename)

        # 直接写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content.strip())

        # 更新shared变量
        if "generated_files" not in shared:
            shared["generated_files"] = []

        # 添加生成的文件信息
        file_info = {
            "filename": filename,
            "path": file_path,
            "size": len(content.strip()),
            "created_at": __import__('time').time()
        }
        shared["generated_files"].append(file_info)
        shared["output_directory"] = output_dir

        await emit_processing_status(shared, f"📄 文件已生成: {file_path}")
        return True

    except Exception as e:
        await emit_error(shared, f"⚠️ 文件生成出错: {str(e)}")
        return False



