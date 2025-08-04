"""
需求解析节点 (Node_Req)

从自然语言对话中提取结构化的需求信息。
基于架构文档中定义的输入输出规格实现。

功能描述：
- 文本预处理和分词
- 实体识别和分类  
- 意图识别和功能点提取
- 约束条件识别
- 结果结构化和置信度评估
"""

import json
import asyncio
import sys
import os
from typing import Dict, List, Any, Optional
from pocketflow import Node
from ..shared import get_shared_state, DialogueMessage

# 添加utils路径以导入call_llm
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from call_llm import call_llm_async


class NodeReq(Node):
    """需求解析节点 - 完全基于LLM进行需求分析"""

    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化需求解析节点

        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
    
    def prep(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从共享状态获取对话文本
        
        Args:
            shared: 共享状态对象
            
        Returns:
            准备结果字典
        """
        try:
            # 获取对话历史
            dialogue_history = shared.dialogue_history.messages
            
            # 提取用户消息
            user_messages = [msg for msg in dialogue_history if msg.role == "user"]
            
            if not user_messages:
                return {
                    "error": "No user messages found",
                    "dialogue_text": "",
                    "context_history": [],
                    "extraction_focus": ["entities", "functions", "constraints"]
                }
            
            # 合并所有用户消息作为对话文本
            dialogue_text = " ".join([msg.content for msg in user_messages])
            
            # 构建上下文历史
            context_history = [msg.content for msg in dialogue_history[-5:]]  # 最近5条消息
            
            return {
                "dialogue_text": dialogue_text,
                "context_history": context_history,
                "extraction_focus": ["entities", "functions", "constraints"],
                "message_count": len(user_messages),
                "total_length": len(dialogue_text)
            }
            
        except Exception as e:
            return {
                "error": f"Preparation failed: {str(e)}",
                "dialogue_text": "",
                "context_history": [],
                "extraction_focus": []
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：使用LLM执行需求解析

        Args:
            prep_res: 准备阶段的结果

        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])

        dialogue_text = prep_res["dialogue_text"]

        if not dialogue_text.strip():
            raise ValueError("Empty dialogue text")

        try:
            # 使用LLM进行需求分析
            analysis_result = asyncio.run(self._analyze_requirements_with_llm(dialogue_text))

            return {
                "extracted_entities": analysis_result.get("extracted_entities", {}),
                "functional_requirements": analysis_result.get("functional_requirements", {}),
                "non_functional_requirements": analysis_result.get("non_functional_requirements", {}),
                "confidence_score": analysis_result.get("confidence_score", 0.5),
                "processed_text_length": len(dialogue_text),
                "extraction_metadata": {
                    "processing_time": analysis_result.get("processing_time", 0),
                    "text_complexity": analysis_result.get("text_complexity", "medium"),
                    "extraction_method": "llm_based_analysis"
                },
                "user_intent": analysis_result.get("user_intent", {}),
                "project_overview": analysis_result.get("project_overview", {})
            }

        except Exception as e:
            raise RuntimeError(f"LLM requirement extraction failed: {str(e)}")

    async def _analyze_requirements_with_llm(self, dialogue_text: str) -> Dict[str, Any]:
        """使用LLM分析需求"""

        prompt = f"""
请分析以下用户需求对话，提取结构化的需求信息。请以JSON格式返回分析结果。

用户对话内容：
{dialogue_text}

请按照以下JSON结构返回分析结果：
{{
    "extracted_entities": {{
        "business_objects": ["实体1", "实体2"],
        "actors": ["角色1", "角色2"],
        "systems": ["系统1", "系统2"]
    }},
    "functional_requirements": {{
        "core_features": ["功能1", "功能2"],
        "user_stories": ["用户故事1", "用户故事2"],
        "workflows": ["工作流1", "工作流2"]
    }},
    "non_functional_requirements": {{
        "performance": ["性能要求1", "性能要求2"],
        "security": ["安全要求1", "安全要求2"],
        "scalability": ["扩展性要求1", "扩展性要求2"]
    }},
    "user_intent": {{
        "primary_goal": "主要目标",
        "intent_category": "planning/analysis/design/research",
        "domain_context": "领域上下文",
        "complexity_level": "simple/medium/complex",
        "estimated_effort": "low/medium/high"
    }},
    "project_overview": {{
        "title": "项目标题",
        "description": "项目描述",
        "scope": "项目范围",
        "objectives": ["目标1", "目标2"],
        "success_criteria": ["成功标准1", "成功标准2"]
    }},
    "confidence_score": 0.8,
    "text_complexity": "medium",
    "processing_time": 1000
}}

请确保：
1. 仔细分析用户的真实需求，不要添加用户没有提到的内容
2. 提取的实体、功能、角色等都应该基于用户的实际描述
3. 置信度应该基于需求描述的清晰程度和完整性
4. 所有字段都必须填写，如果某个方面用户没有明确提及，可以填写空数组或合理的默认值
"""

        try:
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            # 如果LLM调用失败，返回基本的结构
            return {
                "extracted_entities": {"business_objects": [], "actors": ["用户"], "systems": ["系统"]},
                "functional_requirements": {"core_features": ["基础功能"], "user_stories": [], "workflows": []},
                "non_functional_requirements": {"performance": [], "security": [], "scalability": []},
                "user_intent": {
                    "primary_goal": "系统开发需求",
                    "intent_category": "planning",
                    "domain_context": "通用",
                    "complexity_level": "medium",
                    "estimated_effort": "medium"
                },
                "project_overview": {
                    "title": "用户需求项目",
                    "description": "基于用户对话的项目需求",
                    "scope": "待明确",
                    "objectives": [],
                    "success_criteria": []
                },
                "confidence_score": 0.1,
                "text_complexity": "unknown",
                "processing_time": 0
            }

    def post(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将LLM分析结果更新到共享状态

        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果

        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared.record_error(Exception(exec_res["error"]), "NodeReq.exec")
                return "error"

            # 更新用户意图（从LLM分析结果中获取）
            user_intent_data = exec_res.get("user_intent", {})
            shared.user_intent.primary_goal = user_intent_data.get("primary_goal", "")
            shared.user_intent.intent_category = user_intent_data.get("intent_category", "planning")
            shared.user_intent.confidence_level = exec_res.get("confidence_score", 0.5)
            shared.user_intent.domain_context = user_intent_data.get("domain_context", "")
            shared.user_intent.complexity_level = user_intent_data.get("complexity_level", "medium")
            shared.user_intent.estimated_effort = user_intent_data.get("estimated_effort", "medium")
            shared.user_intent.last_updated = shared.dialogue_history.last_activity

            # 从实体中提取关键词
            entities = exec_res.get("extracted_entities", {})
            keywords = []
            keywords.extend(entities.get("business_objects", []))
            keywords.extend(entities.get("actors", []))
            keywords.extend(entities.get("systems", []))
            shared.user_intent.extracted_keywords = keywords[:10]  # 限制数量

            # 更新项目概览（从LLM分析结果中获取）
            project_overview_data = exec_res.get("project_overview", {})
            shared.structured_requirements.project_overview.title = project_overview_data.get("title", "")
            shared.structured_requirements.project_overview.description = project_overview_data.get("description", "")
            shared.structured_requirements.project_overview.scope = project_overview_data.get("scope", "")
            shared.structured_requirements.project_overview.objectives = project_overview_data.get("objectives", [])
            shared.structured_requirements.project_overview.success_criteria = project_overview_data.get("success_criteria", [])

            # 更新功能需求
            func_reqs = exec_res.get("functional_requirements", {})
            for feature_name in func_reqs.get("core_features", []):
                shared.structured_requirements.functional_requirements.add_feature(
                    name=feature_name,
                    description=f"基于用户需求分析的{feature_name}",
                    priority="medium"
                )

            # 更新非功能需求
            non_func_reqs = exec_res.get("non_functional_requirements", {})
            for perf_req in non_func_reqs.get("performance", []):
                shared.structured_requirements.non_functional_requirements.add_performance_requirement("general", perf_req)
            for sec_req in non_func_reqs.get("security", []):
                shared.structured_requirements.non_functional_requirements.add_security_requirement("general", sec_req)

            # 设置分析元数据
            shared.structured_requirements.analysis_metadata = {
                "created_by": "NodeReq",
                "created_at": shared.dialogue_history.last_activity,
                "version": "1.0",
                "validation_status": "extracted",
                "confidence_score": exec_res.get("confidence_score", 0.5),
                "extraction_metadata": exec_res.get("extraction_metadata", {}),
                "llm_analysis": True
            }

            # 添加系统消息记录处理结果
            shared.add_system_message(
                f"LLM需求解析完成，置信度: {exec_res.get('confidence_score', 0.5):.2f}",
                agent_source="NodeReq",
                entities_count=len(entities.get("business_objects", [])),
                features_count=len(func_reqs.get("core_features", [])),
                llm_analysis=True
            )

            return "success"

        except Exception as e:
            shared.record_error(e, "NodeReq.post")
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
        return {
            "extracted_entities": {
                "business_objects": [],
                "actors": ["用户"],  # 默认至少有用户
                "systems": ["系统"]   # 默认至少有系统
            },
            "functional_requirements": {
                "core_features": ["基础功能"],
                "user_stories": [],
                "workflows": []
            },
            "non_functional_requirements": {
                "performance": [],
                "security": [],
                "scalability": []
            },
            "user_intent": {
                "primary_goal": "系统开发需求",
                "intent_category": "planning",
                "domain_context": "通用",
                "complexity_level": "medium",
                "estimated_effort": "medium"
            },
            "project_overview": {
                "title": "需求分析失败",
                "description": "由于分析失败，无法提取详细需求",
                "scope": "待明确",
                "objectives": [],
                "success_criteria": []
            },
            "confidence_score": 0.1,
            "fallback_reason": str(exc),
            "extraction_metadata": {
                "processing_time": 0,
                "text_complexity": "unknown",
                "extraction_method": "fallback"
            }
        }
