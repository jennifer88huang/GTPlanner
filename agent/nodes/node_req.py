"""
需求解析节点 (Node_Req)

从自然语言对话中提取结构化的需求信息。
基于架构文档中定义的输入输出规格实现。

功能描述：
- 文本预处理和分词
- 实体识别和分类  
- 意图识别和功能点提取
- 约束条件识别
- 结果结构化和置信度评估
"""


from typing import Dict, Any
from pocketflow import AsyncNode

# 导入LLM工具
from agent.llm_utils import call_llm_async


class NodeReq(AsyncNode):
    """需求解析节点 - 完全基于LLM进行需求分析"""

    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化需求解析节点

        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)

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
                    "context_history": [],
                    "extraction_focus": ["entities", "functions", "constraints"]
                }

            # 获取所有消息
            all_messages = dialogue_history.get("messages", [])
            if not all_messages:
                return {
                    "error": "No messages found",
                    "dialogue_text": "",
                    "context_history": [],
                    "extraction_focus": ["entities", "functions", "constraints"]
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
                    "context_history": [],
                    "extraction_focus": ["entities", "functions", "constraints"]
                }

            return {
                "dialogue_text": dialogue_text,
                "context_history": context_history,
                "extraction_focus": ["entities", "functions", "constraints"],
                "message_count": message_count,
                "total_length": len(dialogue_text)
            }
            
        except Exception as e:
            return {
                "error": f"Preparation failed: {str(e)}",
                "dialogue_text": "",
                "context_history": [],
                "extraction_focus": []
            }
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        异步执行阶段：使用LLM执行需求解析

        Args:
            prep_res: 准备阶段的结果

        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])

        dialogue_text = prep_res["dialogue_text"]

        if not dialogue_text.strip():
            raise ValueError("Empty dialogue text")

        try:
            # 使用LLM进行需求分析 - 异步调用
            analysis_result = await self._analyze_requirements_with_llm_async(dialogue_text)

            return {
                "extracted_entities": analysis_result.get("extracted_entities", {}),
                "functional_requirements": analysis_result.get("functional_requirements", {}),
                "non_functional_requirements": analysis_result.get("non_functional_requirements", {}),
                "confidence_score": analysis_result.get("confidence_score", 0.5),
                "processed_text_length": len(dialogue_text),
                "extraction_metadata": {
                    "processing_time": analysis_result.get("processing_time", 0),
                    "text_complexity": analysis_result.get("text_complexity", "medium"),
                    "extraction_method": "llm_based_analysis"
                },
                "user_intent": analysis_result.get("user_intent", {}),
                "project_overview": analysis_result.get("project_overview", {})
            }

        except Exception as e:
            raise RuntimeError(f"LLM requirement extraction failed: {str(e)}")

    async def _analyze_requirements_with_llm_async(self, dialogue_text: str) -> Dict[str, Any]:
        """使用LLM分析需求"""

        prompt = f"""
请分析以下完整的对话历史，提取结构化的项目需求信息。对话包含用户和助手的交互，请重点关注用户的需求表达和项目要求。

完整对话历史：
{dialogue_text}

请按照以下JSON结构返回分析结果：
{{
    "extracted_entities": {{
        "business_objects": ["实体1", "实体2"],
        "actors": ["角色1", "角色2"],
        "systems": ["系统1", "系统2"]
    }},
    "functional_requirements": {{
        "core_features": ["功能1", "功能2"],
        "user_stories": ["用户故事1", "用户故事2"],
        "workflows": ["工作流1", "工作流2"]
    }},
    "non_functional_requirements": {{
        "performance": ["性能要求1", "性能要求2"],
        "security": ["安全要求1", "安全要求2"],
        "scalability": ["扩展性要求1", "扩展性要求2"]
    }},
    "user_intent": {{
        "primary_goal": "主要目标",
        "intent_category": "planning/analysis/design/research",
        "domain_context": "领域上下文",
        "complexity_level": "simple/medium/complex"
    }},
    "project_overview": {{
        "title": "项目标题",
        "description": "项目描述",
        "scope": "项目范围",
        "objectives": ["目标1", "目标2"],
        "success_criteria": ["成功标准1", "成功标准2"]
    }},
    "confidence_score": 0.8,
    "text_complexity": "medium",
    "processing_time": 1000
}}

请确保：
1. 仔细分析用户的真实需求，不要添加用户没有提到的内容
2. 提取的实体、功能、角色等都应该基于用户的实际描述
3. 置信度应该基于需求描述的清晰程度和完整性
4. 所有字段都必须填写，如果某个方面用户没有明确提及，可以填写空数组或合理的默认值
"""

        try:
            result = await call_llm_async(prompt, is_json=True)

            # 确保返回的是字典格式
            if isinstance(result, str):
                import json
                try:
                    result = json.loads(result)
                except json.JSONDecodeError:
                    print(f"❌ LLM返回的不是有效JSON: {result[:200]}...")
                    # 返回默认结构
                    result = {
                        "extracted_entities": {},
                        "functional_requirements": {},
                        "non_functional_requirements": {},
                        "user_intent": {},
                        "project_overview": {},
                        "confidence_score": 0.1,
                        "text_complexity": "unknown",
                        "processing_time": 0
                    }

            return result
        except Exception as e:
            # LLM调用失败，直接抛出异常
            print(f"❌ LLM调用失败: {e}")
            raise e

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将LLM分析结果更新到pocketflow字典共享变量

        Args:
            shared: pocketflow字典共享变量
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果

        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared["requirement_analysis_error"] = exec_res["error"]
                return "error"

            # 更新共享变量
            shared["extracted_entities"] = exec_res["extracted_entities"]
            shared["functional_requirements"] = exec_res["functional_requirements"]
            shared["non_functional_requirements"] = exec_res["non_functional_requirements"]
            shared["user_intent"] = exec_res["user_intent"]
            shared["project_overview"] = exec_res["project_overview"]
            shared["confidence_score"] = exec_res["confidence_score"]
            shared["extraction_metadata"] = exec_res["extraction_metadata"]

            # 标记需求分析完成
            shared["requirement_analysis_complete"] = True

            return "success"

        except Exception as e:
            shared["requirement_analysis_error"] = str(e)
            return "error"