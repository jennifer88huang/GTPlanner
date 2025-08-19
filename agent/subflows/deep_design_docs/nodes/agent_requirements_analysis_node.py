"""
Agent Requirements Analysis Node

第一步：分析需求，明确要设计的Agent类型和核心功能。
专注于理解用户需求，确定Agent的定位和主要职责。
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


class AgentRequirementsAnalysisNode(AsyncNode):
    """Agent需求分析节点 - 理解和分析Agent设计需求"""
    
    def __init__(self):
        super().__init__()
        self.name = "AgentRequirementsAnalysisNode"
        self.description = "分析Agent设计需求，明确Agent类型和核心功能"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集需求信息"""
        try:
            # 获取短期规划结果（必需）
            short_planning = shared.get("short_planning", "")

            # 获取研究结果（可选）
            research_findings = shared.get("research_findings", {})

            # 获取推荐工具（可选）
            recommended_tools = shared.get("recommended_tools", [])

            # 检查必需的输入
            if not short_planning:
                return {"error": "缺少短期规划结果，无法进行架构分析"}

            return {
                "short_planning": short_planning,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Agent requirements analysis preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：分析Agent需求"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(prep_result)

            # 异步调用LLM分析需求，直接输出markdown
            analysis_markdown = await self._analyze_agent_requirements_async(prompt)

            return {
                "analysis_markdown": analysis_markdown,
                "analysis_success": True
            }
            
        except Exception as e:
            return {"error": f"Agent requirements analysis failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存分析结果"""
        try:
            if "error" in exec_res:
                shared["agent_analysis_error"] = exec_res["error"]
                print(f"❌ Agent需求分析失败: {exec_res['error']}")
                return "error"
            
            # 保存markdown内容
            analysis_markdown = exec_res["analysis_markdown"]
            shared["analysis_markdown"] = analysis_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "agent_requirements_analysis",
                "status": "completed",
                "message": "Agent需求分析完成"
            })

            # 使用简化文件工具直接写入markdown
            from ....utils.simple_file_util import write_file_directly
            await write_file_directly("01_agent_analysis.md", analysis_markdown, shared)

            await emit_processing_status(shared, "✅ Agent需求分析完成")

            return "analysis_complete"

        except Exception as e:
            shared["agent_analysis_post_error"] = str(e)
            await emit_error(shared, f"❌ Agent需求分析后处理失败: {str(e)}")
            return "error"
    
    def _build_analysis_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建需求分析提示词"""
        short_planning = prep_result["short_planning"]
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

        # 安全获取技术调研摘要
        research_summary = research_findings.get('summary', '无技术调研结果') if research_findings else '无技术调研结果'

        prompt = f"""基于以下信息，分析并明确要设计的Agent类型和核心功能。

**项目规划：**
{short_planning}

**推荐工具：**
{tools_info if tools_info else "无推荐工具"}

**技术调研结果：**
{research_summary}

请分析上述信息，生成完整的Agent需求分析报告。"""
        
        return prompt
    
    async def _analyze_agent_requirements_async(self, prompt: str) -> str:
        """异步调用LLM分析Agent需求"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的AI Agent设计专家，专门分析和设计基于pocketflow框架的Agent。

请严格按照以下Markdown格式输出Agent需求分析结果：

# Agent需求分析结果

## Agent基本信息
- **Agent类型**: [Agent类型，如：对话Agent、分析Agent、推荐Agent等]
- **Agent目的**: [Agent的主要目的和价值]
- **处理模式**: [处理模式，如：流水线、批处理、实时响应等]

## 核心功能

### 1. [功能名称1]
- **描述**: [功能详细描述]
- **复杂度**: [简单/中等/复杂]
- **优先级**: [高/中/低]

### 2. [功能名称2]
- **描述**: [功能详细描述]
- **复杂度**: [简单/中等/复杂]
- **优先级**: [高/中/低]

## 输入输出类型
- **输入类型**: [输入数据类型，用逗号分隔]
- **输出类型**: [输出数据类型，用逗号分隔]

## 技术挑战
- [主要技术挑战1]
- [主要技术挑战2]
- [其他挑战...]

## 成功标准
- [成功标准1]
- [成功标准2]
- [其他标准...]

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


