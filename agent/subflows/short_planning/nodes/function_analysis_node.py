"""
Function Analysis Node

从结构化需求中识别核心功能模块，为实现步骤生成做准备。
"""

import time
from typing import Dict, Any, List
from pocketflow import Node


class FunctionAnalysisNode(Node):
    """功能分析节点 - 识别核心功能模块"""
    
    def __init__(self):
        super().__init__()
        self.name = "FunctionAnalysisNode"
        self.description = "从结构化需求中识别核心功能模块"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取结构化需求"""
        try:
            # 获取结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            if not structured_requirements:
                return {"error": "No structured requirements found"}
            
            return {
                "structured_requirements": structured_requirements,
                "analysis_timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Function analysis preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行功能分析"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            structured_requirements = prep_result["structured_requirements"]
            
            # 分析核心功能模块
            core_modules = self._analyze_core_modules(structured_requirements)
            
            # 确定实现顺序
            implementation_sequence = self._determine_implementation_sequence(core_modules)
            
            # 分析技术栈需求
            technical_stack = self._analyze_technical_stack(structured_requirements, core_modules)
            
            return {
                "function_modules": {
                    "core_modules": core_modules,
                    "implementation_sequence": implementation_sequence,
                    "technical_stack": technical_stack
                },
                "analysis_success": True
            }
            
        except Exception as e:
            raise e
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存功能分析结果"""
        if "error" in exec_res:
            shared["function_analysis_error"] = exec_res["error"]
            return "error"
        
        # 保存分析结果
        shared["function_modules"] = exec_res["function_modules"]
        
        modules_count = len(exec_res["function_modules"]["core_modules"])
        print(f"✅ 功能分析完成，识别了 {modules_count} 个核心功能模块")
        return "success"
    
    def _analyze_core_modules(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析核心功能模块"""
        modules = []
        
        # 从功能需求中提取模块
        functional_req = requirements.get("functional_requirements", {})
        core_features = functional_req.get("core_features", [])
        
        for i, feature in enumerate(core_features, 1):
            if isinstance(feature, dict):
                module = {
                    "module_id": f"module_{i}",
                    "module_name": feature.get("name", f"功能模块{i}"),
                    "description": feature.get("description", ""),
                    "priority": feature.get("priority", "medium"),
                    "dependencies": [],
                    "technical_requirements": []
                }
                
                # 分析技术要求
                if "authentication" in module["module_name"].lower() or "登录" in module["module_name"]:
                    module["technical_requirements"] = ["用户认证", "会话管理", "权限控制"]
                elif "database" in module["description"].lower() or "数据" in module["module_name"]:
                    module["technical_requirements"] = ["数据库设计", "数据模型", "CRUD操作"]
                elif "api" in module["description"].lower() or "接口" in module["module_name"]:
                    module["technical_requirements"] = ["API设计", "接口文档", "数据验证"]
                
                modules.append(module)
        
        # 如果没有明确的功能特性，从项目描述中推断
        if not modules:
            project_overview = requirements.get("project_overview", {})
            project_title = project_overview.get("title", "")
            project_desc = project_overview.get("description", "")
            
            # 基于项目类型推断基础模块
            if any(keyword in (project_title + project_desc).lower() 
                   for keyword in ["管理", "系统", "平台"]):
                modules = [
                    {
                        "module_id": "module_1",
                        "module_name": "用户管理",
                        "description": "用户注册、登录、权限管理",
                        "priority": "high",
                        "dependencies": [],
                        "technical_requirements": ["用户认证", "权限控制"]
                    },
                    {
                        "module_id": "module_2", 
                        "module_name": "核心业务",
                        "description": "主要业务功能实现",
                        "priority": "high",
                        "dependencies": ["module_1"],
                        "technical_requirements": ["业务逻辑", "数据处理"]
                    },
                    {
                        "module_id": "module_3",
                        "module_name": "数据管理",
                        "description": "数据存储和管理功能",
                        "priority": "medium",
                        "dependencies": ["module_1"],
                        "technical_requirements": ["数据库设计", "数据备份"]
                    }
                ]
        
        return modules
    
    def _determine_implementation_sequence(self, modules: List[Dict[str, Any]]) -> List[str]:
        """确定实现顺序"""
        # 按优先级和依赖关系排序
        high_priority = [m["module_id"] for m in modules if m["priority"] == "high"]
        medium_priority = [m["module_id"] for m in modules if m["priority"] == "medium"]
        low_priority = [m["module_id"] for m in modules if m["priority"] == "low"]
        
        # 基础模块优先（通常是用户认证相关）
        sequence = []
        
        # 先处理基础模块
        for module in modules:
            if any(keyword in module["module_name"].lower() 
                   for keyword in ["用户", "认证", "登录", "权限"]):
                if module["module_id"] not in sequence:
                    sequence.append(module["module_id"])
        
        # 然后按优先级添加其他模块
        for module_id in high_priority:
            if module_id not in sequence:
                sequence.append(module_id)
        
        for module_id in medium_priority:
            if module_id not in sequence:
                sequence.append(module_id)
        
        for module_id in low_priority:
            if module_id not in sequence:
                sequence.append(module_id)
        
        return sequence
    
    def _analyze_technical_stack(self, requirements: Dict[str, Any], 
                                modules: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """分析技术栈需求"""
        
        # 检查是否有明确的技术要求
        tech_req = requirements.get("technical_requirements", {})
        
        # 默认技术栈
        technical_stack = {
            "frontend": ["React", "TypeScript", "CSS3"],
            "backend": ["Node.js", "Express"],
            "database": ["PostgreSQL"],
            "infrastructure": ["Docker", "Nginx"]
        }
        
        # 根据明确的技术要求调整
        if tech_req:
            if "programming_languages" in tech_req:
                languages = tech_req["programming_languages"]
                if "Python" in languages:
                    technical_stack["backend"] = ["Python", "FastAPI"]
                elif "Java" in languages:
                    technical_stack["backend"] = ["Java", "Spring Boot"]
            
            if "frameworks" in tech_req:
                frameworks = tech_req["frameworks"]
                if "Vue" in frameworks:
                    technical_stack["frontend"] = ["Vue.js", "TypeScript"]
                elif "Angular" in frameworks:
                    technical_stack["frontend"] = ["Angular", "TypeScript"]
        
        # 根据功能模块调整技术栈
        has_realtime = any("实时" in m["description"] or "websocket" in m["description"].lower() 
                          for m in modules)
        if has_realtime:
            technical_stack["backend"].append("WebSocket")
        
        has_file_upload = any("文件" in m["description"] or "上传" in m["description"] 
                             for m in modules)
        if has_file_upload:
            technical_stack["infrastructure"].append("文件存储")
        
        return technical_stack
