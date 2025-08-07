"""
LLM Structure Node

使用LLM将提取的需求信息进行结构化处理，生成标准化的项目需求文档。
"""

import json
from typing import Dict, Any
from pocketflow import AsyncNode
from agent.llm_utils import call_llm_async


class LLMStructureNode(AsyncNode):
    """LLM结构化节点"""

    def __init__(self):
        super().__init__()
        self.name = "LLMStructureNode"
        self.description = "使用LLM将提取的需求信息进行结构化处理"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备LLM结构化处理"""
        # 获取NodeReq提取的信息
        extracted_info = {
            "extracted_entities": shared.get("extracted_entities", {}),
            "functional_requirements": shared.get("functional_requirements", {}),
            "non_functional_requirements": shared.get("non_functional_requirements", {}),
            "project_overview": shared.get("project_overview", {}),
            "confidence_score": shared.get("confidence_score", 0.5),
            "extraction_metadata": shared.get("extraction_metadata", {})
        }
        dialogue_history = shared.get("dialogue_history", "")
        user_intent = shared.get("user_intent", {})

        return {
            "extracted_info": extracted_info,
            "dialogue_history": dialogue_history,
            "user_intent": user_intent
        }
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行LLM结构化处理"""
        try:
            extracted_info = prep_result["extracted_info"]
            dialogue_history = prep_result["dialogue_history"]
            user_intent = prep_result["user_intent"]

            # 构建LLM prompt
            prompt = self._build_structure_prompt(extracted_info, dialogue_history, user_intent)

            # 异步调用LLM进行结构化
            structured_result = await self._call_llm_structure_async(prompt)

            return {
                "structured_requirements": structured_result,
                "processing_success": True
            }

        except Exception as e:
            print(f"❌ LLM结构化处理失败: {e}")
            return {
                "error": str(e),
                "processing_success": False
            }
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存结构化结果"""
        if "error" in exec_res:
            shared["llm_structure_error"] = exec_res["error"]
            return "error"
        
        # 保存结构化需求到共享变量
        structured_requirements = exec_res.get("structured_requirements", {})
        shared["structured_requirements"] = structured_requirements
        
        print(f"✅ LLM结构化完成，生成了 {len(structured_requirements.get('functional_requirements', {}).get('core_features', []))} 个核心功能")
        
        return "success"
    
    def _build_structure_prompt(self, extracted_info: Dict[str, Any], 
                               dialogue_history: str, user_intent: Dict[str, Any]) -> str:
        """构建LLM结构化prompt"""
        
        prompt = f"""
请将以下提取的需求信息进行结构化处理，生成标准化的项目需求文档。

## 提取的需求信息：
{json.dumps(extracted_info, ensure_ascii=False, indent=2)}

## 原始对话历史：
{dialogue_history}

## 用户意图：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

请按照以下JSON格式输出结构化的项目需求：

{{
    "project_overview": {{
        "title": "项目标题",
        "description": "项目描述",
        "objectives": ["目标1", "目标2"],
        "target_users": ["用户群体1", "用户群体2"],
        "success_criteria": ["成功标准1", "成功标准2"]
    }},
    "functional_requirements": {{
        "core_features": [
            {{
                "name": "功能名称",
                "description": "功能描述",
                "priority": "high/medium/low",
                "acceptance_criteria": ["验收标准1", "验收标准2"]
            }}
        ],
        "user_stories": [
            {{
                "role": "用户角色",
                "goal": "用户目标",
                "benefit": "用户收益"
            }}
        ]
    }},
    "non_functional_requirements": {{
        "performance": {{
            "response_time": "响应时间要求",
            "throughput": "吞吐量要求",
            "concurrent_users": "并发用户数"
        }},
        "security": {{
            "authentication": "认证要求",
            "authorization": "授权要求",
            "data_protection": "数据保护要求"
        }},
        "scalability": {{
            "horizontal_scaling": "水平扩展要求",
            "vertical_scaling": "垂直扩展要求"
        }}
    }},
    "technical_requirements": {{
        "programming_languages": ["编程语言"],
        "frameworks": ["框架"],
        "databases": ["数据库"],
        "deployment": ["部署方式"],
        "monitoring": ["监控工具"]
    }},
    "constraints": {{
        "budget": "预算约束",
        "timeline": "时间约束",
        "resources": "资源约束",
        "compliance": ["合规要求"]
    }}
}}

请确保：
1. 所有字段都有合理的值，不要留空
2. 优先级要合理分配（high/medium/low）
3. 技术要求要符合项目实际需求
4. 约束条件要现实可行
"""
        
        return prompt
    
    async def _call_llm_structure_async(self, prompt: str) -> Dict[str, Any]:
        """异步调用LLM进行结构化处理"""
        try:
            # 使用异步版本调用LLM
            result = await call_llm_async(prompt, is_json=True)

            # 确保返回的是字典格式
            if isinstance(result, str):
                import json
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    print(f"❌ LLM返回的不是有效JSON: {result[:200]}...")
                    raise ValueError("LLM返回的结果格式不符合要求")

            # 验证LLM返回的结果格式
            if isinstance(result, dict) and self._validate_llm_result(result):
                return result
            else:
                print("❌ LLM返回格式不正确")
                raise ValueError("LLM返回的结果格式不符合要求")

        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            raise e



    def _validate_llm_result(self, result: Dict[str, Any]) -> bool:
        """验证LLM返回结果的格式"""
        try:
            # 检查必需的顶级字段
            required_fields = [
                "project_overview",
                "functional_requirements",
                "non_functional_requirements",
                "technical_requirements"
            ]

            for field in required_fields:
                if field not in result:
                    return False

            # 检查project_overview的必需字段
            project_overview = result.get("project_overview", {})
            if not all(field in project_overview for field in ["title", "description"]):
                return False

            # 检查functional_requirements的必需字段
            func_req = result.get("functional_requirements", {})
            if "core_features" not in func_req or not isinstance(func_req["core_features"], list):
                return False

            return True

        except Exception:
            return False

   