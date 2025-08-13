"""
简化的文件输出工具

直接将LLM输出的markdown内容写入文件，无需JSON解析和验证。
"""

from typing import Dict, Any


def write_file_directly(filename: str, content: str, shared: Dict[str, Any]) -> bool:
    """
    直接将内容写入指定文件

    Args:
        filename: 文件名（如 "01_agent_analysis.md"）
        content: 文件内容
        shared: 共享变量字典

    Returns:
        bool: 是否成功生成文件
    """
    try:
        # 导入NodeOutput
        from agent.nodes.node_output import NodeOutput

        if not content or not content.strip():
            print(f"⚠️ 无内容可写入文件 {filename}")
            return False

        # 准备文件数据
        files_to_generate = [
            {
                "filename": filename,
                "content": content.strip()
            }
        ]

        # 更新shared变量
        shared["files_to_generate"] = files_to_generate

        # 创建NodeOutput并生成文件
        node_output = NodeOutput(output_dir="output")
        result = node_output.generate_files_directly(files_to_generate)

        if result["status"] == "success":
            # 更新或初始化生成的文件信息
            if "generated_files" not in shared:
                shared["generated_files"] = []
            shared["generated_files"].extend(result["generated_files"])
            shared["output_directory"] = result["output_directory"]

            print(f"📄 文件已生成: {result['output_directory']}/{filename}")
            return True
        else:
            print(f"⚠️ 文件生成失败: {result.get('error', '未知错误')}")
            return False

    except Exception as e:
        print(f"⚠️ 文件生成出错: {str(e)}")
        return False



