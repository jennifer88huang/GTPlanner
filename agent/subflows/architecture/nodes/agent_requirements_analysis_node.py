"""
Agent Requirements Analysis Node

第一步：分析需求，明确要设计的Agent类型和核心功能。
专注于理解用户需求，确定Agent的定位和主要职责。
"""

import time
import json
import time
from typing import Dict, Any
from pocketflow import Node

# 导入LLM调用工具
from agent.common import call_llm_async
import asyncio


class AgentRequirementsAnalysisNode(Node):
    """Agent需求分析节点 - 理解和分析Agent设计需求"""
    
    def __init__(self):
        super().__init__()
        self.name = "AgentRequirementsAnalysisNode"
        self.description = "分析Agent设计需求，明确Agent类型和核心功能"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
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
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：分析Agent需求"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建分析提示词
            prompt = self._build_analysis_prompt(prep_result)
            
            # 调用LLM分析需求 - 修复异步事件循环冲突
            analysis_result = self._analyze_agent_requirements_sync(prompt)
            
            # 解析分析结果
            agent_analysis = self._parse_analysis_result(analysis_result)
            
            return {
                "agent_analysis": agent_analysis,
                "raw_analysis": analysis_result,
                "analysis_success": True
            }
            
        except Exception as e:
            return {"error": f"Agent requirements analysis failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存分析结果"""
        try:
            if "error" in exec_res:
                shared["agent_analysis_error"] = exec_res["error"]
                print(f"❌ Agent需求分析失败: {exec_res['error']}")
                return "error"
            
            # 保存分析结果
            agent_analysis = exec_res["agent_analysis"]
            shared["agent_analysis"] = agent_analysis
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "agent_requirements_analysis",
                "status": "completed",
                "message": f"Agent需求分析完成：{agent_analysis.get('agent_type', 'Unknown')} Agent"
            })

            # 生成文件输出
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("agent_analysis", agent_analysis, shared)

            print(f"✅ Agent需求分析完成")
            print(f"   Agent类型: {agent_analysis.get('agent_type', 'Unknown')}")
            print(f"   核心功能: {len(agent_analysis.get('core_functions', []))}个")

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
        
        # 提取项目信息
        project_overview = structured_requirements.get("project_overview", {})
        functional_requirements = structured_requirements.get("functional_requirements", {})
        
        prompt = f"""你是一个专业的AI Agent设计专家。请基于已经结构化的需求分析，明确要设计的Agent类型和核心功能。

**项目概述：**
{json.dumps(project_overview, indent=2, ensure_ascii=False)}

**功能需求：**
{json.dumps(functional_requirements, indent=2, ensure_ascii=False)}

**研究发现：**
{research_findings.get('research_summary', '无研究发现')}

**确认文档：**
{prep_result.get('confirmation_document', '无确认文档')}

请分析并输出JSON格式的结果，包含以下字段：

{{
    "agent_type": "Agent类型（如：对话Agent、分析Agent、推荐Agent等）",
    "agent_purpose": "Agent的主要目的和价值",
    "core_functions": [
        {{
            "function_name": "功能名称",
            "description": "功能描述",
            "complexity": "简单/中等/复杂",
            "priority": "高/中/低"
        }}
    ],
    "input_types": ["输入数据类型1", "输入数据类型2"],
    "output_types": ["输出数据类型1", "输出数据类型2"],
    "processing_pattern": "处理模式（如：流水线、批处理、实时响应等）",
    "key_challenges": ["主要技术挑战1", "主要技术挑战2"],
    "success_criteria": ["成功标准1", "成功标准2"]
}}

请确保分析结果专注于Agent的核心能力和处理逻辑，为后续的Flow和Node设计提供清晰的指导。

**重要：请严格按照上述JSON格式输出，不要添加任何额外的文字说明、代码块标记或其他内容。直接输出纯JSON数据。**"""
        
        return prompt
    
    def _analyze_agent_requirements_sync(self, prompt: str) -> str:
        """调用LLM分析Agent需求"""
        try:
            # 导入同步版本的LLM调用
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'utils'))
            from call_llm import call_llm

            # 使用同步版本调用LLM
            result = call_llm(prompt, is_json=True)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")



  
    
    def _parse_analysis_result(self, analysis_result: str) -> Dict[str, Any]:
        """解析分析结果"""
        try:
            # 尝试解析JSON
            if isinstance(analysis_result, str):
                agent_analysis = json.loads(analysis_result)
            else:
                agent_analysis = analysis_result
            
            # 验证必需字段
            required_fields = ["agent_type", "agent_purpose", "core_functions"]
            for field in required_fields:
                if field not in agent_analysis:
                    agent_analysis[field] = f"未指定{field}"
            
            # 确保core_functions是列表
            if not isinstance(agent_analysis.get("core_functions"), list):
                agent_analysis["core_functions"] = []
            
            return agent_analysis
            
        except json.JSONDecodeError as e:
            raise Exception(f"Agent需求分析JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"Agent需求分析结果解析失败: {e}")
