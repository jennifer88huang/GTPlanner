"""
Plan Generation Node

基于需求分析结果，使用LLM生成清晰的执行步骤和预期产出。
"""

import time
from typing import Dict, Any, List

# 导入LLM工具
from agent.llm_utils import call_llm_async

from pocketflow import AsyncNode


class PlanGenerationNode(AsyncNode):
    """规划生成节点 - 使用LLM生成清晰的执行步骤和预期产出"""
    
    def __init__(self):
        super().__init__()
        self.name = "PlanGenerationNode"
        self.description = "基于需求分析结果生成清晰的执行步骤和预期产出"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取需求分析结果"""
        try:
            # 获取需求分析结果
            requirement_analysis = shared.get("requirement_analysis", {})
            if not requirement_analysis:
                return {"error": "No requirement analysis found"}
            
            # 获取原始结构化需求作为参考
            structured_requirements = shared.get("structured_requirements", {})
            
            return {
                "requirement_analysis": requirement_analysis,
                "structured_requirements": structured_requirements,
                "generation_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Plan generation preparation failed: {str(e)}"}
    
    async def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行规划生成"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            requirement_analysis = prep_result["requirement_analysis"]
            structured_requirements = prep_result["structured_requirements"]
            
            # 使用LLM生成规划
            planning_result = asyncio.run(self._generate_plan_with_llm(
                requirement_analysis, structured_requirements
            ))
            
            return {
                "execution_plan": planning_result,
                "generation_success": True
            }
            
        except Exception as e:
            raise e
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存规划生成结果"""
        if "error" in exec_res:
            shared["plan_generation_error"] = exec_res["error"]
            return "error"
        
        # 保存执行规划
        execution_plan = exec_res["execution_plan"]
        shared["execution_plan"] = execution_plan
        
        # 统计信息
        phases_count = len(execution_plan.get("phases", []))
        deliverables_count = len(execution_plan.get("deliverables", []))
        
        print(f"✅ 规划生成完成，包含 {phases_count} 个阶段，{deliverables_count} 个交付物")
        return "success"
    
    async def _generate_plan_with_llm(self, requirement_analysis: Dict[str, Any], 
                                    structured_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM生成执行规划"""
        
        # 构建LLM提示词
        prompt = self._build_planning_prompt(requirement_analysis, structured_requirements)
        
        # 调用LLM
        result = await call_llm_async(prompt, is_json=True)
        
        # 验证和处理结果
        validated_result = self._validate_planning_result(result)
        
        return validated_result
    
    def _build_planning_prompt(self, requirement_analysis: Dict[str, Any], 
                             structured_requirements: Dict[str, Any]) -> str:
        """构建规划生成的LLM提示词"""
        
        # 提取关键信息
        project_title = requirement_analysis["project_analysis"]["title"]
        core_objectives = requirement_analysis["core_objectives"]
        complexity_level = requirement_analysis["complexity_assessment"]["level"]
        key_insights = requirement_analysis["key_insights"]
        
        # 提取功能需求
        functional_analysis = requirement_analysis["functional_analysis"]
        high_priority_features = functional_analysis["high_priority_features"]
        
        # 提取约束条件
        constraints_analysis = requirement_analysis["constraints_analysis"]
        
        prompt = f"""
请基于以下需求分析结果，生成一个清晰、可执行的项目规划。

## 项目信息
项目名称：{project_title}
复杂度等级：{complexity_level}

## 核心目标
{chr(10).join([f"- {obj}" for obj in core_objectives])}

## 关键洞察
{chr(10).join([f"- {insight}" for insight in key_insights])}

## 高优先级功能
{chr(10).join([f"- {feature.get('name', '')}: {feature.get('description', '')}" for feature in high_priority_features])}

## 约束条件
- 时间约束：{constraints_analysis.get('timeline', '未指定')}
- 预算约束：{constraints_analysis.get('budget', '未指定')}
- 资源约束：{constraints_analysis.get('resources', '未指定')}

请生成包含以下内容的执行规划：

1. **执行阶段**：将项目分解为清晰的执行阶段
2. **阶段交付物**：每个阶段的具体产出
3. **依赖关系**：阶段间的依赖关系
4. **风险识别**：潜在风险和应对策略
5. **资源需求**：人力和技术资源需求
6. **质量保证**：评审点和验证方法

请严格按照以下JSON格式返回结果：

{{
    "planning_approach": "waterfall|agile|hybrid",
    "execution_phases": [
        {{
            "phase_id": "phase_1",
            "phase_name": "阶段名称",
            "description": "阶段描述",
            "deliverables": ["交付物1", "交付物2"],
            "dependencies": ["依赖的阶段ID"],
            "risks": ["风险点1", "风险点2"],
            "success_criteria": ["成功标准1", "成功标准2"]
        }}
    ],
    "resource_requirements": {{
        "human_resources": ["角色1", "角色2"],
        "technical_resources": ["技术资源1", "技术资源2"],
        "external_dependencies": ["外部依赖1", "外部依赖2"]
    }},
    "timeline_overview": {{
        "critical_path": ["关键阶段1", "关键阶段2"],
        "milestone_dates": {{}}
    }},
    "quality_assurance": {{
        "review_points": ["评审点1", "评审点2"],
        "testing_strategy": "测试策略描述",
        "validation_methods": ["验证方法1", "验证方法2"]
    }}
}}

请确保：
1. 阶段划分合理，每个阶段有明确的目标和交付物
2. 依赖关系清晰，符合实际开发流程
3. 考虑项目的复杂度和约束条件
4. 风险识别全面，应对策略具体
5. 资源需求明确，技术栈合理
6. 质量保证措施完善
"""
        
        return prompt
    
    def _validate_planning_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证和处理规划结果"""

        # 确保必需的字段存在，按照文档规范
        validated_result = {
            "planning_approach": result.get("planning_approach", "hybrid"),
            "execution_phases": result.get("execution_phases", []),
            "resource_requirements": result.get("resource_requirements", {}),
            "timeline_overview": result.get("timeline_overview", {}),
            "quality_assurance": result.get("quality_assurance", {})
        }

        # 验证阶段数量
        phases = validated_result["execution_phases"]
        if len(phases) < 2:
            # 如果阶段太少，添加基础阶段
            if not phases:
                validated_result["execution_phases"] = [
                    {
                        "phase_id": "phase_1",
                        "phase_name": "需求确认与设计",
                        "description": "确认需求并完成初步设计",
                        "deliverables": ["需求规格说明书", "系统设计文档"],
                        "dependencies": [],
                        "risks": ["需求变更风险"],
                        "success_criteria": ["需求确认完成", "设计评审通过"]
                    },
                    {
                        "phase_id": "phase_2",
                        "phase_name": "开发实现",
                        "description": "核心功能开发与实现",
                        "deliverables": ["功能模块", "单元测试"],
                        "dependencies": ["phase_1"],
                        "risks": ["技术实现风险"],
                        "success_criteria": ["功能开发完成", "测试通过"]
                    },
                    {
                        "phase_id": "phase_3",
                        "phase_name": "测试与部署",
                        "description": "系统测试与生产部署",
                        "deliverables": ["测试报告", "部署文档"],
                        "dependencies": ["phase_2"],
                        "risks": ["部署风险"],
                        "success_criteria": ["测试完成", "成功部署"]
                    }
                ]

        # 确保每个阶段都有基本信息
        for i, phase in enumerate(validated_result["execution_phases"]):
            if not phase.get("phase_id"):
                phase["phase_id"] = f"phase_{i + 1}"
            if not phase.get("phase_name"):
                phase["phase_name"] = f"阶段 {i + 1}"
            if not phase.get("deliverables"):
                phase["deliverables"] = []
            if not phase.get("dependencies"):
                phase["dependencies"] = []
            if not phase.get("risks"):
                phase["risks"] = []
            if not phase.get("success_criteria"):
                phase["success_criteria"] = []

        # 确保资源需求结构完整
        if not validated_result["resource_requirements"]:
            validated_result["resource_requirements"] = {
                "human_resources": [],
                "technical_resources": [],
                "external_dependencies": []
            }

        # 确保质量保证结构完整
        if not validated_result["quality_assurance"]:
            validated_result["quality_assurance"] = {
                "review_points": [],
                "testing_strategy": "",
                "validation_methods": []
            }

        return validated_result
