"""
Validation Node

验证确认文档的完整性和质量，确保规划内容完整且易于理解。
"""

import time
from typing import Dict, Any, List, Tuple
from pocketflow import AsyncNode
from agent.shared_migration import field_validation_decorator


class ValidationNode(AsyncNode):
    """验证节点 - 确保规划完整且易于理解"""
    
    def __init__(self):
        super().__init__()
        self.name = "ValidationNode"
        self.description = "验证确认文档的完整性和质量"
        
        # 验证配置
        self.validation_config = {
            "required_sections": [
                "项目概览", "执行计划", "交付物清单", "风险评估", "资源需求", "确认事项"
            ],
            "min_phases": 2,
            "max_phases": 8,
            "min_document_length": 500,
            "quality_thresholds": {
                "completeness": 0.7,
                "clarity": 0.6,
                "feasibility": 0.7
            }
        }
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取确认文档和相关数据"""
        try:
            # 获取确认文档
            confirmation_document = shared.get("confirmation_document", "")
            if not confirmation_document:
                return {"error": "No confirmation document found"}
            
            # 获取执行规划
            execution_plan = shared.get("execution_plan", {})
            
            # 获取规划摘要
            planning_summary = shared.get("planning_summary", {})
            
            return {
                "confirmation_document": confirmation_document,
                "execution_plan": execution_plan,
                "planning_summary": planning_summary,
                "validation_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Validation preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行验证"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            confirmation_document = prep_result["confirmation_document"]
            execution_plan = prep_result["execution_plan"]
            planning_summary = prep_result["planning_summary"]
            
            # 执行结构验证
            structure_validation = self._validate_structure(confirmation_document, execution_plan)
            
            # 执行内容验证
            content_validation = self._validate_content(execution_plan, planning_summary)
            
            # 执行质量评估
            quality_assessment = self._assess_quality(
                confirmation_document, execution_plan, planning_summary
            )
            
            # 生成验证报告
            validation_report = self._generate_validation_report(
                structure_validation, content_validation, quality_assessment
            )
            
            # 判断整体验证是否通过
            validation_passed = (
                structure_validation["is_valid"] and
                content_validation["is_complete"] and
                quality_assessment["overall_score"] >= 0.6
            )
            
            return {
                "validation_report": validation_report,
                "validation_passed": validation_passed,
                "structure_validation": structure_validation,
                "content_validation": content_validation,
                "quality_assessment": quality_assessment
            }
            
        except Exception as e:
            raise e
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存验证结果"""
        if "error" in exec_res:
            shared["validation_error"] = exec_res["error"]
            return "error"
        
        # 保存验证报告
        shared["planning_validation_report"] = exec_res["validation_report"]
        
        validation_passed = exec_res["validation_passed"]
        overall_score = exec_res["quality_assessment"]["overall_score"]
        
        print(f"✅ 规划验证完成，质量评分: {overall_score:.2f}, 验证{'通过' if validation_passed else '未通过'}")
        
        return "success" if validation_passed else "warning"
    
    def _validate_structure(self, document: Dict[str, Any], execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """验证文档结构 - 按照文档规范格式验证"""
        validation_result = {
            "is_valid": True,
            "missing_sections": [],
            "structure_issues": [],
            "section_count": 0
        }

        # 检查文档规范的必需字段
        required_structure_fields = [
            "document_structure", "presentation_format",
            "user_interaction", "document_metadata"
        ]

        for field in required_structure_fields:
            if field not in document:
                validation_result["missing_sections"].append(field)
                validation_result["is_valid"] = False

        # 检查document_structure的必需子字段
        if "document_structure" in document:
            doc_structure = document["document_structure"]
            required_doc_fields = [
                "executive_summary", "project_scope", "key_deliverables",
                "timeline_summary", "resource_overview", "risk_assessment", "next_steps"
            ]

            for field in required_doc_fields:
                if field not in doc_structure or not doc_structure[field]:
                    validation_result["missing_sections"].append(f"document_structure.{field}")
                    validation_result["is_valid"] = False

        # 检查阶段数量
        execution_phases = execution_plan.get("execution_phases", [])
        phases_count = len(execution_phases)

        if phases_count < self.validation_config["min_phases"]:
            validation_result["structure_issues"].append("项目阶段数量过少")
            validation_result["is_valid"] = False
        elif phases_count > self.validation_config["max_phases"]:
            validation_result["structure_issues"].append("项目阶段数量过多")

        # 统计结构完整性
        validation_result["section_count"] = len(required_structure_fields)

        return validation_result
    
    def _validate_content(self, execution_plan: Dict[str, Any], 
                         planning_summary: Dict[str, Any]) -> Dict[str, Any]:
        """验证内容完整性"""
        validation_result = {
            "is_complete": True,
            "missing_content": [],
            "content_issues": [],
            "completeness_score": 0.0
        }
        
        issues = []
        
        # 检查项目摘要
        project_summary = execution_plan.get("project_summary", {})
        if not project_summary.get("title"):
            issues.append("缺少项目标题")
        if not project_summary.get("duration_estimate"):
            issues.append("缺少时长估算")
        
        # 检查阶段内容
        phases = execution_plan.get("phases", [])
        for i, phase in enumerate(phases, 1):
            if not phase.get("phase_name"):
                issues.append(f"阶段{i}缺少名称")
            if not phase.get("description"):
                issues.append(f"阶段{i}缺少描述")
            if not phase.get("tasks"):
                issues.append(f"阶段{i}缺少任务列表")
        
        # 检查交付物
        deliverables = execution_plan.get("deliverables", [])
        if not deliverables:
            issues.append("缺少交付物定义")
        
        # 检查资源需求
        resource_req = execution_plan.get("resource_requirements", {})
        if not resource_req.get("team_roles"):
            issues.append("缺少团队角色定义")
        
        # 更新验证结果
        validation_result["content_issues"] = issues
        validation_result["is_complete"] = len(issues) == 0
        
        # 计算完整性分数
        total_checks = 8  # 总检查项数
        passed_checks = total_checks - len(issues)
        validation_result["completeness_score"] = passed_checks / total_checks
        
        return validation_result
    
    def _assess_quality(self, document: str, execution_plan: Dict[str, Any],
                       planning_summary: Dict[str, Any]) -> Dict[str, Any]:
        """评估规划质量"""
        
        # 评估完整性
        completeness_score = self._assess_completeness(execution_plan, planning_summary)
        
        # 评估清晰度
        clarity_score = self._assess_clarity(document, execution_plan)
        
        # 评估可行性
        feasibility_score = self._assess_feasibility(execution_plan)
        
        # 计算总体分数
        overall_score = (completeness_score * 0.4 + clarity_score * 0.3 + feasibility_score * 0.3)
        
        return {
            "overall_score": round(overall_score, 3),
            "completeness_score": round(completeness_score, 3),
            "clarity_score": round(clarity_score, 3),
            "feasibility_score": round(feasibility_score, 3),
            "grade": self._get_quality_grade(overall_score),
            "recommendations": self._generate_recommendations(
                completeness_score, clarity_score, feasibility_score
            )
        }
    
    def _assess_completeness(self, execution_plan: Dict[str, Any],
                           planning_summary: Dict[str, Any]) -> float:
        """评估完整性"""
        score = 0.0
        
        # 检查项目摘要完整性 (25%)
        project_summary = execution_plan.get("project_summary", {})
        summary_fields = ["title", "duration_estimate", "team_size_estimate", "complexity_level"]
        summary_completeness = sum(1 for field in summary_fields if project_summary.get(field)) / len(summary_fields)
        score += summary_completeness * 0.25
        
        # 检查阶段完整性 (35%)
        phases = execution_plan.get("phases", [])
        if phases:
            phase_completeness = 0
            for phase in phases:
                phase_fields = ["phase_name", "duration", "description", "tasks", "deliverables"]
                phase_score = sum(1 for field in phase_fields if phase.get(field)) / len(phase_fields)
                phase_completeness += phase_score
            phase_completeness /= len(phases)
            score += phase_completeness * 0.35
        
        # 检查交付物完整性 (20%)
        deliverables = execution_plan.get("deliverables", [])
        if deliverables:
            deliverable_completeness = 0
            for deliverable in deliverables:
                deliverable_fields = ["name", "description", "phase", "priority"]
                deliverable_score = sum(1 for field in deliverable_fields if deliverable.get(field)) / len(deliverable_fields)
                deliverable_completeness += deliverable_score
            deliverable_completeness /= len(deliverables)
            score += deliverable_completeness * 0.20
        
        # 检查风险和资源 (20%)
        risks = execution_plan.get("risks", [])
        resource_req = execution_plan.get("resource_requirements", {})
        
        risk_score = 0.5 if risks else 0
        resource_score = 0.5 if resource_req.get("team_roles") else 0
        score += (risk_score + resource_score) * 0.20
        
        return min(1.0, score)
    
    def _assess_clarity(self, document: str, execution_plan: Dict[str, Any]) -> float:
        """评估清晰度"""
        score = 0.5  # 基础分数
        
        # 文档长度评估
        doc_length = len(document)
        if doc_length > 1000:
            score += 0.2
        elif doc_length > 500:
            score += 0.1
        
        # 结构清晰度评估
        section_count = document.count("##")
        if section_count >= 5:
            score += 0.1
        
        # 阶段描述清晰度
        phases = execution_plan.get("phases", [])
        if phases:
            clear_descriptions = sum(1 for phase in phases 
                                   if len(phase.get("description", "")) > 20)
            description_ratio = clear_descriptions / len(phases)
            score += description_ratio * 0.2
        
        return min(1.0, score)
    
    def _assess_feasibility(self, execution_plan: Dict[str, Any]) -> float:
        """评估可行性"""
        score = 0.6  # 基础分数
        
        # 时间估算合理性
        phases = execution_plan.get("phases", [])
        if phases:
            # 检查是否有时间估算
            phases_with_duration = sum(1 for phase in phases if phase.get("duration"))
            if phases_with_duration == len(phases):
                score += 0.2
            elif phases_with_duration > 0:
                score += 0.1
        
        # 任务分解合理性
        total_tasks = sum(len(phase.get("tasks", [])) for phase in phases)
        phases_count = len(phases)
        if phases_count > 0:
            avg_tasks_per_phase = total_tasks / phases_count
            if 2 <= avg_tasks_per_phase <= 8:  # 合理的任务数量
                score += 0.1
        
        # 资源配置合理性
        resource_req = execution_plan.get("resource_requirements", {})
        team_roles = resource_req.get("team_roles", [])
        if 1 <= len(team_roles) <= 6:  # 合理的团队规模
            score += 0.1
        
        return min(1.0, score)
    
    def _get_quality_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.8:
            return "良好"
        elif score >= 0.7:
            return "中等"
        elif score >= 0.6:
            return "及格"
        else:
            return "需改进"
    
    def _generate_recommendations(self, completeness_score: float,
                                clarity_score: float, feasibility_score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if completeness_score < 0.7:
            recommendations.append("建议补充缺失的项目信息，如时间估算、团队配置等")
        
        if clarity_score < 0.6:
            recommendations.append("建议增加更详细的描述，提高文档的可读性")
        
        if feasibility_score < 0.7:
            recommendations.append("建议重新评估时间安排和资源配置的合理性")
        
        if not recommendations:
            recommendations.append("规划质量良好，可以开始项目实施")
        
        return recommendations
    
    def _generate_validation_report(self, structure_validation: Dict[str, Any],
                                  content_validation: Dict[str, Any],
                                  quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """生成验证报告"""
        
        return {
            "validation_timestamp": time.time(),
            "structure_validation": structure_validation,
            "content_validation": content_validation,
            "quality_assessment": quality_assessment,
            "summary": {
                "total_issues": (
                    len(structure_validation.get("missing_sections", [])) +
                    len(structure_validation.get("structure_issues", [])) +
                    len(content_validation.get("content_issues", []))
                ),
                "overall_score": quality_assessment["overall_score"],
                "grade": quality_assessment["grade"],
                "validation_passed": (
                    structure_validation["is_valid"] and
                    content_validation["is_complete"] and
                    quality_assessment["overall_score"] >= 0.6
                )
            }
        }
