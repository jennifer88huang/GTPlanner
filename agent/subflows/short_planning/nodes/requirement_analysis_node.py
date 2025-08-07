"""
Requirement Analysis Node

解析结构化需求，识别核心目标和关键信息，为规划生成做准备。
"""

import time
from typing import Dict, Any, List
from pocketflow import AsyncNode
from agent.shared_migration import field_validation_decorator


class RequirementAnalysisNode(AsyncNode):
    """需求分析节点 - 解析结构化需求，识别核心目标"""
    
    def __init__(self):
        super().__init__()
        self.name = "RequirementAnalysisNode"
        self.description = "解析结构化需求，识别核心目标和关键信息"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：从pocketflow字典共享变量获取结构化需求"""
        try:
            # 获取结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            if not structured_requirements:
                return {"error": "No structured requirements found"}
            
            # 获取对话历史作为上下文
            dialogue_history = shared.get("dialogue_history", {})
            
            return {
                "structured_requirements": structured_requirements,
                "dialogue_history": dialogue_history,
                "analysis_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Requirement analysis preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行需求分析"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            structured_requirements = prep_result["structured_requirements"]
            dialogue_history = prep_result["dialogue_history"]
            
            # 分析项目概览
            project_analysis = self._analyze_project_overview(structured_requirements)
            
            # 分析功能需求
            functional_analysis = self._analyze_functional_requirements(structured_requirements)
            
            # 分析非功能需求
            non_functional_analysis = self._analyze_non_functional_requirements(structured_requirements)
            
            # 分析约束条件
            constraints_analysis = self._analyze_constraints(structured_requirements)
            
            # 提取关键信息
            key_insights = self._extract_key_insights(
                project_analysis, functional_analysis, 
                non_functional_analysis, constraints_analysis
            )
            
            # 识别核心目标
            core_objectives = self._identify_core_objectives(structured_requirements)
            
            # 评估复杂度
            complexity_assessment = self._assess_complexity(structured_requirements)
            
            return {
                "project_analysis": project_analysis,
                "functional_analysis": functional_analysis,
                "non_functional_analysis": non_functional_analysis,
                "constraints_analysis": constraints_analysis,
                "key_insights": key_insights,
                "core_objectives": core_objectives,
                "complexity_assessment": complexity_assessment,
                "analysis_success": True
            }
            
        except Exception as e:
            raise e
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存需求分析结果"""
        if "error" in exec_res:
            shared["requirement_analysis_error"] = exec_res["error"]
            return "error"
        
        # 保存分析结果
        shared["requirement_analysis"] = {
            "project_analysis": exec_res["project_analysis"],
            "functional_analysis": exec_res["functional_analysis"],
            "non_functional_analysis": exec_res["non_functional_analysis"],
            "constraints_analysis": exec_res["constraints_analysis"],
            "key_insights": exec_res["key_insights"],
            "core_objectives": exec_res["core_objectives"],
            "complexity_assessment": exec_res["complexity_assessment"]
        }
        
        print(f"✅ 需求分析完成，识别了 {len(exec_res['core_objectives'])} 个核心目标")
        return "success"
    
    def _analyze_project_overview(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析项目概览"""
        project_overview = requirements.get("project_overview", {})
        
        return {
            "title": project_overview.get("title", ""),
            "description": project_overview.get("description", ""),
            "objectives": project_overview.get("objectives", []),
            "target_users": project_overview.get("target_users", []),
            "success_criteria": project_overview.get("success_criteria", []),
            "scope": project_overview.get("scope", ""),
            "has_clear_title": bool(project_overview.get("title")),
            "has_description": bool(project_overview.get("description")),
            "objectives_count": len(project_overview.get("objectives", [])),
            "target_users_count": len(project_overview.get("target_users", []))
        }
    
    def _analyze_functional_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析功能需求"""
        functional_req = requirements.get("functional_requirements", {})
        core_features = functional_req.get("core_features", [])
        user_stories = functional_req.get("user_stories", [])
        
        # 分析功能优先级分布
        priority_distribution = {"high": 0, "medium": 0, "low": 0}
        for feature in core_features:
            if isinstance(feature, dict):
                priority = feature.get("priority", "medium")
                if priority in priority_distribution:
                    priority_distribution[priority] += 1
        
        return {
            "core_features": core_features,
            "user_stories": user_stories,
            "features_count": len(core_features),
            "user_stories_count": len(user_stories),
            "priority_distribution": priority_distribution,
            "high_priority_features": [f for f in core_features 
                                     if isinstance(f, dict) and f.get("priority") == "high"]
        }
    
    def _analyze_non_functional_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析非功能需求"""
        non_functional = requirements.get("non_functional_requirements", {})
        
        return {
            "performance": non_functional.get("performance", {}),
            "security": non_functional.get("security", {}),
            "scalability": non_functional.get("scalability", {}),
            "has_performance_req": bool(non_functional.get("performance")),
            "has_security_req": bool(non_functional.get("security")),
            "has_scalability_req": bool(non_functional.get("scalability"))
        }
    
    def _analyze_constraints(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """分析约束条件"""
        constraints = requirements.get("constraints", {})
        
        return {
            "timeline": constraints.get("timeline", ""),
            "budget": constraints.get("budget", ""),
            "resources": constraints.get("resources", ""),
            "compliance": constraints.get("compliance", []),
            "has_timeline": bool(constraints.get("timeline")),
            "has_budget": bool(constraints.get("budget")),
            "has_resources": bool(constraints.get("resources")),
            "compliance_count": len(constraints.get("compliance", []))
        }
    
    def _extract_key_insights(self, project_analysis: Dict[str, Any], 
                            functional_analysis: Dict[str, Any],
                            non_functional_analysis: Dict[str, Any],
                            constraints_analysis: Dict[str, Any]) -> List[str]:
        """提取关键洞察"""
        insights = []
        
        # 项目规模洞察
        features_count = functional_analysis["features_count"]
        if features_count > 10:
            insights.append("项目功能较多，建议分阶段实施")
        elif features_count < 3:
            insights.append("项目功能相对简单，可快速实现")
        
        # 优先级洞察
        high_priority_count = functional_analysis["priority_distribution"]["high"]
        if high_priority_count > 5:
            insights.append("高优先级功能较多，需要重点关注资源分配")
        
        # 非功能需求洞察
        if non_functional_analysis["has_performance_req"]:
            insights.append("项目有性能要求，需要在架构设计中重点考虑")
        
        if non_functional_analysis["has_security_req"]:
            insights.append("项目有安全要求，需要实施安全最佳实践")
        
        # 约束洞察
        if constraints_analysis["has_timeline"]:
            insights.append("项目有时间约束，需要合理安排开发计划")
        
        if constraints_analysis["has_budget"]:
            insights.append("项目有预算约束，需要优化资源使用")
        
        return insights
    
    def _identify_core_objectives(self, requirements: Dict[str, Any]) -> List[str]:
        """识别核心目标"""
        objectives = []
        
        # 从项目概览中提取目标
        project_overview = requirements.get("project_overview", {})
        project_objectives = project_overview.get("objectives", [])
        objectives.extend(project_objectives)
        
        # 从高优先级功能中提取目标
        functional_req = requirements.get("functional_requirements", {})
        core_features = functional_req.get("core_features", [])
        for feature in core_features:
            if isinstance(feature, dict) and feature.get("priority") == "high":
                feature_name = feature.get("name", "")
                if feature_name:
                    objectives.append(f"实现{feature_name}功能")
        
        # 去重并限制数量
        unique_objectives = list(dict.fromkeys(objectives))  # 去重
        return unique_objectives[:8]  # 最多8个核心目标
    
    def _assess_complexity(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """评估项目复杂度"""
        complexity_score = 0
        factors = []
        
        # 功能数量因子
        functional_req = requirements.get("functional_requirements", {})
        features_count = len(functional_req.get("core_features", []))
        if features_count > 10:
            complexity_score += 3
            factors.append("功能数量较多")
        elif features_count > 5:
            complexity_score += 2
            factors.append("功能数量中等")
        else:
            complexity_score += 1
            factors.append("功能数量较少")
        
        # 非功能需求因子
        non_functional = requirements.get("non_functional_requirements", {})
        nfr_count = sum([
            bool(non_functional.get("performance")),
            bool(non_functional.get("security")),
            bool(non_functional.get("scalability"))
        ])
        complexity_score += nfr_count
        if nfr_count > 0:
            factors.append(f"有{nfr_count}类非功能需求")
        
        # 技术需求因子
        tech_req = requirements.get("technical_requirements", {})
        if tech_req:
            languages = tech_req.get("programming_languages", [])
            frameworks = tech_req.get("frameworks", [])
            if len(languages) > 2 or len(frameworks) > 3:
                complexity_score += 2
                factors.append("技术栈较复杂")
            elif languages or frameworks:
                complexity_score += 1
                factors.append("技术栈明确")
        
        # 确定复杂度等级
        if complexity_score >= 8:
            level = "high"
            description = "高复杂度项目"
        elif complexity_score >= 5:
            level = "medium"
            description = "中等复杂度项目"
        else:
            level = "low"
            description = "低复杂度项目"
        
        return {
            "level": level,
            "score": complexity_score,
            "description": description,
            "factors": factors
        }
