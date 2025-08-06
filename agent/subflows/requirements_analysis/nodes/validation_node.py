"""
Validation Node

对结构化的需求进行格式校验和质量评估，确保输出符合标准。
提供完整的验证机制，包括格式检查、完整性验证、一致性分析和质量评分。
"""

import time
from typing import Dict, Any, List, Set, Tuple
from pocketflow import Node


class ValidationNode(Node):
    """需求验证节点 - 完整的专业验证系统"""
    
    def __init__(self):
        super().__init__()
        self.name = "ValidationNode"
        self.description = "对结构化需求进行格式校验和质量评估"
        
        # 验证配置
        self.validation_config = {
            "required_fields": {
                "project_overview": ["title", "description", "objectives"],
                "functional_requirements": ["core_features"],
                "non_functional_requirements": ["performance", "security"],
                "technical_requirements": ["programming_languages", "frameworks"],
                "constraints": []
            },
            "quality_weights": {
                "completeness": 0.3,
                "clarity": 0.25,
                "consistency": 0.25,
                "feasibility": 0.2
            },
            "priority_values": ["high", "medium", "low"],
            "complexity_levels": ["simple", "medium", "complex"],
            "min_features_count": 1,
            "max_features_count": 50
        }
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备验证处理"""
        structured_requirements = shared.get("structured_requirements", {})
        
        if not structured_requirements:
            return {
                "error": "No structured requirements found for validation",
                "structured_requirements": {}
            }
        
        return {
            "structured_requirements": structured_requirements,
            "validation_timestamp": time.time()
        }
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行需求验证"""
        try:
            if "error" in prep_result:
                return {
                    "error": prep_result["error"],
                    "validation_success": False
                }
            
            structured_requirements = prep_result["structured_requirements"]
            validation_timestamp = prep_result["validation_timestamp"]
            
            # 执行格式验证
            format_validation = self._validate_format(structured_requirements)
            
            # 执行完整性验证
            completeness_validation = self._validate_completeness(structured_requirements)
            
            # 执行一致性验证
            consistency_validation = self._validate_consistency(structured_requirements)
            
            # 执行质量评估
            quality_assessment = self._assess_quality(structured_requirements)
            
            # 生成综合验证报告
            validation_report = self._generate_validation_report(
                format_validation,
                completeness_validation,
                consistency_validation,
                quality_assessment,
                validation_timestamp
            )
            
            # 判断整体验证是否成功
            validation_success = (
                format_validation["is_valid"] and
                completeness_validation["is_complete"] and
                quality_assessment["overall_score"] >= 0.5
            )
            
            return {
                "validation_report": validation_report,
                "validation_success": validation_success,
                "validated_requirements": structured_requirements,
                "validation_metadata": {
                    "validation_time": time.time() - validation_timestamp,
                    "validator_version": "1.0",
                    "validation_rules_count": len(self.validation_config["required_fields"])
                }
            }
            
        except Exception as e:
            return {
                "error": f"Validation process failed: {str(e)}",
                "validation_success": False
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存验证结果"""
        if "error" in exec_res:
            shared["validation_error"] = exec_res["error"]
            print(f"❌ 需求验证失败: {exec_res['error']}")
            return "error"
        
        # 保存验证报告
        validation_report = exec_res.get("validation_report", {})
        shared["validation_report"] = validation_report
        
        # 更新结构化需求（如果有修正）
        validated_requirements = exec_res.get("validated_requirements", {})
        if validated_requirements:
            shared["structured_requirements"] = validated_requirements
        
        # 保存验证元数据
        validation_metadata = exec_res.get("validation_metadata", {})
        shared["validation_metadata"] = validation_metadata
        
        validation_success = exec_res.get("validation_success", False)
        overall_score = validation_report.get("quality_assessment", {}).get("overall_score", 0)
        
        print(f"✅ 需求验证完成，质量评分: {overall_score:.2f}, 验证{'通过' if validation_success else '未通过'}")
        
        return "success" if validation_success else "warning"
    
    def _validate_format(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证需求格式"""
        validation_result = {
            "is_valid": True,
            "missing_fields": [],
            "invalid_fields": [],
            "warnings": [],
            "field_count": 0
        }
        
        # 检查必需的顶级字段
        for section, required_fields in self.validation_config["required_fields"].items():
            if section not in requirements:
                validation_result["missing_fields"].append(section)
                validation_result["is_valid"] = False
                continue
            
            section_data = requirements[section]
            if not isinstance(section_data, dict):
                validation_result["invalid_fields"].append(f"{section} (not a dict)")
                validation_result["is_valid"] = False
                continue
            
            # 检查section内的必需字段
            for field in required_fields:
                if field not in section_data or not section_data[field]:
                    validation_result["missing_fields"].append(f"{section}.{field}")
                    validation_result["is_valid"] = False
        
        # 验证功能需求的特殊格式
        if "functional_requirements" in requirements:
            func_req = requirements["functional_requirements"]
            if "core_features" in func_req:
                features = func_req["core_features"]
                if isinstance(features, list):
                    for i, feature in enumerate(features):
                        if isinstance(feature, dict):
                            self._validate_feature_format(feature, i, validation_result)
                        else:
                            validation_result["invalid_fields"].append(f"functional_requirements.core_features[{i}]")
        
        validation_result["field_count"] = self._count_fields(requirements)
        return validation_result
    
    def _validate_feature_format(self, feature: Dict[str, Any], index: int, validation_result: Dict[str, Any]):
        """验证单个功能的格式"""
        required_feature_fields = ["name", "description", "priority"]
        
        for field in required_feature_fields:
            if field not in feature or not feature[field]:
                validation_result["missing_fields"].append(f"functional_requirements.core_features[{index}].{field}")
                validation_result["is_valid"] = False
        
        # 验证优先级值
        if "priority" in feature:
            priority = feature["priority"]
            if priority not in self.validation_config["priority_values"]:
                validation_result["invalid_fields"].append(f"functional_requirements.core_features[{index}].priority")
                validation_result["warnings"].append(f"无效的优先级值: {priority}")
    
    def _validate_completeness(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证需求完整性"""
        completeness_result = {
            "is_complete": True,
            "completion_score": 0.0,
            "missing_sections": [],
            "incomplete_sections": [],
            "section_scores": {}
        }
        
        # 评估各个section的完整性
        section_scores = {}
        
        # 项目概览完整性
        section_scores["project_overview"] = self._assess_section_completeness(
            requirements.get("project_overview", {}),
            ["title", "description", "objectives", "target_users", "success_criteria"]
        )
        
        # 功能需求完整性
        func_req = requirements.get("functional_requirements", {})
        features_count = len(func_req.get("core_features", []))
        if features_count < self.validation_config["min_features_count"]:
            section_scores["functional_requirements"] = 0.3
            completeness_result["incomplete_sections"].append("functional_requirements (insufficient features)")
        elif features_count > self.validation_config["max_features_count"]:
            section_scores["functional_requirements"] = 0.7
            completeness_result["incomplete_sections"].append("functional_requirements (too many features)")
        else:
            section_scores["functional_requirements"] = min(1.0, features_count / 5.0)
        
        # 非功能需求完整性
        section_scores["non_functional_requirements"] = self._assess_section_completeness(
            requirements.get("non_functional_requirements", {}),
            ["performance", "security", "scalability"]
        )
        
        # 技术需求完整性
        tech_req = requirements.get("technical_requirements", {})
        tech_fields = ["programming_languages", "frameworks", "databases"]
        section_scores["technical_requirements"] = self._assess_section_completeness(tech_req, tech_fields)
        
        # 计算总体完整性分数
        completeness_result["section_scores"] = section_scores
        completeness_result["completion_score"] = sum(section_scores.values()) / len(section_scores)
        completeness_result["is_complete"] = completeness_result["completion_score"] >= 0.7
        
        return completeness_result
    
    def _assess_section_completeness(self, section: Dict[str, Any], expected_fields: List[str]) -> float:
        """评估单个section的完整性"""
        if not section:
            return 0.0
        
        filled_fields = sum(1 for field in expected_fields if field in section and section[field])
        return filled_fields / len(expected_fields) if expected_fields else 1.0
    
    def _validate_consistency(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """验证需求一致性"""
        consistency_result = {
            "is_consistent": True,
            "consistency_score": 0.0,
            "inconsistencies": [],
            "warnings": []
        }
        
        inconsistencies = []
        
        # 检查技术栈一致性
        tech_inconsistencies = self._check_tech_stack_consistency(requirements)
        inconsistencies.extend(tech_inconsistencies)
        
        # 检查功能与非功能需求的一致性
        func_nonfunc_inconsistencies = self._check_functional_nonfunctional_consistency(requirements)
        inconsistencies.extend(func_nonfunc_inconsistencies)
        
        # 检查约束条件的一致性
        constraint_inconsistencies = self._check_constraint_consistency(requirements)
        inconsistencies.extend(constraint_inconsistencies)
        
        consistency_result["inconsistencies"] = inconsistencies
        consistency_result["is_consistent"] = len(inconsistencies) == 0
        consistency_result["consistency_score"] = max(0.0, 1.0 - len(inconsistencies) * 0.2)
        
        return consistency_result
    
    def _check_tech_stack_consistency(self, requirements: Dict[str, Any]) -> List[str]:
        """检查技术栈一致性"""
        inconsistencies = []
        tech_req = requirements.get("technical_requirements", {})
        
        languages = tech_req.get("programming_languages", [])
        frameworks = tech_req.get("frameworks", [])
        
        # 检查语言和框架的匹配
        if "Python" in languages and not any(fw in ["Django", "Flask", "FastAPI"] for fw in frameworks):
            inconsistencies.append("Python语言但未选择相应的Python框架")
        
        if "JavaScript" in languages and not any(fw in ["React", "Vue", "Angular", "Node.js"] for fw in frameworks):
            inconsistencies.append("JavaScript语言但未选择相应的JavaScript框架")
        
        return inconsistencies
    
    def _check_functional_nonfunctional_consistency(self, requirements: Dict[str, Any]) -> List[str]:
        """检查功能与非功能需求的一致性"""
        inconsistencies = []
        
        func_req = requirements.get("functional_requirements", {})
        non_func_req = requirements.get("non_functional_requirements", {})
        
        features_count = len(func_req.get("core_features", []))
        performance = non_func_req.get("performance", {})
        
        # 检查功能复杂度与性能要求的匹配
        if features_count > 10 and not performance.get("concurrent_users"):
            inconsistencies.append("功能较多但未定义并发用户数要求")
        
        return inconsistencies
    
    def _check_constraint_consistency(self, requirements: Dict[str, Any]) -> List[str]:
        """检查约束条件一致性"""
        inconsistencies = []
        constraints = requirements.get("constraints", {})
        
        timeline = constraints.get("timeline", "")
        budget = constraints.get("budget", "")
        
        # 简单的一致性检查
        if "紧急" in timeline and "低" in budget:
            inconsistencies.append("时间紧急但预算较低，可能存在冲突")
        
        return inconsistencies
    
    def _assess_quality(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """评估需求质量"""
        quality_metrics = {}
        
        # 完整性评分
        quality_metrics["completeness"] = self._assess_completeness_quality(requirements)
        
        # 清晰度评分
        quality_metrics["clarity"] = self._assess_clarity_quality(requirements)
        
        # 一致性评分
        quality_metrics["consistency"] = self._assess_consistency_quality(requirements)
        
        # 可行性评分
        quality_metrics["feasibility"] = self._assess_feasibility_quality(requirements)
        
        # 计算加权总分
        weights = self.validation_config["quality_weights"]
        overall_score = sum(
            quality_metrics[metric] * weights[metric]
            for metric in quality_metrics
            if metric in weights
        )
        
        return {
            "overall_score": round(overall_score, 3),
            "metrics": quality_metrics,
            "grade": self._get_quality_grade(overall_score),
            "recommendations": self._generate_quality_recommendations(quality_metrics)
        }
    
    def _assess_completeness_quality(self, requirements: Dict[str, Any]) -> float:
        """评估完整性质量"""
        completeness_validation = self._validate_completeness(requirements)
        return completeness_validation["completion_score"]
    
    def _assess_clarity_quality(self, requirements: Dict[str, Any]) -> float:
        """评估清晰度质量"""
        score = 0.5  # 基础分数
        
        project_overview = requirements.get("project_overview", {})
        description = project_overview.get("description", "")
        
        # 基于描述长度和内容质量评分
        if len(description) > 50:
            score += 0.2
        if len(description) > 100:
            score += 0.1
        
        # 检查关键词
        quality_keywords = ["基于", "实现", "支持", "提供", "管理", "系统", "平台"]
        keyword_count = sum(1 for keyword in quality_keywords if keyword in description)
        score += min(0.2, keyword_count * 0.05)
        
        return min(1.0, score)
    
    def _assess_consistency_quality(self, requirements: Dict[str, Any]) -> float:
        """评估一致性质量"""
        consistency_validation = self._validate_consistency(requirements)
        return consistency_validation["consistency_score"]
    
    def _assess_feasibility_quality(self, requirements: Dict[str, Any]) -> float:
        """评估可行性质量"""
        score = 0.6  # 基础分数
        
        constraints = requirements.get("constraints", {})
        tech_req = requirements.get("technical_requirements", {})
        
        # 检查技术栈的成熟度
        languages = tech_req.get("programming_languages", [])
        mature_languages = ["Python", "JavaScript", "Java", "C#"]
        if any(lang in mature_languages for lang in languages):
            score += 0.2
        
        # 检查约束条件的合理性
        if constraints.get("timeline") and constraints.get("budget"):
            score += 0.2
        
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
    
    def _generate_quality_recommendations(self, quality_metrics: Dict[str, float]) -> List[str]:
        """生成质量改进建议"""
        recommendations = []
        
        for metric, score in quality_metrics.items():
            if score < 0.7:
                if metric == "completeness":
                    recommendations.append("增加需求的完整性，补充缺失的字段和详细信息")
                elif metric == "clarity":
                    recommendations.append("提高需求描述的清晰度，使用更具体和详细的语言")
                elif metric == "consistency":
                    recommendations.append("检查需求的一致性，确保技术栈、功能和约束之间的匹配")
                elif metric == "feasibility":
                    recommendations.append("评估需求的可行性，考虑技术实现难度和资源约束")
        
        return recommendations
    
    def _generate_validation_report(self, format_validation: Dict[str, Any],
                                   completeness_validation: Dict[str, Any],
                                   consistency_validation: Dict[str, Any],
                                   quality_assessment: Dict[str, Any],
                                   validation_timestamp: float) -> Dict[str, Any]:
        """生成综合验证报告"""
        return {
            "validation_timestamp": validation_timestamp,
            "format_validation": format_validation,
            "completeness_validation": completeness_validation,
            "consistency_validation": consistency_validation,
            "quality_assessment": quality_assessment,
            "summary": {
                "total_issues": (
                    len(format_validation.get("missing_fields", [])) +
                    len(format_validation.get("invalid_fields", [])) +
                    len(consistency_validation.get("inconsistencies", []))
                ),
                "overall_score": quality_assessment["overall_score"],
                "grade": quality_assessment["grade"],
                "validation_passed": (
                    format_validation["is_valid"] and
                    completeness_validation["is_complete"] and
                    quality_assessment["overall_score"] >= 0.5
                )
            }
        }
    
    def _count_fields(self, obj: Any, depth: int = 0) -> int:
        """递归计算字段数量"""
        if depth > 5:  # 防止无限递归
            return 0
        
        if isinstance(obj, dict):
            return len(obj) + sum(self._count_fields(v, depth + 1) for v in obj.values())
        elif isinstance(obj, list):
            return len(obj) + sum(self._count_fields(item, depth + 1) for item in obj)
        else:
            return 1
