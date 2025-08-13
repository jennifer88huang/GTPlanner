"""
Agent Requirements Analysis Node

第一步：分析需求，明确要设计的Agent类型和核心功能。
专注于理解用户需求，确定Agent的定位和主要职责。
"""

import time
import json
import time
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入LLM调用工具
from agent.llm_utils import call_llm_async
import asyncio


class AgentRequirementsAnalysisNode(AsyncNode):
    """Agent需求分析节点 - 理解和分析Agent设计需求"""
    
    def __init__(self):
        super().__init__()
        self.name = "AgentRequirementsAnalysisNode"
        self.description = "分析Agent设计需求，明确Agent类型和核心功能"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集需求信息"""
        try:
            # 获取结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            
            # 获取研究结果
            research_findings = shared.get("research_findings", {})
            
            # 获取确认文档
            confirmation_document = shared.get("confirmation_document", "")
            
            # 获取用户原始输入
            user_input = shared.get("user_input", "")
            
            # 检查必需的输入
            if not structured_requirements:
                return {"error": "缺少结构化需求"}
            
            return {
                "structured_requirements": structured_requirements,
                "research_findings": research_findings,
                "confirmation_document": confirmation_document,
                "user_input": user_input,
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
            from ..utils.simple_file_util import write_file_directly
            write_file_directly("01_agent_analysis.md", analysis_markdown, shared)

            print(f"✅ Agent需求分析完成")

            return "analysis_complete"
            
        except Exception as e:
            shared["agent_analysis_post_error"] = str(e)
            print(f"❌ Agent需求分析后处理失败: {str(e)}")
            return "error"
    
    def _build_analysis_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建需求分析提示词"""
        structured_requirements = prep_result["structured_requirements"]
        research_findings = prep_result.get("research_findings", {})
        user_input = prep_result.get("user_input", "")
        

        prompt = f"""基于以下信息，分析并明确要设计的Agent类型和核心功能。

**结构化需求：**
{json.dumps(structured_requirements, indent=2, ensure_ascii=False)}

**研究发现：**
{research_findings.get('research_summary', '无研究发现')}

**确认文档：**
{prep_result.get('confirmation_document', '无确认文档')}

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
            result = await call_llm_async(prompt, is_json=False, system_prompt=system_prompt)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")


