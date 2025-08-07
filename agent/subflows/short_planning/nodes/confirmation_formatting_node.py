"""
Confirmation Formatting Node

将实现步骤格式化为用户友好的Markdown确认文档。
"""

import time
from typing import Dict, Any, List
from pocketflow import AsyncNode
from agent.shared_migration import field_validation_decorator


class ConfirmationFormattingNode(AsyncNode):
    """确认文档格式化节点 - 生成Markdown格式的确认文档"""
    
    def __init__(self):
        super().__init__()
        self.name = "ConfirmationFormattingNode"
        self.description = "将实现步骤格式化为用户友好的确认文档"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取实现步骤和相关数据"""
        try:
            # 获取实现步骤
            implementation_steps = shared.get("implementation_steps", {})
            if not implementation_steps:
                return {"error": "No implementation steps found"}
            
            # 获取功能模块信息
            function_modules = shared.get("function_modules", {})
            
            # 获取原始需求
            structured_requirements = shared.get("structured_requirements", {})
            
            return {
                "implementation_steps": implementation_steps,
                "function_modules": function_modules,
                "structured_requirements": structured_requirements,
                "formatting_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Confirmation formatting preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行确认文档格式化"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            implementation_steps = prep_result["implementation_steps"]
            function_modules = prep_result["function_modules"]
            structured_requirements = prep_result["structured_requirements"]
            
            # 生成确认文档
            confirmation_document = self._generate_confirmation_document(
                implementation_steps, function_modules, structured_requirements
            )
            
            return {
                "confirmation_document": confirmation_document,
                "formatting_success": True
            }
            
        except Exception as e:
            raise e
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存确认文档格式化结果"""
        if "error" in exec_res:
            shared["confirmation_formatting_error"] = exec_res["error"]
            return "error"
        
        # 保存确认文档
        shared["confirmation_document"] = exec_res["confirmation_document"]
        
        # 统计信息
        confirmation_doc = exec_res["confirmation_document"]
        content_length = len(confirmation_doc.get("content", ""))
        steps_count = len(confirmation_doc.get("structure", {}).get("implementation_steps", []))
        
        print(f"✅ 确认文档生成完成，包含 {steps_count} 个实现步骤，文档长度: {content_length} 字符")
        return "success"
    
    def _generate_confirmation_document(self, implementation_steps: Dict[str, Any],
                                      function_modules: Dict[str, Any],
                                      structured_requirements: Dict[str, Any]) -> Dict[str, Any]:
        """生成确认文档 - 按照文档规范格式"""
        
        # 获取项目基本信息
        project_overview = structured_requirements.get("project_overview", {})
        project_title = project_overview.get("title", "项目")
        
        # 生成Markdown内容
        markdown_content = self._generate_markdown_content(
            project_title, implementation_steps, function_modules, structured_requirements
        )
        
        # 按照文档规范生成confirmation_document结构
        confirmation_document = {
            "content": markdown_content,
            "structure": {
                "project_title": project_title,
                "implementation_steps": self._extract_step_structure(implementation_steps),
                "core_functions": self._extract_core_functions(function_modules),
                "technical_stack": function_modules.get("technical_stack", {}),
                "confirmation_points": self._generate_confirmation_points()
            },
            "metadata": {
                "format": "markdown",
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": "1.0"
            }
        }
        
        return confirmation_document
    
    def _generate_markdown_content(self, project_title: str, 
                                 implementation_steps: Dict[str, Any],
                                 function_modules: Dict[str, Any],
                                 structured_requirements: Dict[str, Any]) -> str:
        """生成Markdown格式的确认文档内容"""
        
        steps = implementation_steps.get("steps", [])
        core_modules = function_modules.get("core_modules", [])
        technical_stack = function_modules.get("technical_stack", {})
        
        # 构建Markdown内容
        content_sections = []
        
        # 1. 项目标题和描述
        project_overview = structured_requirements.get("project_overview", {})
        project_description = project_overview.get("description", "")
        
        content_sections.append(f"# {project_title} - 实现步骤")
        if project_description:
            content_sections.append(f"\n{project_description}\n")
        
        # 2. 实现步骤
        content_sections.append("## 🚀 实现步骤")
        content_sections.append("")
        
        for step in steps:
            step_number = step.get("step_number", "")
            step_name = step.get("step_name", "")
            description = step.get("description", "")
            key_deliverables = step.get("key_deliverables", [])
            technical_focus = step.get("technical_focus", [])
            
            content_sections.append(f"### {step_number}. {step_name}")
            content_sections.append(f"{description}")
            
            if key_deliverables:
                content_sections.append(f"**关键产出：** {', '.join(key_deliverables)}")
            
            if technical_focus:
                content_sections.append(f"**技术重点：** {', '.join(technical_focus)}")
            
            content_sections.append("")
        
        # 3. 核心功能点
        content_sections.append("## 📋 核心功能点")
        content_sections.append("")
        
        for module in core_modules:
            module_name = module.get("module_name", "")
            description = module.get("description", "")
            priority = module.get("priority", "medium")
            
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
            content_sections.append(f"- {priority_emoji} **{module_name}**：{description}")
        
        content_sections.append("")
        
        # 4. 技术实现要点
        content_sections.append("## 🛠 技术实现要点")
        content_sections.append("")
        
        for category, technologies in technical_stack.items():
            if technologies:
                category_name = {
                    "frontend": "前端技术",
                    "backend": "后端技术", 
                    "database": "数据库",
                    "infrastructure": "基础设施"
                }.get(category, category)
                
                content_sections.append(f"- **{category_name}**：{', '.join(technologies)}")
        
        content_sections.append("")
        
        # 5. 确认要点
        content_sections.append("## ✅ 确认要点")
        content_sections.append("")
        content_sections.append("请确认以下关键信息：")
        content_sections.append("")
        content_sections.append("- [ ] 功能模块划分是否完整？")
        content_sections.append("- [ ] 实现步骤顺序是否合理？")
        content_sections.append("- [ ] 技术栈选择是否合适？")
        content_sections.append("- [ ] 有无遗漏的核心功能？")
        content_sections.append("")
        content_sections.append("**如有任何疑问或需要调整的地方，请及时反馈。确认无误后，我们将按照此步骤开始功能实现。**")
        
        return chr(10).join(content_sections)
    
    def _extract_step_structure(self, implementation_steps: Dict[str, Any]) -> List[Dict[str, Any]]:
        """提取步骤结构信息"""
        
        steps = implementation_steps.get("steps", [])
        step_structure = []
        
        for step in steps:
            step_info = {
                "step_number": step.get("step_number", 0),
                "step_title": step.get("step_name", ""),
                "description": step.get("description", ""),
                "key_functions": step.get("key_deliverables", [])
            }
            step_structure.append(step_info)
        
        return step_structure
    
    def _extract_core_functions(self, function_modules: Dict[str, Any]) -> List[str]:
        """提取核心功能列表"""
        
        core_modules = function_modules.get("core_modules", [])
        core_functions = []
        
        for module in core_modules:
            module_name = module.get("module_name", "")
            if module_name:
                core_functions.append(module_name)
        
        return core_functions
    
    def _generate_confirmation_points(self) -> List[Dict[str, str]]:
        """生成确认点"""
        
        confirmation_points = [
            {
                "question": "功能模块划分是否完整？",
                "type": "function"
            },
            {
                "question": "实现步骤顺序是否合理？",
                "type": "sequence"
            },
            {
                "question": "技术栈选择是否合适？",
                "type": "tech"
            },
            {
                "question": "有无遗漏的核心功能？",
                "type": "function"
            }
        ]
        
        return confirmation_points
