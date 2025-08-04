"""
输出文档节点 (Node_Output)

生成最终的文档文件。
完全基于LLM进行文档生成和格式化。

功能描述：
- 输入数据验证和预处理
- 模板选择和加载
- 内容格式化和渲染
- 文件生成和验证
- 元数据添加和打包
"""

import time
import asyncio
import sys
import os
import json
from typing import Dict, List, Any, Optional
from pocketflow import Node

# 添加utils路径以导入call_llm
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from call_llm import call_llm_async


class NodeOutput(Node):
    """输出文档节点 - 完全基于LLM进行文档生成"""
    
    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化输出文档节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
    
    def prep(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从参数和共享状态获取输出配置
        
        Args:
            shared: 共享状态对象
            
        Returns:
            准备结果字典
        """
        try:
            # 从节点参数获取输出配置
            requirements_md = self.params.get("requirements_md", "")
            mermaid_code = self.params.get("mermaid_code", "")
            nodes_json = self.params.get("nodes_json", {})
            variables_json = self.params.get("variables_json", {})
            output_config = self.params.get("output_config", {
                "file_format": ["md", "json"],
                "include_metadata": True,
                "template_style": "detailed"
            })
            
            # 如果没有提供数据，从共享状态中提取
            if not any([requirements_md, mermaid_code, nodes_json, variables_json]):
                extracted_data = self._extract_data_from_shared_state(shared)
                requirements_md = extracted_data.get("requirements_md", "")
                mermaid_code = extracted_data.get("mermaid_code", "")
                nodes_json = extracted_data.get("nodes_json", {})
                variables_json = extracted_data.get("variables_json", {})
            
            # 验证是否有足够的数据生成文档
            if not any([requirements_md, mermaid_code, nodes_json, variables_json]):
                return {
                    "error": "No data available for document generation",
                    "requirements_md": "",
                    "mermaid_code": "",
                    "nodes_json": {},
                    "variables_json": {},
                    "output_config": output_config
                }
            
            return {
                "requirements_md": requirements_md,
                "mermaid_code": mermaid_code,
                "nodes_json": nodes_json,
                "variables_json": variables_json,
                "output_config": output_config,
                "data_available": {
                    "has_requirements": bool(requirements_md),
                    "has_mermaid": bool(mermaid_code),
                    "has_nodes": bool(nodes_json),
                    "has_variables": bool(variables_json)
                }
            }
            
        except Exception as e:
            return {
                "error": f"Output preparation failed: {str(e)}",
                "requirements_md": "",
                "mermaid_code": "",
                "nodes_json": {},
                "variables_json": {},
                "output_config": {"file_format": ["md"], "include_metadata": True, "template_style": "standard"}
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：使用LLM生成文档文件
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        requirements_md = prep_res["requirements_md"]
        mermaid_code = prep_res["mermaid_code"]
        nodes_json = prep_res["nodes_json"]
        variables_json = prep_res["variables_json"]
        output_config = prep_res["output_config"]
        
        try:
            start_time = time.time()
            
            # 使用LLM生成文档
            generation_result = asyncio.run(self._generate_documents_with_llm(
                requirements_md, mermaid_code, nodes_json, variables_json, output_config
            ))
            
            generation_time = time.time() - start_time
            
            return {
                "generated_files": generation_result.get("generated_files", []),
                "generation_summary": {
                    "total_files": len(generation_result.get("generated_files", [])),
                    "generation_time": round(generation_time * 1000),  # 转换为毫秒
                    "validation_status": generation_result.get("validation_status", "passed")
                },
                "generation_metadata": {
                    "template_style": output_config.get("template_style", "standard"),
                    "include_metadata": output_config.get("include_metadata", True),
                    "generation_method": "llm_based"
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Document generation failed: {str(e)}")
    
    def post(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将生成的文档保存并更新共享状态
        
        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared.record_error(Exception(exec_res["error"]), "NodeOutput.exec")
                return "error"
            
            generated_files = exec_res["generated_files"]
            
            # 将生成的文档信息添加到共享状态
            if not hasattr(shared, 'generated_documents'):
                shared.generated_documents = []
            
            # 记录生成的文档
            for file_info in generated_files:
                document_record = {
                    "filename": file_info.get("filename", ""),
                    "file_type": file_info.get("file_type", ""),
                    "file_size": file_info.get("file_size", 0),
                    "content_preview": file_info.get("content", "")[:200] + "..." if len(file_info.get("content", "")) > 200 else file_info.get("content", ""),
                    "generated_at": time.time(),
                    "generation_method": "llm_based"
                }
                shared.generated_documents.append(document_record)
            
            # 更新处理阶段
            shared.update_stage("documents_generated")
            
            # 添加系统消息记录生成结果
            shared.add_system_message(
                f"文档生成完成，共生成 {exec_res['generation_summary']['total_files']} 个文件",
                agent_source="NodeOutput",
                files_count=exec_res['generation_summary']['total_files'],
                generation_time_ms=exec_res['generation_summary']['generation_time'],
                validation_status=exec_res['generation_summary']['validation_status']
            )
            
            return "success"
            
        except Exception as e:
            shared.record_error(e, "NodeOutput.post")
            return "error"
    
    def exec_fallback(self, prep_res: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        执行失败时的降级处理
        
        Args:
            prep_res: 准备阶段结果
            exc: 异常对象
            
        Returns:
            降级结果
        """
        # 生成基本的文档文件
        basic_files = []
        
        # 如果有需求数据，生成基本的需求文档
        if prep_res.get("requirements_md"):
            basic_files.append({
                "filename": "requirements_basic.md",
                "content": prep_res["requirements_md"],
                "file_type": "md",
                "file_size": len(prep_res["requirements_md"])
            })
        
        # 如果有Mermaid代码，生成基本的图表文档
        if prep_res.get("mermaid_code"):
            basic_files.append({
                "filename": "architecture_basic.md",
                "content": f"# 架构图\n\n```mermaid\n{prep_res['mermaid_code']}\n```",
                "file_type": "md",
                "file_size": len(prep_res["mermaid_code"]) + 50
            })
        
        return {
            "generated_files": basic_files,
            "generation_summary": {
                "total_files": len(basic_files),
                "generation_time": 0,
                "validation_status": "fallback"
            },
            "generation_metadata": {
                "template_style": "basic",
                "include_metadata": False,
                "generation_method": "fallback"
            },
            "fallback_reason": str(exc)
        }
    
    def _extract_data_from_shared_state(self, shared) -> Dict[str, Any]:
        """从共享状态中提取文档生成所需的数据"""
        data = {
            "requirements_md": "",
            "mermaid_code": "",
            "nodes_json": {},
            "variables_json": {}
        }
        
        # 提取需求信息
        if hasattr(shared, 'structured_requirements'):
            req = shared.structured_requirements
            if req.project_overview.title:
                requirements_parts = [
                    f"# {req.project_overview.title}",
                    f"\n## 项目描述\n{req.project_overview.description}",
                    f"\n## 项目范围\n{req.project_overview.scope}"
                ]
                
                if req.project_overview.objectives:
                    requirements_parts.append(f"\n## 项目目标\n" + "\n".join([f"- {obj}" for obj in req.project_overview.objectives]))
                
                if req.functional_requirements.core_features:
                    requirements_parts.append(f"\n## 核心功能\n" + "\n".join([f"- {feature.name}" for feature in req.functional_requirements.core_features]))
                
                data["requirements_md"] = "\n".join(requirements_parts)
        
        # 提取架构信息
        if hasattr(shared, 'architecture_draft'):
            arch = shared.architecture_draft
            if arch.mermaid_diagram.diagram_code:
                data["mermaid_code"] = arch.mermaid_diagram.diagram_code
            
            if arch.nodes_definition:
                data["nodes_json"] = {
                    "nodes": [
                        {
                            "id": node.node_id,
                            "name": node.node_name,
                            "type": node.node_type,
                            "description": node.description
                        } for node in arch.nodes_definition
                    ]
                }
            
            if arch.shared_variables:
                data["variables_json"] = {
                    "variables": [
                        {
                            "id": var.variable_id,
                            "name": var.variable_name,
                            "type": var.data_type,
                            "description": var.description,
                            "scope": var.scope
                        } for var in arch.shared_variables
                    ]
                }
        
        return data
    
    async def _generate_documents_with_llm(self, requirements_md: str, mermaid_code: str, 
                                          nodes_json: Dict, variables_json: Dict, 
                                          output_config: Dict) -> Dict[str, Any]:
        """使用LLM生成文档"""
        
        file_formats = output_config.get("file_format", ["md"])
        template_style = output_config.get("template_style", "standard")
        include_metadata = output_config.get("include_metadata", True)
        
        prompt = f"""
请基于以下数据生成完整的项目文档。

需求文档内容：
{requirements_md if requirements_md else "无需求文档"}

Mermaid架构图代码：
{mermaid_code if mermaid_code else "无架构图"}

节点定义JSON：
{json.dumps(nodes_json, ensure_ascii=False, indent=2) if nodes_json else "无节点定义"}

变量定义JSON：
{json.dumps(variables_json, ensure_ascii=False, indent=2) if variables_json else "无变量定义"}

输出配置：
- 文件格式：{file_formats}
- 模板样式：{template_style}
- 包含元数据：{include_metadata}

请以JSON格式返回生成的文件：
{{
    "generated_files": [
        {{
            "filename": "requirements.md",
            "content": "完整的需求文档内容，包含项目概述、功能需求、非功能需求等",
            "file_type": "md",
            "file_size": 1500
        }},
        {{
            "filename": "architecture.md", 
            "content": "架构设计文档，包含Mermaid图表和说明",
            "file_type": "md",
            "file_size": 2000
        }},
        {{
            "filename": "nodes_definition.json",
            "content": "节点定义的完整JSON结构",
            "file_type": "json", 
            "file_size": 800
        }}
    ],
    "validation_status": "passed"
}}

请确保：
1. 生成的文档内容完整、专业、格式规范
2. Markdown文档包含适当的标题层次和格式
3. JSON文档结构清晰、数据完整
4. 文件大小计算准确
5. 根据提供的数据生成相应的文档，没有数据的部分可以不生成对应文件
"""
        
        try:
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            # 如果LLM调用失败，返回基本的文档结构
            basic_files = []
            
            if requirements_md:
                basic_files.append({
                    "filename": "requirements.md",
                    "content": requirements_md,
                    "file_type": "md",
                    "file_size": len(requirements_md)
                })
            
            if mermaid_code:
                basic_files.append({
                    "filename": "architecture.md",
                    "content": f"# 架构设计\n\n```mermaid\n{mermaid_code}\n```",
                    "file_type": "md",
                    "file_size": len(mermaid_code) + 50
                })
            
            return {
                "generated_files": basic_files,
                "validation_status": "fallback"
            }
