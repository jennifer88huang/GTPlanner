"""
Flow Design Node

第三步：基于已识别的Node列表，设计pocketflow的Flow架构。
专注于设计Node之间的连接、Action驱动的转换逻辑。
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
import asyncio


class FlowDesignNode(AsyncNode):
    """Flow设计节点 - 设计pocketflow的Flow架构"""
    
    def __init__(self):
        super().__init__()
        self.name = "FlowDesignNode"
        self.description = "设计pocketflow的Flow架构和Node连接逻辑"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取已识别的Node列表"""
        try:
            # 获取markdown格式的设计结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")

            # 获取项目状态信息
            short_planning = shared.get("short_planning", "")
            user_requirements = shared.get("user_requirements", "")
            research_findings = shared.get("research_findings", {})
            recommended_tools = shared.get("recommended_tools", [])

            # 检查必需的输入
            if not analysis_markdown:
                return {"error": "缺少Agent分析结果"}

            if not nodes_markdown:
                return {"error": "缺少Node识别结果"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"Flow design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：设计Flow架构"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建Flow设计提示词
            prompt = self._build_flow_design_prompt(prep_result)

            # 异步调用LLM设计Flow，直接输出markdown
            flow_markdown = await self._design_flow_architecture(prompt)

            return {
                "flow_markdown": flow_markdown,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Flow design failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存Flow设计"""
        try:
            if "error" in exec_res:
                shared["flow_design_error"] = exec_res["error"]
                await emit_error(shared, f"❌ Flow设计失败: {exec_res['error']}")
                return "error"
            
            # 保存Flow设计markdown
            flow_markdown = exec_res["flow_markdown"]
            shared["flow_markdown"] = flow_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "flow_design",
                "status": "completed",
                "message": "Flow设计完成"
            })

            # 使用简化文件工具直接写入markdown
            from ....utils.simple_file_util import write_file_directly
            await write_file_directly("03_flow_design.md", flow_markdown, shared)

            await emit_processing_status(shared, "✅ Flow设计完成")

            return "flow_designed"

        except Exception as e:
            shared["flow_design_post_error"] = str(e)
            await emit_error(shared, f"❌ Flow设计后处理失败: {str(e)}")
            return "error"
    
    def _build_flow_design_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建Flow设计提示词"""
        analysis_markdown = prep_result.get("analysis_markdown", "")
        nodes_markdown = prep_result.get("nodes_markdown", "")
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
                    tool_name = tool.get("name", tool.get("id", "未知工具"))
                    tool_type = tool.get("type", "")
                    tool_summary = tool.get("summary", tool.get("description", ""))
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

        prompt = f"""基于以下已识别的Node列表，设计完整的Flow编排。

**Agent分析结果：**
{analysis_markdown}

**已识别的Node列表：**
{nodes_markdown}

**用户需求：**
{user_requirements if user_requirements else "未提供用户需求"}

**项目规划：**
{short_planning if short_planning else "未提供项目规划"}

**技术调研结果：**
{research_info if research_info else "未提供技术调研结果"}

**推荐工具：**
{tools_info if tools_info else "无推荐工具"}

请分析上述信息，设计出完整的Flow编排方案。"""
        
        return prompt
    
    async def _design_flow_architecture(self, prompt: str) -> str:
        """调用LLM设计Flow架构"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的pocketflow架构设计师，专门设计基于pocketflow框架的Flow编排。

请严格按照以下Markdown格式输出Flow设计结果：

# Flow设计结果

## Flow概述
- **Flow名称**: [Flow名称]
- **Flow描述**: [Flow的整体描述]
- **起始节点**: [起始节点名称，必须来自已识别的Node列表]

## Flow图表

```mermaid
flowchart TD
    [在这里生成完整的Mermaid flowchart TD代码]
```

## 节点连接关系

### 连接 1
- **源节点**: [源节点名称]
- **目标节点**: [目标节点名称]
- **触发Action**: [default或具体action名]
- **转换条件**: [转换条件描述]
- **传递数据**: [传递的数据描述]

## 执行流程

### 步骤 1
- **节点**: [节点名称]
- **描述**: [此步骤的作用]
- **输入数据**: [输入数据来源]
- **输出数据**: [输出数据去向]

## 设计理由
[Flow编排的设计理由]

编排要求：
1. 只能使用已识别的Node列表中的Node
2. 确保数据流的完整性和逻辑性
3. 使用Action驱动的转换逻辑
4. 考虑错误处理和分支逻辑
5. Mermaid图要清晰展示所有连接和数据流
6. 确保每个Node都有明确的前置和后置关系

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
    

