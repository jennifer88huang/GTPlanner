"""
LLM分析节点 - Research Agent的2c步骤

负责使用LLM分析URL解析后的内容，提取关键洞察和技术细节
"""

import asyncio
from pocketflow import AsyncNode

from agent.llm_utils import call_llm_async


class LLMAnalysisNode(AsyncNode):
    """LLM分析节点 - 2c步骤"""
    
    def __init__(self):
        super().__init__()
        self.name = "LLMAnalysisNode"
    
    async def prep_async(self, shared):
        """准备LLM分析"""
        # 从共享变量中获取URL解析结果
        url_content = shared.get("url_content", "")
        current_keyword = shared.get("current_keyword", "")
        analysis_requirements = shared.get("analysis_requirements", "")
        
        if not url_content:
            return {"error": "No URL content available for analysis"}
        
        return {
            "url_content": url_content,
            "current_keyword": current_keyword,
            "analysis_requirements": analysis_requirements
        }
    
    async def exec_async(self, prep_res):
        """执行LLM分析"""
        if "error" in prep_res:
            return {"error": prep_res["error"]}

        url_content = prep_res["url_content"]
        keyword = prep_res["current_keyword"]
        analysis_requirements = prep_res["analysis_requirements"]

        # 使用LLM进行内容分析 - 异步调用
        try:
            analysis_result = await self._analyze_content_with_llm_async(
                url_content, keyword, analysis_requirements
            )

            return {
                "analysis": analysis_result,
                "keyword": keyword
            }

        except Exception as e:
            error_msg = f"LLM分析执行失败: {str(e)}"
            print(f"❌ {error_msg}")

            # 返回错误结果而不是抛出异常，让post_async处理
            return {
                "error": error_msg,
                "keyword": keyword,
                "failed_stage": "llm_analysis"
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        """保存LLM分析结果到共享变量"""
        try:
            if "error" in exec_res:
                # 记录执行阶段的错误
                error_info = {
                    "source": "LLMAnalysisNode.exec",
                    "error": exec_res["error"],
                    "keyword": prep_res.get("current_keyword", "unknown"),
                    "timestamp": prep_res.get("timestamp", ""),
                    "stage": "execution"
                }

                if "errors" not in shared:
                    shared["errors"] = []
                shared["errors"].append(error_info)

                # 设置分析失败状态
                shared["llm_analysis_status"] = "failed"
                shared["llm_analysis_error"] = exec_res["error"]

                print(f"❌ LLM分析执行失败: {exec_res['error']}")
                return "error"

            # 保存分析结果到共享变量
            analysis_result = exec_res["analysis"]
            keyword = exec_res["keyword"]

            shared["llm_analysis"] = analysis_result
            shared["analyzed_keyword"] = keyword
            shared["llm_analysis_status"] = "success"

            print(f"✅ LLM分析完成: {keyword}")
            return "analysis_complete"

        except Exception as e:
            # 记录后处理阶段的错误
            error_info = {
                "source": "LLMAnalysisNode.post",
                "error": str(e),
                "keyword": prep_res.get("current_keyword", "unknown"),
                "timestamp": prep_res.get("timestamp", ""),
                "stage": "post_processing"
            }

            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append(error_info)

            # 设置分析失败状态
            shared["llm_analysis_status"] = "failed"
            shared["llm_analysis_post_error"] = str(e)

            print(f"❌ LLM分析后处理失败: {e}")
            return "error"
    
    async def _analyze_content_with_llm_async(self, content, keyword, requirements):
        """异步使用LLM分析内容"""
        # 系统提示词：定义角色和输出格式
        system_prompt = """你是一个专业的内容分析专家，擅长从大量文本中提取关键信息和洞察。

你的任务是：
1. 分析给定的内容，重点关注与指定关键词相关的信息
2. 提取核心要点和技术细节
3. 提供实用的建议和洞察
4. 严格按照指定的JSON格式输出结果

输出格式要求：
- 必须返回有效的JSON格式
- 包含summary、key_points、relevance、recommendations四个字段
- key_points和recommendations必须是数组格式
- 内容要简洁明了，避免冗余信息"""

        # 用户提示词：具体的分析任务
        user_prompt = f"""请分析以下内容，重点关注与"{keyword}"相关的信息。

分析要求：{requirements}

内容：
{content[:2000]}

请严格按照以下JSON格式返回分析结果：
{{
    "summary": "核心内容总结",
    "key_points": ["要点1", "要点2", "要点3"],
    "relevance": "与{keyword}的相关性说明",
    "recommendations": ["建议1", "建议2"]
}}"""

        try:
            result = await call_llm_async(
                user_prompt,
                is_json=True,
                system_prompt=system_prompt
            )

            # 确保返回标准格式
            if isinstance(result, str):
                import json
                result = json.loads(result)

            # 标准化返回格式
            return {
                "summary": result.get("summary", f"关于{keyword}的分析"),
                "key_points": result.get("key_points", []),
                "relevance": result.get("relevance", "相关性分析"),
                "recommendations": result.get("recommendations", []),
                "keyword": keyword
            }
        except Exception as e:
            # 抛出异常，让上层处理
            raise Exception(f"LLM内容分析失败: {str(e)}")
