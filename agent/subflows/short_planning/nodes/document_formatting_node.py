"""
Document Formatting Node

将执行规划格式化为用户友好的确认文档。
"""

import time
from typing import Dict, Any, List
from pocketflow import Node


class DocumentFormattingNode(Node):
    """文档格式化节点 - 生成用户友好的确认文档"""
    
    def __init__(self):
        super().__init__()
        self.name = "DocumentFormattingNode"
        self.description = "将执行规划格式化为用户友好的确认文档"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取执行规划和需求分析结果"""
        try:
            # 获取执行规划
            execution_plan = shared.get("execution_plan", {})
            if not execution_plan:
                return {"error": "No execution plan found"}
            
            # 获取需求分析结果
            requirement_analysis = shared.get("requirement_analysis", {})
            
            # 获取原始结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            
            return {
                "execution_plan": execution_plan,
                "requirement_analysis": requirement_analysis,
                "structured_requirements": structured_requirements,
                "formatting_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Document formatting preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行文档格式化"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            execution_plan = prep_result["execution_plan"]
            requirement_analysis = prep_result["requirement_analysis"]
            structured_requirements = prep_result["structured_requirements"]
            
            # 生成确认文档
            confirmation_document = self._generate_confirmation_document(
                execution_plan, requirement_analysis, structured_requirements
            )
            
            # 生成摘要信息
            summary_info = self._generate_summary_info(execution_plan)
            
            return {
                "confirmation_document": confirmation_document,
                "summary_info": summary_info,
                "formatting_success": True
            }
            
        except Exception as e:
            raise e
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存文档格式化结果"""
        if "error" in exec_res:
            shared["document_formatting_error"] = exec_res["error"]
            return "error"
        
        # 保存确认文档（按照文档规范格式）
        shared["confirmation_document"] = exec_res["confirmation_document"]
        shared["planning_summary"] = exec_res["summary_info"]
        
        # 统计信息
        confirmation_doc = exec_res["confirmation_document"]
        if isinstance(confirmation_doc, dict):
            key_deliverables = confirmation_doc.get("document_structure", {}).get("key_deliverables", [])
            phases_count = exec_res["summary_info"]["phases_count"]
            print(f"✅ 确认文档生成完成，包含 {len(key_deliverables)} 个关键交付物，{phases_count} 个阶段")
        else:
            print(f"✅ 确认文档生成完成，文档长度: {len(str(confirmation_doc))} 字符")
        return "success"
    
    def _generate_confirmation_document(self, execution_plan: Dict[str, Any],
                                      requirement_analysis: Dict[str, Any],
                                      structured_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """生成确认文档 - 按照文档规范格式"""
        
        # 获取项目基本信息
        project_overview = structured_requirements.get("project_overview", {})
        
        # 按照文档规范生成confirmation_document结构
        confirmation_document = {
            "document_structure": {
                "executive_summary": self._generate_executive_summary(
                    project_overview, requirement_analysis
                ),
                "project_scope": self._generate_project_scope(
                    structured_requirements, requirement_analysis
                ),
                "key_deliverables": self._extract_key_deliverables(execution_plan),
                "timeline_summary": self._generate_timeline_summary(execution_plan),
                "resource_overview": self._generate_resource_overview(execution_plan),
                "risk_assessment": self._generate_risk_assessment(execution_plan),
                "next_steps": self._generate_next_steps(execution_plan)
            },
            "presentation_format": {
                "format_type": "markdown",
                "visual_elements": ["phase_diagram", "deliverable_timeline"],
                "interactive_elements": ["confirmation_checkboxes"],
                "accessibility_features": ["clear_headings", "structured_content"]
            },
            "user_interaction": {
                "confirmation_points": self._generate_confirmation_points(execution_plan),
                "feedback_mechanisms": ["inline_comments", "section_approval"],
                "modification_options": ["scope_adjustment", "priority_reordering"]
            },
            "document_metadata": {
                "version": "1.0",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "review_status": "pending_review",
                "approval_required": True
            }
        }
        
        return confirmation_document
    
    def _generate_executive_summary(self, project_overview: Dict[str, Any],
                                  requirement_analysis: Dict[str, Any]) -> str:
        """生成执行摘要"""
        
        project_title = project_overview.get("title", "项目")
        project_description = project_overview.get("description", "")
        core_objectives = requirement_analysis.get("core_objectives", [])
        complexity_assessment = requirement_analysis.get("complexity_assessment", {})
        
        summary = f"""项目 "{project_title}" 旨在{project_description}。
        
核心目标包括：{', '.join(core_objectives[:3])}等。

项目复杂度评估为{complexity_assessment.get('level', '中等')}，需要系统性的规划和实施。"""
        
        return summary.strip()
    
    def _generate_project_scope(self, structured_requirements: Dict[str, Any],
                               requirement_analysis: Dict[str, Any]) -> str:
        """生成项目范围"""
        
        functional_req = structured_requirements.get("functional_requirements", {})
        core_features = functional_req.get("core_features", [])
        
        scope_items = []
        for feature in core_features:
            if isinstance(feature, dict):
                name = feature.get("name", "")
                if name:
                    scope_items.append(name)
        
        scope = f"""项目范围包含以下核心功能：
        
{chr(10).join([f"- {item}" for item in scope_items])}

项目将专注于核心功能的实现，确保质量和可维护性。"""
        
        return scope.strip()
    
    def _extract_key_deliverables(self, execution_plan: Dict[str, Any]) -> List[str]:
        """提取关键交付物"""
        
        deliverables = []
        execution_phases = execution_plan.get("execution_phases", [])
        
        for phase in execution_phases:
            phase_deliverables = phase.get("deliverables", [])
            deliverables.extend(phase_deliverables)
        
        # 去重并限制数量
        unique_deliverables = list(dict.fromkeys(deliverables))
        return unique_deliverables[:10]  # 最多10个关键交付物
    
    def _generate_timeline_summary(self, execution_plan: Dict[str, Any]) -> str:
        """生成时间线摘要"""
        
        execution_phases = execution_plan.get("execution_phases", [])
        timeline_overview = execution_plan.get("timeline_overview", {})
        critical_path = timeline_overview.get("critical_path", [])
        
        if critical_path:
            summary = f"项目将分{len(execution_phases)}个阶段实施，关键路径包括：{', '.join(critical_path)}。"
        else:
            summary = f"项目将分{len(execution_phases)}个阶段实施，各阶段按序推进。"
        
        return summary
    
    def _generate_resource_overview(self, execution_plan: Dict[str, Any]) -> str:
        """生成资源概览"""
        
        resource_req = execution_plan.get("resource_requirements", {})
        human_resources = resource_req.get("human_resources", [])
        technical_resources = resource_req.get("technical_resources", [])
        
        overview = f"""项目需要以下资源：
        
人力资源：{', '.join(human_resources) if human_resources else '待确定'}
技术资源：{', '.join(technical_resources) if technical_resources else '待确定'}"""
        
        return overview.strip()
    
    def _generate_risk_assessment(self, execution_plan: Dict[str, Any]) -> str:
        """生成风险评估"""
        
        execution_phases = execution_plan.get("execution_phases", [])
        all_risks = []
        
        for phase in execution_phases:
            phase_risks = phase.get("risks", [])
            all_risks.extend(phase_risks)
        
        if all_risks:
            unique_risks = list(dict.fromkeys(all_risks))[:5]  # 最多5个主要风险
            assessment = f"主要风险包括：{', '.join(unique_risks)}。需要制定相应的应对策略。"
        else:
            assessment = "暂未识别到重大风险，但需要在实施过程中持续监控。"
        
        return assessment
    
    def _generate_next_steps(self, execution_plan: Dict[str, Any]) -> List[str]:
        """生成下一步行动"""
        
        execution_phases = execution_plan.get("execution_phases", [])
        
        next_steps = ["确认项目规划和资源配置"]
        
        if execution_phases:
            first_phase = execution_phases[0]
            phase_name = first_phase.get("phase_name", "第一阶段")
            next_steps.append(f"启动{phase_name}")
            
            first_deliverables = first_phase.get("deliverables", [])
            if first_deliverables:
                next_steps.append(f"准备{first_deliverables[0]}的相关工作")
        
        next_steps.append("建立项目沟通机制")
        
        return next_steps
    
    def _generate_confirmation_points(self, execution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成确认点"""
        
        confirmation_points = [
            {
                "point_id": "scope_confirmation",
                "question": "项目范围和目标是否符合您的预期？",
                "options": ["完全符合", "基本符合", "需要调整"],
                "importance": "critical"
            },
            {
                "point_id": "resource_confirmation", 
                "question": "资源配置是否合理？",
                "options": ["合理", "需要增加资源", "需要优化配置"],
                "importance": "important"
            },
            {
                "point_id": "timeline_confirmation",
                "question": "项目阶段划分是否合适？",
                "options": ["合适", "需要调整", "需要详细讨论"],
                "importance": "important"
            }
        ]
        
        return confirmation_points
    
    def _generate_summary_info(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """生成摘要信息"""
        
        execution_phases = execution_plan.get("execution_phases", [])
        
        # 统计交付物数量
        total_deliverables = 0
        for phase in execution_phases:
            deliverables = phase.get("deliverables", [])
            total_deliverables += len(deliverables)
        
        # 统计风险数量
        total_risks = 0
        for phase in execution_phases:
            risks = phase.get("risks", [])
            total_risks += len(risks)
        
        return {
            "phases_count": len(execution_phases),
            "deliverables_count": total_deliverables,
            "risks_count": total_risks,
            "planning_approach": execution_plan.get("planning_approach", "hybrid")
        }
