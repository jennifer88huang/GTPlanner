"""
结果组装节点 - Research Agent的2d步骤

负责将搜索结果、URL内容和LLM分析结果组装成单个关键词的完整报告
"""

import time
from pocketflow import AsyncNode


class ResultAssemblyNode(AsyncNode):
    """结果组装节点 - 2d步骤"""
    
    async def prep_async(self, shared):
        """准备结果组装"""
        # 从共享变量中获取所有必要数据
        current_keyword = shared.get("current_keyword", "")
        search_result = shared.get("first_search_result", {})
        url_content = shared.get("url_content", "")
        llm_analysis = shared.get("llm_analysis", {})
        
        return {
            "keyword": current_keyword,
            "url": search_result.get("url", ""),
            "title": search_result.get("title", ""),
            "content": url_content,
            "analysis": llm_analysis
        }
    
    async def exec_async(self, prep_res):
        """执行结果组装"""
        # 组装单个关键词的完整报告
        keyword_report = {
            "keyword": prep_res["keyword"],
            "url": prep_res["url"],
            "title": prep_res["title"],
            "content": prep_res["content"][:1000] + "..." if len(prep_res["content"]) > 1000 else prep_res["content"],
            "analysis": prep_res["analysis"],
            "processed_at": time.time()
        }
        
        return {"keyword_report": keyword_report}
    
    async def post_async(self, shared, prep_res, exec_res):
        """保存组装结果到共享变量"""
        if "error" in exec_res:
            return "error"

        # 保存单个关键词报告到共享变量
        keyword_report = exec_res["keyword_report"]
        shared["keyword_report"] = keyword_report

        # 设置research_findings格式，供function calling工具使用
        research_keywords = shared.get("research_keywords", ["技术调研"])
        shared["research_findings"] = {
            "topics": research_keywords,
            "results": [keyword_report],  # 包装为列表
            "summary": keyword_report.get("summary", "技术调研完成")
        }

        print(f"✅ 研究结果组装完成，关键词: {research_keywords}")

        return "success"
