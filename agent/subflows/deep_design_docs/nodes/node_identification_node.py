"""
Node Identification Node

第二步：基于Agent需求分析，确定需要哪些Node。
专注于识别完成Agent功能所需的所有Node，为后续Flow编排提供基础。
"""

import time
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入OpenAI客户端
from utils.openai_client import get_openai_client
from agent.streaming import (
    emit_processing_status,
    emit_error
)


class NodeIdentificationNode(AsyncNode):
    """Node识别节点 - 确定Agent需要的所有Node"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeIdentificationNode"
        self.description = "基于Agent需求分析，识别需要的所有Node"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取Agent分析结果"""
        try:
            # 获取Agent分析markdown结果
            analysis_markdown = shared.get("analysis_markdown", "")

            # 获取项目状态信息
            short_planning = shared.get("short_planning", "")
            user_requirements = shared.get("user_requirements", "")
            research_findings = shared.get("research_findings", {})
            recommended_tools = shared.get("recommended_tools", [])

            # 检查必需的输入
            if not analysis_markdown:
                return {"error": "缺少Agent分析结果"}

            return {
                "analysis_markdown": analysis_markdown,
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node identification preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：识别所需的Node"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建Node识别提示词
            prompt = self._build_node_identification_prompt(prep_result)

            # 调用LLM识别Node，直接输出markdown
            nodes_markdown = await self._identify_nodes(prompt)

            return {
                "nodes_markdown": nodes_markdown,
                "identification_success": True
            }
            
        except Exception as e:
            return {"error": f"Node identification failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存识别的Node列表"""
        try:
            if "error" in exec_res:
                shared["node_identification_error"] = exec_res["error"]
                print(f"❌ Node识别失败: {exec_res['error']}")
                return "error"
            
            # 保存markdown内容
            nodes_markdown = exec_res["nodes_markdown"]
            shared["nodes_markdown"] = nodes_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_identification",
                "status": "completed",
                "message": "Node识别完成"
            })

            # 使用简化文件工具直接写入markdown
            from ....utils.simple_file_util import write_file_directly
            await write_file_directly("02_identified_nodes.md", nodes_markdown, shared)

            await emit_processing_status(shared, "✅ Node识别完成")

            return "nodes_identified"

        except Exception as e:
            shared["node_identification_post_error"] = str(e)
            await emit_error(shared, f"❌ Node识别后处理失败: {str(e)}")
            return "error"
    
    def _build_node_identification_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建Node识别提示词"""
        analysis_markdown = prep_result.get("analysis_markdown", "")
        short_planning = prep_result.get("short_planning", "")
        user_requirements = prep_result.get("user_requirements", "")
        research_findings = prep_result.get("research_findings", {})
        recommended_tools = prep_result.get("recommended_tools", [])

        # 构建推荐工具信息
        tools_info = ""
        if recommended_tools:
            tools_list = []
            for tool in recommended_tools:
                # 添加 None 检查，防止 tool 为 None
                if tool and isinstance(tool, dict):
                    # 安全获取工具名称
                    tool_name = tool.get("name") or tool.get("id", "未知工具")
                    tool_type = tool.get("type", "")
                    # 安全获取工具摘要
                    tool_summary = tool.get("summary") or tool.get("description", "")
                    tools_list.append(f"- {tool_name} ({tool_type}): {tool_summary}")
            tools_info = "\n".join(tools_list)

        # 构建技术调研信息
        research_info = ""
        if research_findings and isinstance(research_findings, dict):
            # 使用正确的字段名
            if research_findings.get("summary"):
                research_info += f"**调研摘要：**\n{research_findings['summary']}\n\n"

            # 从关键词结果中提取关键信息
            keyword_results = research_findings.get("keyword_results", [])
            if keyword_results:
                successful_results = [r for r in keyword_results if r.get("success", False)]
                if successful_results:
                    research_info += "**关键发现：**\n"
                    for result in successful_results[:3]:  # 只显示前3个结果
                        keyword = result.get("keyword", "")
                        result_data = result.get("result", {})
                        if result_data and result_data.get("summary"):
                            research_info += f"- {keyword}: {result_data['summary'][:100]}...\n"
                    research_info += "\n"

        prompt = f"""基于以下Agent需求分析结果，识别完成此Agent功能所需的所有Node。

**Agent分析结果：**
{analysis_markdown}

**用户需求：**
{user_requirements if user_requirements else "未提供用户需求"}

**项目规划：**
{short_planning if short_planning else "未提供项目规划"}

**技术调研结果：**
{research_info if research_info else "未提供技术调研结果"}

**推荐工具：**
{tools_info if tools_info else "无推荐工具"}

请分析上述信息，识别出完整实现Agent功能所需的所有Node。"""
        
        return prompt
    
    async def _identify_nodes(self, prompt: str) -> str:
        """调用LLM识别Node"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的pocketflow架构师，专门识别和设计基于pocketflow框架的Node。

请严格按照以下Markdown格式输出Node识别结果：

# Node识别结果

## 概述
基于Agent需求分析，识别出以下Node：

## 识别的Node列表

### 1. [Node名称1]

- **Node类型**: [Node/AsyncNode/BatchNode等]
- **目的**: [Node的具体目的和职责]
- **职责**: [Node负责的具体功能]
- **输入期望**: [期望的输入数据类型]
- **输出期望**: [期望的输出数据类型]
- **复杂度**: [简单/中等/复杂]
- **处理类型**: [数据预处理/核心计算/结果后处理/IO操作等]
- **推荐重试**: [是/否]

### 2. [Node名称2]

- **Node类型**: [Node/AsyncNode/BatchNode等]
- **目的**: [Node的具体目的和职责]
- **职责**: [Node负责的具体功能]
- **输入期望**: [期望的输入数据类型]
- **输出期望**: [期望的输出数据类型]
- **复杂度**: [简单/中等/复杂]
- **处理类型**: [数据预处理/核心计算/结果后处理/IO操作等]
- **推荐重试**: [是/否]

## Node类型统计
- **AsyncNode**: [数量]个
- **Node**: [数量]个
- **BatchNode**: [数量]个

## 设计理由
[为什么选择这些Node的设计理由]

识别要求：
1. 每个Node都有明确的单一职责
2. Node之间职责不重叠
3. 覆盖Agent的所有核心功能
4. 考虑数据流的完整性（输入→处理→输出）
5. 优先使用AsyncNode提高性能
6. 考虑错误处理和重试需求

常见Node模式参考：
- InputValidationNode: 输入验证和预处理
- DataRetrievalNode: 数据获取和检索
- CoreProcessingNode: 核心业务逻辑处理
- ResultFormattingNode: 结果格式化
- OutputDeliveryNode: 结果输出和传递

重要：请严格按照上述Markdown格式输出，不要输出JSON格式！直接输出完整的Markdown文档。"""

            # 使用系统提示词调用LLM
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt
            )
            result = response.choices[0].message.content if response.choices else ""
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
