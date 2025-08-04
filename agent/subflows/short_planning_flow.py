"""
短规划Agent子流程 (Short Planning Flow)

生成项目规划并与用户确认，确保需求理解的一致性。
完全基于LLM进行规划生成和确认文档格式化。

流程步骤：
1. 需求理解和分析
2. 生成执行规划
3. 格式化确认文档
4. 用户确认处理
"""

import asyncio
import sys
import os
from typing import Dict, Any, Optional
from pocketflow import Flow
from ..shared import get_shared_state

# 添加utils路径以导入call_llm
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from call_llm import call_llm_async


class ShortPlanningFlow(Flow):
    """短规划Agent子流程 - 完全基于LLM进行规划生成"""
    
    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化短规划流程
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
    
    def prep(self, shared_state=None) -> Dict[str, Any]:
        """
        准备阶段：验证需求数据并设置规划参数
        
        Args:
            shared_state: 共享状态对象
            
        Returns:
            准备结果字典
        """
        try:
            # 获取共享状态
            if shared_state is None:
                shared_state = get_shared_state()
            
            # 验证是否有结构化需求
            if not hasattr(shared_state, 'structured_requirements'):
                return {
                    "error": "No structured requirements available for planning",
                    "shared_state": shared_state,
                    "planning_config": {
                        "planning_depth": "detailed",
                        "include_timeline": True,
                        "include_resources": True,
                        "require_user_confirmation": True
                    }
                }
            
            # 检查需求完整性
            requirements = shared_state.structured_requirements
            if not requirements.project_overview.title:
                return {
                    "error": "Incomplete requirements: missing project title",
                    "shared_state": shared_state,
                    "planning_config": {
                        "planning_depth": "basic",
                        "include_timeline": False,
                        "include_resources": False,
                        "require_user_confirmation": True
                    }
                }
            
            # 规划配置
            planning_config = {
                "planning_depth": "detailed",
                "include_timeline": True,
                "include_resources": True,
                "include_risks": True,
                "require_user_confirmation": True,
                "max_planning_time": 90000  # 90秒
            }
            
            # 提取需求摘要用于规划
            requirements_summary = self._extract_requirements_summary(requirements)
            
            return {
                "shared_state": shared_state,
                "planning_config": planning_config,
                "requirements_summary": requirements_summary,
                "user_intent": shared_state.user_intent.__dict__ if hasattr(shared_state, 'user_intent') else {}
            }
            
        except Exception as e:
            return {
                "error": f"Short planning flow preparation failed: {str(e)}",
                "shared_state": shared_state or get_shared_state(),
                "planning_config": {
                    "planning_depth": "basic",
                    "include_timeline": False,
                    "include_resources": False,
                    "require_user_confirmation": True
                }
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：生成项目规划和确认文档
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        shared_state = prep_res["shared_state"]
        planning_config = prep_res["planning_config"]
        requirements_summary = prep_res["requirements_summary"]
        user_intent = prep_res["user_intent"]
        
        try:
            # 更新处理阶段
            shared_state.update_stage("short_planning_started")
            
            # 步骤1: 使用LLM生成项目规划
            planning_result = asyncio.run(self._generate_planning_with_llm(
                requirements_summary, user_intent, planning_config
            ))
            
            # 步骤2: 格式化确认文档
            confirmation_document = asyncio.run(self._format_confirmation_document(
                planning_result, planning_config
            ))
            
            # 步骤3: 验证规划质量
            validation_result = self._validate_planning_result(planning_result, planning_config)
            
            # 更新处理阶段
            shared_state.update_stage("short_planning_completed")
            
            return {
                "planning_result": planning_result,
                "confirmation_document": confirmation_document,
                "validation_result": validation_result,
                "flow_status": "completed",
                "planning_quality_score": validation_result.get("quality_score", 0.5),
                "requires_user_confirmation": planning_config.get("require_user_confirmation", True),
                "planning_summary": {
                    "total_phases": len(planning_result.get("execution_phases", [])),
                    "estimated_duration": planning_result.get("timeline_overview", {}).get("total_estimated_time", "未估算"),
                    "key_milestones": len(planning_result.get("timeline_overview", {}).get("milestone_dates", {})),
                    "identified_risks": len(planning_result.get("risk_assessment", {}).get("identified_risks", []))
                }
            }
            
        except Exception as e:
            # 记录错误到共享状态
            shared_state.record_error(e, "ShortPlanningFlow.exec")
            shared_state.update_stage("short_planning_failed")
            raise RuntimeError(f"Short planning flow execution failed: {str(e)}")
    
    def post(self, shared_state, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：保存规划结果并准备用户确认
        
        Args:
            shared_state: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared_state.record_error(Exception(exec_res["error"]), "ShortPlanningFlow.exec")
                return "error"
            
            # 保存规划结果到共享状态
            if not hasattr(shared_state, 'project_planning'):
                shared_state.project_planning = {}
            
            shared_state.project_planning = {
                "planning_result": exec_res["planning_result"],
                "confirmation_document": exec_res["confirmation_document"],
                "validation_result": exec_res["validation_result"],
                "created_at": shared_state.dialogue_history.last_activity,
                "status": "pending_confirmation"
            }
            
            # 添加流程完成的系统消息
            planning_summary = exec_res.get("planning_summary", {})
            quality_score = exec_res.get("planning_quality_score", 0.5)
            
            shared_state.add_system_message(
                f"项目规划生成完成，质量评分: {quality_score:.2f}，"
                f"包含 {planning_summary.get('total_phases', 0)} 个执行阶段，"
                f"预估时长: {planning_summary.get('estimated_duration', '未估算')}",
                agent_source="ShortPlanningFlow",
                flow_status=exec_res.get("flow_status", "completed"),
                quality_score=quality_score,
                requires_confirmation=exec_res.get("requires_user_confirmation", True)
            )
            
            # 如果需要用户确认，返回确认状态
            if exec_res.get("requires_user_confirmation", True):
                return "require_user_confirmation"
            else:
                return "proceed_to_research"
            
        except Exception as e:
            shared_state.record_error(e, "ShortPlanningFlow.post")
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
        shared_state = prep_res.get("shared_state")
        if shared_state:
            shared_state.update_stage("short_planning_fallback")
        
        # 生成基本的规划结果
        basic_planning = {
            "planning_approach": "basic",
            "execution_phases": [
                {
                    "phase_id": "phase_1",
                    "phase_name": "需求分析",
                    "description": "分析和确认项目需求",
                    "estimated_duration": "1-2周"
                },
                {
                    "phase_id": "phase_2", 
                    "phase_name": "设计开发",
                    "description": "系统设计和开发实现",
                    "estimated_duration": "4-6周"
                },
                {
                    "phase_id": "phase_3",
                    "phase_name": "测试部署",
                    "description": "测试验证和系统部署",
                    "estimated_duration": "1-2周"
                }
            ],
            "timeline_overview": {
                "total_estimated_time": "6-10周",
                "critical_path": ["需求分析", "设计开发", "测试部署"]
            }
        }
        
        basic_confirmation = {
            "document_structure": {
                "executive_summary": "由于规划生成失败，提供基础项目规划",
                "project_scope": "基于现有需求的基础项目范围",
                "key_deliverables": ["需求文档", "系统设计", "实现代码", "测试报告"],
                "timeline_summary": "预计6-10周完成",
                "next_steps": ["确认需求", "开始设计", "制定详细计划"]
            }
        }
        
        return {
            "planning_result": basic_planning,
            "confirmation_document": basic_confirmation,
            "validation_result": {"quality_score": 0.2, "issues": ["规划生成失败"], "warnings": []},
            "flow_status": "fallback",
            "planning_quality_score": 0.2,
            "requires_user_confirmation": True,
            "planning_summary": {
                "total_phases": 3,
                "estimated_duration": "6-10周",
                "key_milestones": 0,
                "identified_risks": 0
            },
            "fallback_reason": str(exc)
        }
    
    def _extract_requirements_summary(self, requirements) -> Dict[str, Any]:
        """从结构化需求中提取摘要信息"""
        return {
            "project_title": requirements.project_overview.title,
            "project_description": requirements.project_overview.description,
            "project_scope": requirements.project_overview.scope,
            "objectives": requirements.project_overview.objectives,
            "core_features": [feature.name for feature in requirements.functional_requirements.core_features],
            "success_criteria": requirements.project_overview.success_criteria,
            "constraints": requirements.constraints
        }
    
    async def _generate_planning_with_llm(self, requirements_summary: Dict[str, Any], 
                                         user_intent: Dict[str, Any], 
                                         planning_config: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM生成项目规划"""
        
        prompt = f"""
请基于以下项目需求生成详细的执行规划。

项目需求摘要：
{requirements_summary}

用户意图：
{user_intent}

规划配置：
- 规划深度：{planning_config.get('planning_depth', 'detailed')}
- 包含时间线：{planning_config.get('include_timeline', True)}
- 包含资源：{planning_config.get('include_resources', True)}
- 包含风险：{planning_config.get('include_risks', True)}

请以JSON格式返回项目规划：
{{
    "planning_approach": "agile/waterfall/hybrid",
    "execution_phases": [
        {{
            "phase_id": "phase_1",
            "phase_name": "阶段名称",
            "description": "阶段描述",
            "deliverables": ["交付物1", "交付物2"],
            "estimated_duration": "预估时长",
            "dependencies": ["依赖项"],
            "risks": ["风险点"],
            "success_criteria": ["成功标准"]
        }}
    ],
    "resource_requirements": {{
        "human_resources": ["人力资源需求"],
        "technical_resources": ["技术资源需求"],
        "external_dependencies": ["外部依赖"]
    }},
    "timeline_overview": {{
        "total_estimated_time": "总预估时间",
        "critical_path": ["关键路径"],
        "milestone_dates": {{"里程碑1": "日期"}},
        "buffer_time": "缓冲时间"
    }},
    "risk_assessment": {{
        "identified_risks": ["风险1", "风险2"],
        "mitigation_strategies": ["缓解策略1", "缓解策略2"],
        "contingency_plans": ["应急计划"]
    }},
    "quality_assurance": {{
        "review_points": ["评审点"],
        "testing_strategy": "测试策略",
        "validation_methods": ["验证方法"]
    }}
}}

请确保：
1. 规划切实可行，符合项目实际情况
2. 时间估算合理，考虑项目复杂度
3. 识别主要风险点和缓解措施
4. 明确各阶段的交付物和成功标准
5. 考虑资源约束和外部依赖
"""
        
        try:
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            # 如果LLM调用失败，返回基本规划
            return {
                "planning_approach": "hybrid",
                "execution_phases": [
                    {
                        "phase_id": "phase_1",
                        "phase_name": "项目启动",
                        "description": "项目初始化和需求确认",
                        "deliverables": ["需求文档"],
                        "estimated_duration": "1-2周",
                        "dependencies": [],
                        "risks": ["需求变更"],
                        "success_criteria": ["需求确认完成"]
                    }
                ],
                "resource_requirements": {
                    "human_resources": ["项目经理", "开发人员"],
                    "technical_resources": ["开发环境"],
                    "external_dependencies": []
                },
                "timeline_overview": {
                    "total_estimated_time": "待评估",
                    "critical_path": ["项目启动"],
                    "milestone_dates": {},
                    "buffer_time": "20%"
                },
                "risk_assessment": {
                    "identified_risks": ["规划生成失败"],
                    "mitigation_strategies": ["手动规划"],
                    "contingency_plans": ["简化流程"]
                },
                "quality_assurance": {
                    "review_points": ["阶段评审"],
                    "testing_strategy": "基础测试",
                    "validation_methods": ["人工验证"]
                }
            }
    
    async def _format_confirmation_document(self, planning_result: Dict[str, Any], 
                                           planning_config: Dict[str, Any]) -> Dict[str, Any]:
        """格式化确认文档"""
        
        prompt = f"""
请将以下项目规划格式化为用户友好的确认文档。

项目规划：
{planning_result}

请以JSON格式返回确认文档：
{{
    "document_structure": {{
        "executive_summary": "执行摘要，简明扼要地描述项目规划要点",
        "project_scope": "项目范围说明",
        "key_deliverables": ["关键交付物列表"],
        "timeline_summary": "时间线摘要",
        "resource_overview": "资源需求概览",
        "risk_assessment": "风险评估摘要",
        "next_steps": ["下一步行动计划"]
    }},
    "user_interaction": {{
        "confirmation_points": [
            {{
                "point_id": "confirm_1",
                "question": "确认问题",
                "options": ["选项1", "选项2"],
                "importance": "critical/important/optional"
            }}
        ],
        "feedback_mechanisms": ["反馈方式"],
        "modification_options": ["可修改的方面"]
    }}
}}

请确保：
1. 语言简洁明了，易于理解
2. 突出关键信息和决策点
3. 提供明确的确认选项
4. 便于用户提供反馈和修改建议
"""
        
        try:
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            # 如果LLM调用失败，返回基本确认文档
            return {
                "document_structure": {
                    "executive_summary": "项目规划已生成，请确认是否符合您的期望",
                    "project_scope": "基于您的需求制定的项目范围",
                    "key_deliverables": ["需求文档", "设计方案", "实现代码"],
                    "timeline_summary": "预计数周完成",
                    "resource_overview": "需要开发团队支持",
                    "risk_assessment": "存在一般性项目风险",
                    "next_steps": ["确认规划", "开始执行"]
                },
                "user_interaction": {
                    "confirmation_points": [
                        {
                            "point_id": "confirm_1",
                            "question": "您是否同意这个项目规划？",
                            "options": ["同意", "需要修改", "重新规划"],
                            "importance": "critical"
                        }
                    ],
                    "feedback_mechanisms": ["文字反馈"],
                    "modification_options": ["时间调整", "范围调整", "资源调整"]
                }
            }
    
    def _validate_planning_result(self, planning_result: Dict[str, Any], 
                                 planning_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证规划结果的质量"""
        validation_result = {
            "quality_score": 0.5,
            "issues": [],
            "warnings": []
        }
        
        try:
            score = 0.0
            max_score = 5.0
            
            # 检查执行阶段
            phases = planning_result.get("execution_phases", [])
            if phases:
                score += 1.0
                if len(phases) >= 3:
                    score += 0.5
            else:
                validation_result["issues"].append("缺少执行阶段定义")
            
            # 检查时间线
            timeline = planning_result.get("timeline_overview", {})
            if timeline.get("total_estimated_time"):
                score += 1.0
            else:
                validation_result["warnings"].append("缺少总体时间估算")
            
            # 检查资源需求
            resources = planning_result.get("resource_requirements", {})
            if resources.get("human_resources") or resources.get("technical_resources"):
                score += 1.0
            else:
                validation_result["warnings"].append("缺少资源需求分析")
            
            # 检查风险评估
            risks = planning_result.get("risk_assessment", {})
            if risks.get("identified_risks"):
                score += 1.0
            else:
                validation_result["warnings"].append("缺少风险识别")
            
            # 检查质量保证
            qa = planning_result.get("quality_assurance", {})
            if qa.get("review_points") or qa.get("testing_strategy"):
                score += 0.5
            
            validation_result["quality_score"] = score / max_score
            
        except Exception as e:
            validation_result["issues"].append(f"验证过程出错: {str(e)}")
            validation_result["quality_score"] = 0.1
        
        return validation_result
