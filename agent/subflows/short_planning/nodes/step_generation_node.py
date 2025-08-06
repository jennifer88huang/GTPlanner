"""
Step Generation Node

基于功能模块分析结果，使用LLM生成清晰的实现步骤序列。
"""

import time
import sys
import os
import asyncio
from typing import Dict, Any, List

# 添加utils路径以导入call_llm
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'utils'))


from pocketflow import AsyncNode


class StepGenerationNode(AsyncNode):
    """步骤生成节点 - 使用LLM生成实现步骤序列"""
    
    def __init__(self):
        super().__init__()
        self.name = "StepGenerationNode"
        self.description = "基于功能模块分析生成实现步骤序列"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取功能模块分析结果"""
        try:
            # 获取功能模块分析结果
            function_modules = shared.get("function_modules", {})
            if not function_modules:
                return {"error": "No function modules found"}
            
            # 获取原始需求作为参考
            structured_requirements = shared.get("structured_requirements", {})
            
            return {
                "function_modules": function_modules,
                "structured_requirements": structured_requirements,
                "generation_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Step generation preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行步骤生成"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            function_modules = prep_result["function_modules"]
            structured_requirements = prep_result["structured_requirements"]
            
            # 使用异步LLM生成实现步骤
            implementation_steps = await self._generate_steps_with_llm(
                function_modules, structured_requirements
            )
            
            return {
                "implementation_steps": implementation_steps,
                "generation_success": True
            }
            
        except Exception as e:
            raise e
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存步骤生成结果"""
        if "error" in exec_res:
            shared["step_generation_error"] = exec_res["error"]
            return "error"
        
        # 保存实现步骤
        shared["implementation_steps"] = exec_res["implementation_steps"]
        
        steps_count = len(exec_res["implementation_steps"].get("steps", []))
        print(f"✅ 实现步骤生成完成，包含 {steps_count} 个步骤")
        return "success"
    
    async def _generate_steps_with_llm(self, function_modules: Dict[str, Any],
                                     structured_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """使用异步LLM生成实现步骤"""

        # 构建LLM提示词
        prompt = self._build_step_generation_prompt(function_modules, structured_requirements)

        # 调用异步LLM
        from call_llm import call_llm_async
        result = await call_llm_async(prompt, is_json=True)

        # 验证和处理结果
        validated_result = self._validate_steps_result(result, function_modules)

        return validated_result
    
    def _build_step_generation_prompt(self, function_modules: Dict[str, Any], 
                                    structured_requirements: Dict[str, Any]) -> str:
        """构建步骤生成的LLM提示词"""
        
        # 提取关键信息
        project_overview = structured_requirements.get("project_overview", {})
        project_title = project_overview.get("title", "项目")
        project_description = project_overview.get("description", "")
        
        core_modules = function_modules.get("core_modules", [])
        implementation_sequence = function_modules.get("implementation_sequence", [])
        technical_stack = function_modules.get("technical_stack", {})
        
        # 构建模块信息
        modules_info = []
        for module in core_modules:
            module_info = f"- {module['module_name']}: {module['description']}"
            if module.get('technical_requirements'):
                module_info += f" (技术要求: {', '.join(module['technical_requirements'])})"
            modules_info.append(module_info)
        
        prompt = f"""
请为以下项目生成清晰的功能实现步骤序列。

## 项目信息
项目名称：{project_title}
项目描述：{project_description}

## 核心功能模块
{chr(10).join(modules_info)}

## 技术栈
- 前端：{', '.join(technical_stack.get('frontend', []))}
- 后端：{', '.join(technical_stack.get('backend', []))}
- 数据库：{', '.join(technical_stack.get('database', []))}
- 基础设施：{', '.join(technical_stack.get('infrastructure', []))}

## 实现顺序
{', '.join([f"模块{i+1}" for i in range(len(implementation_sequence))])}

请生成5-8个清晰的实现步骤，每个步骤应该：
1. 有明确的功能目标
2. 包含具体的技术实现要点
3. 明确涉及的功能模块
4. 产出明确的交付物

请以JSON格式返回结果：

{{
    "steps": [
        {{
            "step_number": 1,
            "step_name": "步骤名称",
            "description": "详细描述这个步骤要实现什么功能",
            "target_modules": ["涉及的模块ID"],
            "key_deliverables": ["关键产出1", "关键产出2"],
            "technical_focus": ["技术重点1", "技术重点2"]
        }}
    ],
    "critical_path": ["关键步骤的step_number"],
    "parallel_opportunities": ["可以并行开发的步骤说明"]
}}

请确保：
1. 步骤顺序符合开发逻辑（如：先基础功能，后高级功能）
2. 每个步骤都有明确的技术实现重点
3. 交付物具体且可验证
4. 考虑模块间的依赖关系
5. 专注于功能实现，不包含部署运维步骤
"""
        
        return prompt
    
    def _validate_steps_result(self, result: Dict[str, Any], 
                             function_modules: Dict[str, Any]) -> Dict[str, Any]:
        """验证和处理步骤结果"""
        
        # 确保必需的字段存在
        validated_result = {
            "steps": result.get("steps", []),
            "critical_path": result.get("critical_path", []),
            "parallel_opportunities": result.get("parallel_opportunities", [])
        }
        
        # 验证步骤数量
        steps = validated_result["steps"]
        if len(steps) < 3:
            # 如果步骤太少，基于模块生成基础步骤
            core_modules = function_modules.get("core_modules", [])
            implementation_sequence = function_modules.get("implementation_sequence", [])
            
            basic_steps = []
            for i, module_id in enumerate(implementation_sequence[:5], 1):
                # 找到对应的模块
                module = next((m for m in core_modules if m["module_id"] == module_id), None)
                if module:
                    step = {
                        "step_number": i,
                        "step_name": f"实现{module['module_name']}",
                        "description": f"开发{module['module_name']}的核心功能：{module['description']}",
                        "target_modules": [module_id],
                        "key_deliverables": [f"{module['module_name']}功能模块", "相关API接口"],
                        "technical_focus": module.get("technical_requirements", ["功能实现"])
                    }
                    basic_steps.append(step)
            
            if basic_steps:
                validated_result["steps"] = basic_steps
        
        # 确保每个步骤都有基本信息
        for i, step in enumerate(validated_result["steps"]):
            if not step.get("step_number"):
                step["step_number"] = i + 1
            if not step.get("step_name"):
                step["step_name"] = f"实现步骤 {i + 1}"
            if not step.get("target_modules"):
                step["target_modules"] = []
            if not step.get("key_deliverables"):
                step["key_deliverables"] = []
            if not step.get("technical_focus"):
                step["technical_focus"] = []
        
        return validated_result
