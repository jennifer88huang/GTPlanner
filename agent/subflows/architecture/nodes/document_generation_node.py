"""
Document Generation Node

第六步：整合所有设计结果，生成完整的Agent设计文档。
基于之前提示词的完整格式，生成高质量的pocketflow Agent设计文档。
"""

import time
import json
from typing import Dict, Any
from pocketflow import Node

# 导入LLM调用工具
from agent.common import call_llm_async
import asyncio


class DocumentGenerationNode(Node):
    """文档生成节点 - 生成完整的Agent设计文档"""
    
    def __init__(self):
        super().__init__()
        self.name = "DocumentGenerationNode"
        self.description = "整合所有设计结果生成完整的Agent设计文档"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集所有设计结果"""
        try:
            # 获取所有前面步骤的结果
            agent_analysis = shared.get("agent_analysis", {})
            identified_nodes = shared.get("identified_nodes", [])
            flow_design = shared.get("flow_design", {})
            data_structure = shared.get("data_structure", {})
            detailed_nodes = shared.get("detailed_nodes", [])
            
            # 获取原始需求信息
            structured_requirements = shared.get("structured_requirements", {})
            research_findings = shared.get("research_findings", {})
            confirmation_document = shared.get("confirmation_document", "")
            
            # 检查必需的输入
            required_data = {
                "agent_analysis": agent_analysis,
                "identified_nodes": identified_nodes,
                "flow_design": flow_design,
                "data_structure": data_structure,
                "detailed_nodes": detailed_nodes
            }
            
            missing_data = [key for key, value in required_data.items() if not value]
            if missing_data:
                return {"error": f"缺少必需的设计数据: {missing_data}"}
            
            return {
                "agent_analysis": agent_analysis,
                "identified_nodes": identified_nodes,
                "flow_design": flow_design,
                "data_structure": data_structure,
                "detailed_nodes": detailed_nodes,
                "structured_requirements": structured_requirements,
                "research_findings": research_findings,
                "confirmation_document": confirmation_document,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document generation preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：生成完整的Agent设计文档"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建文档生成提示词
            prompt = self._build_document_generation_prompt(prep_result)
            
            # 调用LLM生成文档
            agent_design_document = asyncio.run(self._generate_complete_document(prompt))
            
            return {
                "agent_design_document": agent_design_document,
                "generation_success": True,
                "generation_time": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document generation failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存文档并生成文件"""
        try:
            if "error" in exec_res:
                shared["document_generation_error"] = exec_res["error"]
                print(f"❌ 文档生成失败: {exec_res['error']}")
                return "error"
            
            # 保存生成的文档
            agent_design_document = exec_res["agent_design_document"]
            shared["agent_design_document"] = agent_design_document

            # 生成文件
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("document_generation", agent_design_document, shared)
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "document_generation",
                "status": "completed",
                "message": "完整Agent设计文档生成完成"
            })
            
            print("✅ 完整Agent设计文档生成完成")
            return "documentation_complete"
            
        except Exception as e:
            shared["document_generation_post_error"] = str(e)
            print(f"❌ 文档生成后处理失败: {str(e)}")
            return "error"
    
    def _build_document_generation_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建文档生成提示词"""
        agent_analysis = prep_result["agent_analysis"]
        identified_nodes = prep_result["identified_nodes"]
        flow_design = prep_result["flow_design"]
        data_structure = prep_result["data_structure"]
        detailed_nodes = prep_result["detailed_nodes"]
        structured_requirements = prep_result.get("structured_requirements", {})
        
        # 提取项目信息
        project_overview = structured_requirements.get("project_overview", {})
        project_title = project_overview.get("title", "AI Agent项目")
        
        prompt = f"""你是一个专业的AI助手，擅长编写基于pocketflow的Agent设计文档。请根据以下完整的设计结果，生成一份高质量的Agent设计文档。

**项目标题：** {project_title}

**Agent分析结果：**
{json.dumps(agent_analysis, indent=2, ensure_ascii=False)}

**识别的Node列表：**
{json.dumps(identified_nodes, indent=2, ensure_ascii=False)}

**Flow设计：**
{json.dumps(flow_design, indent=2, ensure_ascii=False)}

**数据结构设计：**
{json.dumps(data_structure, indent=2, ensure_ascii=False)}

**详细Node设计：**
{json.dumps(detailed_nodes, indent=2, ensure_ascii=False)}

请生成一份完整的Markdown格式的Agent设计文档，必须包含以下部分：

# {project_title}

## 项目需求
基于Agent分析结果，清晰描述项目目标和功能需求。

## 工具函数
如果需要的话，列出所需的工具函数（如LLM调用、数据处理等）。

## Flow设计
详细描述pocketflow的Flow编排，包含：
- Flow的整体设计思路
- 节点连接和Action驱动的转换逻辑
- 完整的执行流程描述

### Flow图表
使用Mermaid flowchart TD语法，生成完整的Flow图表。

## 数据结构
详细描述shared存储的数据结构，包含：
- shared存储的整体设计
- 各个字段的定义和用途
- 数据流转模式

## Node设计
为每个Node提供详细设计，包含：
- Purpose（目的）
- Design（设计类型，如Node、AsyncNode等）
- Data Access（数据访问模式）
- 详细的prep/exec/post三阶段设计

请确保文档：
1. 遵循pocketflow的最佳实践
2. 体现关注点分离原则
3. 包含完整的Action驱动逻辑
4. 提供清晰的数据流设计
5. 使用专业的技术文档格式

输出完整的Markdown格式文档："""
        
        return prompt
    
    async def _generate_complete_document(self, prompt: str) -> str:
        """调用LLM生成完整文档"""
        try:
            # 使用重试机制调用LLM
            result = await call_llm_async(prompt, is_json=False, max_retries=3, retry_delay=2)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    def _generate_document_file(self, shared: Dict[str, Any], document_content: str):
        """生成文档文件"""
        try:
            # 导入Node_Output
            from agent.nodes.node_output import NodeOutput
            
            node_output = NodeOutput(output_dir="output")
            
            # 准备文件数据
            files_to_generate = [
                {
                    "filename": "agent_design_complete.md",
                    "content": document_content
                }
            ]
            
            # 生成文件
            result = node_output.generate_files_directly(files_to_generate)
            
            if result["status"] == "success":
                # 更新或合并生成的文件信息
                if "generated_files" not in shared:
                    shared["generated_files"] = []
                shared["generated_files"].extend(result["generated_files"])
                shared["output_directory"] = result["output_directory"]
                print(f"✅ 完整设计文档已生成: {result['output_directory']}/agent_design_complete.md")
            else:
                print(f"⚠️ 文件生成失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"⚠️ 文件生成出错: {str(e)}")
            # 即使文件生成失败，也不影响主流程
