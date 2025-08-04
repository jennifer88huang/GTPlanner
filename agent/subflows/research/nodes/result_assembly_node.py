"""
结果组装节点 - Research Agent的2d步骤

负责将搜索结果、URL内容和LLM分析结果组装成单个关键词的完整报告
"""

import time
from pocketflow import Node


class ResultAssemblyNode(Node):
    """结果组装节点 - 2d步骤"""
    
    def prep(self, shared):
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
    
    def exec(self, prep_res):
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
    
    def post(self, shared, prep_res, exec_res):
        """保存组装结果到共享变量"""
        if "error" in exec_res:
            return "error"
        
        # 保存单个关键词报告到共享变量
        shared["keyword_report"] = exec_res["keyword_report"]
        
        return "success"
