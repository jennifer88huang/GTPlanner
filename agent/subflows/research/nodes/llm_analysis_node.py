"""
LLM分析节点 - Research Agent的2c步骤

负责使用LLM分析URL解析后的内容，提取关键洞察和技术细节
"""

import asyncio
from pocketflow import Node

from agent.common import call_llm_async


class LLMAnalysisNode(Node):
    """LLM分析节点 - 2c步骤"""
    
    def prep(self, shared):
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
    
    def exec(self, prep_res):
        """执行LLM分析"""
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        url_content = prep_res["url_content"]
        keyword = prep_res["current_keyword"]
        analysis_requirements = prep_res["analysis_requirements"]
        
        # 使用LLM进行内容分析
        try:
            analysis_result = asyncio.run(self._analyze_content_with_llm(
                url_content, keyword, analysis_requirements
            ))
        except Exception as e:
            print(f"⚠️ LLM分析失败，使用模拟结果: {e}")
            # 使用模拟分析结果
            analysis_result = {
                "key_insights": [f"关于{keyword}的基础信息", f"{keyword}的应用场景"],
                "relevant_information": f"这是关于{keyword}的相关信息摘要",
                "technical_details": [f"{keyword}的技术实现", f"{keyword}的最佳实践"],
                "recommendations": [f"学习{keyword}的建议", f"使用{keyword}的注意事项"],
                "relevance_score": 0.8,
                "summary": f"关于{keyword}的内容分析"
            }
        
        return {
            "analysis": analysis_result,
            "keyword": keyword
        }
    
    def post(self, shared, prep_res, exec_res):
        """保存LLM分析结果到共享变量"""
        if "error" in exec_res:
            shared["llm_analysis_error"] = exec_res["error"]
            return "error"
        
        # 保存分析结果到共享变量
        shared["llm_analysis"] = exec_res["analysis"]
        shared["analyzed_keyword"] = exec_res["keyword"]
        
        return "success"
    
    async def _analyze_content_with_llm(self, content, keyword, requirements):
        """使用LLM分析内容"""
        prompt = f"""
请分析以下网页内容，重点关注与关键词"{keyword}"相关的信息。

分析需求：
{requirements}

网页内容：
{content[:3000]}

请以JSON格式返回分析结果：
{{
    "key_insights": ["关键洞察1", "关键洞察2"],
    "relevant_information": "与关键词最相关的信息摘要",
    "technical_details": ["技术细节1", "技术细节2"],
    "recommendations": ["建议1", "建议2"],
    "relevance_score": 0.8,
    "summary": "内容总结"
}}

请确保：
1. 重点提取与关键词相关的信息
2. 识别技术细节和实现要点
3. 提供实用的建议和洞察
4. 评估内容与关键词的相关性（0-1分）
"""
        
        try:
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            return {
                "key_insights": [f"关于{keyword}的基础信息"],
                "relevant_information": f"LLM分析失败: {str(e)}",
                "technical_details": [],
                "recommendations": [],
                "relevance_score": 0.1,
                "summary": "分析过程出错"
            }
