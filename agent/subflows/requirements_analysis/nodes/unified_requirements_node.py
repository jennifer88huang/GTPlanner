"""
统一需求分析节点 (UnifiedRequirementsNode)

将原来的NodeReq和LLMStructureNode功能合并，只调用一次LLM就完成：
1. 从对话中提取需求信息
2. 直接生成结构化的项目需求文档

这样避免了重复的LLM调用，提高效率的同时保持结果质量。
"""

import json
from typing import Dict, Any
from pocketflow import AsyncNode
from agent.llm_utils import call_llm_async


class UnifiedRequirementsNode(AsyncNode):
    """统一需求分析节点 - 一次LLM调用完成完整需求分析和结构化"""

    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化统一需求分析节点

        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        self.name = "UnifiedRequirementsNode"
        self.description = "一次LLM调用完成需求提取和结构化处理"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备阶段：从pocketflow字典共享变量获取对话文本

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 从字典共享变量获取对话历史
            dialogue_history = shared.get("dialogue_history")
            user_intent = shared.get("user_intent", {})

            # 处理字典格式的对话历史
            if not isinstance(dialogue_history, dict) or "messages" not in dialogue_history:
                return {
                    "error": "Invalid dialogue history: expected dict with messages",
                    "dialogue_text": "",
                    "context_history": []
                }

            # 获取所有消息
            all_messages = dialogue_history.get("messages", [])
            if not all_messages:
                return {
                    "error": "No messages found",
                    "dialogue_text": "",
                    "context_history": []
                }

            # 获取完整的对话文本（包含用户和助手的所有消息）
            dialogue_text = "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in all_messages
            ])

            # 获取最近的消息作为上下文
            recent_messages = all_messages[-10:] if len(all_messages) > 10 else all_messages
            context_history = [f"{msg['role']}: {msg['content']}" for msg in recent_messages]
            message_count = len(all_messages)

            if not dialogue_text.strip():
                return {
                    "error": "Empty dialogue text",
                    "dialogue_text": "",
                    "context_history": []
                }

            return {
                "dialogue_text": dialogue_text,
                "context_history": context_history,
                "user_intent": user_intent,
                "message_count": message_count,
                "total_length": len(dialogue_text)
            }
            
        except Exception as e:
            return {
                "error": f"Preparation failed: {str(e)}",
                "dialogue_text": "",
                "context_history": []
            }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步执行阶段：使用LLM一次性完成需求分析和结构化

        Args:
            prep_res: 准备阶段的结果

        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])

        dialogue_text = prep_res["dialogue_text"]
        user_intent = prep_res.get("user_intent", {})

        if not dialogue_text.strip():
            raise ValueError("Empty dialogue text")

        try:
            # 使用LLM一次性完成需求分析和结构化
            unified_result = await self._unified_requirements_analysis_async(dialogue_text, user_intent)

            return {
                "structured_requirements": unified_result,
                "processing_success": True,
                "processed_text_length": len(dialogue_text),
                "extraction_metadata": {
                    "processing_method": "unified_llm_analysis",
                    "text_complexity": unified_result.get("analysis_metadata", {}).get("text_complexity", "medium"),
                    "confidence_score": unified_result.get("analysis_metadata", {}).get("confidence_score", 0.5)
                }
            }

        except Exception as e:
            raise RuntimeError(f"Unified LLM requirement analysis failed: {str(e)}")

    async def _unified_requirements_analysis_async(self, dialogue_text: str, user_intent: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM一次性完成需求分析和结构化"""

        prompt = f"""
请分析以下完整的对话历史，一次性完成需求提取和结构化处理，生成标准化的项目需求文档。

完整对话历史：
{dialogue_text}

用户意图信息：
{json.dumps(user_intent, ensure_ascii=False, indent=2)}

请按照以下JSON格式返回完整的结构化项目需求：

{{
    "project_overview": {{
        "title": "项目标题",
        "description": "项目描述",
        "objectives": ["目标1", "目标2"],
        "target_users": ["用户群体1", "用户群体2"],
        "success_criteria": ["成功标准1", "成功标准2"],
        "scope": "项目范围"
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
        ],
        "workflows": ["工作流1", "工作流2"]
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
    "extracted_entities": {{
        "business_objects": ["实体1", "实体2"],
        "actors": ["角色1", "角色2"],
        "systems": ["系统1", "系统2"]
    }},
    "analysis_metadata": {{
        "confidence_score": 0.8,
        "text_complexity": "medium"
    }}
}}

请确保：
1. 仔细分析用户的真实需求，不要添加用户没有提到的内容
2. 提取的实体、功能、角色等都应该基于用户的实际描述
3. 所有字段都有合理的值，不要留空
4. 优先级要合理分配（high/medium/low）
5. 置信度应该基于需求描述的清晰程度和完整性
6. 专注于核心业务需求，避免过度技术化
7. 最终输出只包含json文本,不要使用代码块包裹
"""

        try:
            result = await call_llm_async(prompt, is_json=True)

            # 确保返回的是字典格式
            if isinstance(result, str):
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    print(f"❌ LLM返回的不是有效JSON: {result[:200]}...")
                    # 返回默认结构
                    result = self._get_default_structure()

            # 验证LLM返回结果的格式
            if isinstance(result, dict) and self._validate_unified_result(result):
                return result
            else:
                print("❌ LLM返回格式不正确，使用默认结构")
                return self._get_default_structure()

        except Exception as e:
            print(f"❌ LLM调用失败: {e}")
            raise e

    def _validate_unified_result(self, result: Dict[str, Any]) -> bool:
        """验证LLM返回结果的格式"""
        try:
            # 检查必需的顶级字段
            required_fields = [
                "project_overview",
                "functional_requirements",
                "non_functional_requirements",
                "extracted_entities",
                "analysis_metadata"
            ]

            for field in required_fields:
                if field not in result:
                    print(f"❌ 缺少必需字段: {field}")
                    return False

            # 检查project_overview的必需字段
            project_overview = result.get("project_overview", {})
            if not all(field in project_overview for field in ["title", "description"]):
                print("❌ project_overview缺少必需字段")
                return False

            # 检查functional_requirements的必需字段
            func_req = result.get("functional_requirements", {})
            if "core_features" not in func_req or not isinstance(func_req["core_features"], list):
                print("❌ functional_requirements格式不正确")
                return False

            # 检查analysis_metadata
            metadata = result.get("analysis_metadata", {})
            if "confidence_score" not in metadata:
                print("❌ analysis_metadata缺少confidence_score")
                return False

            return True

        except Exception as e:
            print(f"❌ 验证过程出错: {e}")
            return False

    def _get_default_structure(self) -> Dict[str, Any]:
        """获取默认的结构化结果"""
        return {
            "project_overview": {
                "title": "未明确的项目",
                "description": "需要进一步明确项目需求",
                "objectives": [],
                "target_users": [],
                "success_criteria": [],
                "scope": "待定义"
            },
            "functional_requirements": {
                "core_features": [],
                "user_stories": [],
                "workflows": []
            },
            "non_functional_requirements": {
                "performance": {},
                "security": {},
                "scalability": {}
            },
            "extracted_entities": {
                "business_objects": [],
                "actors": [],
                "systems": []
            },
            "analysis_metadata": {
                "confidence_score": 0.1,
                "text_complexity": "unknown"
            }
        }

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将统一分析结果更新到pocketflow字典共享变量

        Args:
            shared: pocketflow字典共享变量
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果

        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res or not exec_res.get("processing_success", False):
                shared["requirement_analysis_error"] = exec_res.get("error", "处理失败")
                return "error"

            structured_requirements = exec_res.get("structured_requirements", {})
            
            # 更新共享变量 - 保持与原来节点相同的接口
            shared["structured_requirements"] = structured_requirements
            
            # 为了兼容性，也设置原来NodeReq的输出格式
            shared["extracted_entities"] = structured_requirements.get("extracted_entities", {})
            shared["functional_requirements"] = structured_requirements.get("functional_requirements", {})
            shared["non_functional_requirements"] = structured_requirements.get("non_functional_requirements", {})
            shared["project_overview"] = structured_requirements.get("project_overview", {})
            shared["user_intent"] = structured_requirements.get("analysis_metadata", {})
            shared["confidence_score"] = structured_requirements.get("analysis_metadata", {}).get("confidence_score", 0.5)
            shared["extraction_metadata"] = exec_res.get("extraction_metadata", {})

            # 标记需求分析完成
            shared["requirement_analysis_complete"] = True

            # 输出处理结果摘要
            core_features_count = len(structured_requirements.get("functional_requirements", {}).get("core_features", []))
            confidence_score = structured_requirements.get("analysis_metadata", {}).get("confidence_score", 0.5)
        
            return "requirements_complete"

        except Exception as e:
            shared["requirement_analysis_error"] = str(e)
            print(f"❌ 后处理阶段出错: {e}")
            return "error"
