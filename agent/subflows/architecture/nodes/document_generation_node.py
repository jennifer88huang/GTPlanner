"""
Document Generation Node

第六步：整合所有设计结果，生成完整的Agent设计文档。
基于之前提示词的完整格式，生成高质量的pocketflow Agent设计文档。
"""

import time
import json
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入OpenAI客户端
from utils.openai_client import get_openai_client


class DocumentGenerationNode(AsyncNode):
    """文档生成节点 - 生成完整的Agent设计文档"""
    
    def __init__(self):
        super().__init__()
        self.name = "DocumentGenerationNode"
        self.description = "整合所有设计结果生成完整的Agent设计文档"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集所有设计结果"""
        try:
            # 获取所有前面步骤的markdown结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")
            flow_markdown = shared.get("flow_markdown", "")
            data_structure_markdown = shared.get("data_structure_markdown", "")
            node_design_markdown = shared.get("node_design_markdown", "")

            # 获取项目状态信息
            short_planning = shared.get("short_planning", "")
            user_requirements = shared.get("user_requirements", "")
            research_findings = shared.get("research_findings", {})
            recommended_tools = shared.get("recommended_tools", [])

            # 检查必需的输入
            required_data = {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown
            }

            missing_data = [key for key, value in required_data.items() if not value]
            if missing_data:
                return {"error": f"缺少必需的设计数据: {missing_data}"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "flow_markdown": flow_markdown,
                "data_structure_markdown": data_structure_markdown,
                "node_design_markdown": node_design_markdown,
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document generation preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：生成完整的Agent设计文档"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建文档生成提示词
            prompt = self._build_document_generation_prompt(prep_result)
            
            # 异步调用LLM生成文档
            agent_design_document = await self._generate_complete_document(prompt)
            
            return {
                "agent_design_document": agent_design_document,
                "generation_success": True,
                "generation_time": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document generation failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存文档并生成文件"""
        try:
            if "error" in exec_res:
                shared["document_generation_error"] = exec_res["error"]
                print(f"❌ 文档生成失败: {exec_res['error']}")
                return "error"
            
            # 保存生成的文档
            agent_design_document = exec_res["agent_design_document"]
            shared["agent_design_document"] = agent_design_document

            # 使用简化文件工具直接写入markdown
            from ..utils.simple_file_util import write_file_directly
            write_file_directly("06_agent_design_complete.md", agent_design_document, shared)
            
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
        analysis_markdown = prep_result.get("analysis_markdown", "")
        nodes_markdown = prep_result.get("nodes_markdown", "")
        flow_markdown = prep_result.get("flow_markdown", "")
        data_structure_markdown = prep_result.get("data_structure_markdown", "")
        node_design_markdown = prep_result.get("node_design_markdown", "")
        user_requirements = prep_result.get("user_requirements", "")

        # 从用户需求中提取项目标题，如果没有则使用默认值
        project_title = "AI Agent项目"
        if user_requirements and isinstance(user_requirements, str):
            # 简单提取：取第一行或前50个字符作为标题
            first_line = user_requirements.split('\n')[0].strip()
            if first_line:
                project_title = first_line[:50] + ("..." if len(first_line) > 50 else "")

        # 获取其他上下文信息
        short_planning = prep_result.get("short_planning", "")
        research_findings = prep_result.get("research_findings", {})
        recommended_tools = prep_result.get("recommended_tools", [])

        # 构建推荐工具信息
        tools_info = ""
        if recommended_tools:
            tools_list = []
            for tool in recommended_tools:
                tool_name = tool.get("name", tool.get("id", "未知工具"))
                tool_type = tool.get("type", "")
                tool_summary = tool.get("summary", tool.get("description", ""))
                tools_list.append(f"- {tool_name} ({tool_type}): {tool_summary}")
            tools_info = "\n".join(tools_list)

        prompt = f"""你是一个专业的AI助手，擅长编写基于pocketflow的Agent设计文档。请根据以下完整的设计结果，生成一份高质量的Agent设计文档。

**项目标题：** {project_title}

**用户需求：**
{user_requirements if user_requirements else "未提供用户需求"}

**项目规划：**
{short_planning if short_planning else "未提供项目规划"}

**推荐工具：**
{tools_info if tools_info else "无推荐工具"}

**技术调研结果：**
{research_findings.get('research_summary', '无技术调研结果')}

**Agent分析结果：**
{analysis_markdown}

**识别的Node列表：**
{nodes_markdown}

**Flow设计：**
{flow_markdown}

**数据结构设计：**
{data_structure_markdown}

**详细Node设计：**
{node_design_markdown}

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
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content if response.choices else ""
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
