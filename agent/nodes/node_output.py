"""
输出文档节点 (Node_Output) - 简化版本

简单的文件生成节点，不使用LLM。
直接接收文档内容并生成文件。

功能描述：
- 接收文档内容
- 验证文件格式
- 生成文件到指定目录
- 返回生成结果
"""

import time
import os
import json
from typing import Dict, Any
from pocketflow import Node


class NodeOutput(Node):
    """输出文档节点 - 简单的文件生成器"""
    
    def __init__(self, output_dir: str = "output"):
        """
        初始化输出文档节点
        
        Args:
            output_dir: 输出目录，默认为"output"
        """
        super().__init__()
        self.output_dir = output_dir
    
    def prep(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从共享变量获取文档内容

        期望的输入格式：
        {
            "files_to_generate": [
                {
                    "filename": "requirements.md",
                    "content": "文档内容..."
                },
                {
                    "filename": "nodes.json",
                    "content": {...}
                }
            ],
            "output_config": {
                "output_directory": "output"  # 可选，默认使用节点初始化时的目录
            }
        }

        Args:
            shared: 共享变量字典

        Returns:
            准备结果字典
        """
        try:
            # 获取要生成的文件列表
            files_to_generate = shared.get("files_to_generate", [])

            # 验证输入格式
            if not files_to_generate:
                raise ValueError("没有找到要生成的文件列表 (files_to_generate)")

            if not isinstance(files_to_generate, list):
                raise ValueError("files_to_generate 必须是列表格式")

            # 验证每个文件的格式
            validated_files = []
            for i, file_info in enumerate(files_to_generate):
                if not isinstance(file_info, dict):
                    raise ValueError(f"文件 {i} 必须是字典格式")

                if "filename" not in file_info:
                    raise ValueError(f"文件 {i} 缺少 filename 字段")

                if "content" not in file_info:
                    raise ValueError(f"文件 {i} 缺少 content 字段")

                validated_files.append({
                    "filename": file_info["filename"],
                    "content": file_info["content"]
                })

            # 获取输出配置
            output_config = shared.get("output_config", {})
            output_dir = output_config.get("output_directory", self.output_dir)

            return {
                "files_to_generate": validated_files,
                "output_dir": output_dir,
                "timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"Output preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：生成文件

        Args:
            prep_result: 准备阶段的结果

        Returns:
            执行结果字典
        """
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            files_to_generate = prep_result["files_to_generate"]
            output_dir = prep_result["output_dir"]

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            generated_files = []

            # 生成每个文件
            for file_info in files_to_generate:
                filename = file_info["filename"]
                content = file_info["content"]
                file_path = os.path.join(output_dir, filename)

                # 根据文件类型处理内容
                if filename.endswith('.json'):
                    # JSON文件：确保格式正确
                    if isinstance(content, str):
                        try:
                            # 验证JSON格式
                            json.loads(content)
                            file_content = content
                        except json.JSONDecodeError:
                            # 如果不是有效JSON，包装成字符串
                            file_content = json.dumps({"content": content}, indent=2, ensure_ascii=False)
                    else:
                        # 如果是字典或列表，直接序列化
                        file_content = json.dumps(content, indent=2, ensure_ascii=False)
                else:
                    # 文本文件：直接写入
                    file_content = str(content)

                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)

                # 记录生成的文件信息
                generated_file_info = {
                    "filename": filename,
                    "file_path": file_path,
                    "file_size": len(file_content.encode('utf-8')),
                    "file_type": filename.split('.')[-1] if '.' in filename else 'txt',
                    "generated_at": time.time()
                }
                generated_files.append(generated_file_info)

                print(f"✅ 生成文件: {file_path} ({generated_file_info['file_size']} bytes)")

            return {
                "generated_files": generated_files,
                "output_directory": output_dir,
                "total_files": len(generated_files),
                "generation_time": time.time()
            }

        except Exception as e:
            return {"error": f"File generation failed: {str(e)}"}
    
    def post(self, shared, prep_result: Dict[str, Any], exec_result: Dict[str, Any]) -> str:
        """
        后处理阶段：更新共享状态
        
        Args:
            shared: 共享变量字典
            prep_result: 准备阶段结果
            exec_result: 执行阶段结果
            
        Returns:
            处理结果状态
        """
        try:
            if "error" in exec_result:
                shared["output_error"] = exec_result["error"]
                print(f"❌ 文件生成失败: {exec_result['error']}")
                return "error"
            
            # 更新共享状态
            generated_files = exec_result["generated_files"]
            shared["generated_files"] = generated_files
            shared["output_directory"] = exec_result["output_directory"]
            shared["file_generation_completed"] = True
            
            # 添加系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "file_generation",
                "status": "completed",
                "message": f"成功生成 {len(generated_files)} 个文件",
                "details": {
                    "output_directory": exec_result["output_directory"],
                    "files": [f["filename"] for f in generated_files]
                }
            })
            
            print(f"✅ 文件生成完成，共生成 {len(generated_files)} 个文件")
            print(f"   输出目录: {exec_result['output_directory']}")
            
            return "success"
            
        except Exception as e:
            shared["output_post_error"] = str(e)
            print(f"❌ 后处理失败: {str(e)}")
            return "error"
    
    def generate_files_directly(self, files_to_generate: list, output_dir: str = None) -> Dict[str, Any]:
        """
        直接生成文件的便捷方法

        Args:
            files_to_generate: 文件列表 [{"filename": "xxx", "content": "xxx"}, ...]
            output_dir: 输出目录，如果为None则使用默认目录

        Returns:
            生成结果
        """
        if output_dir is None:
            output_dir = self.output_dir

        # 创建临时共享状态
        temp_shared = {
            "files_to_generate": files_to_generate,
            "output_config": {"output_directory": output_dir}
        }

        # 执行完整流程
        prep_result = self.prep(temp_shared)
        exec_result = self.exec(prep_result)
        post_result = self.post(temp_shared, prep_result, exec_result)

        return {
            "status": post_result,
            "generated_files": exec_result.get("generated_files", []),
            "output_directory": exec_result.get("output_directory", ""),
            "error": exec_result.get("error", "")
        }
