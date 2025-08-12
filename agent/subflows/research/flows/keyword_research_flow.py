"""
关键词研究子流程

使用箭头函数编排单个关键词的完整研究流程：
搜索 → URL解析 → LLM分析 → 结果组装
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ....nodes.node_search import NodeSearch
from ....nodes.node_url import NodeURL
from ..nodes.llm_analysis_node import LLMAnalysisNode
from ..nodes.result_assembly_node import ResultAssemblyNode


@trace_flow(flow_name="KeywordResearchFlow")
class TracedKeywordResearchFlow(AsyncFlow):
    """带有tracing的关键词研究流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        keyword = shared.get("current_keyword", "未知关键词")
        print(f"🔍 启动关键词研究流程: {keyword}")
        shared["subflow_start_time"] = __import__('asyncio').get_event_loop().time()

        return {
            "subflow_id": f"keyword_research_{keyword}",
            "start_time": shared["subflow_start_time"],
            "keyword": keyword
        }

    async def post_async(self, shared, prep_result, exec_result):
        """流程级后处理"""
        flow_duration = __import__('asyncio').get_event_loop().time() - prep_result["start_time"]
        keyword = prep_result["keyword"]

        shared["subflow_metadata"] = {
            "subflow_id": prep_result["subflow_id"],
            "duration": flow_duration,
            "status": "completed",
            "keyword": keyword
        }

        print(f"✅ 关键词研究流程完成: {keyword}，耗时: {flow_duration:.3f}秒")
        return exec_result


def create_keyword_research_subflow():
    """
    创建单个关键词的研究子流程
    
    使用箭头函数编排：
    搜索 → URL解析 → LLM分析 → 结果组装
    """
    # 创建所有节点
    search_node = NodeSearch()
    url_node = NodeURL()
    llm_analysis_node = LLMAnalysisNode()
    assembly_node = ResultAssemblyNode()
    
    # 设置节点名称
    search_node.name = "research_search"
    url_node.name = "research_url_parser"
    llm_analysis_node.name = "llm_analysis"
    assembly_node.name = "result_assembly"
    
    # 使用pocketflow的条件转换语法 - 事件字符串表示状态
    search_node - "search_complete" >> url_node
    url_node - "url_parsed" >> llm_analysis_node
    llm_analysis_node - "analysis_complete" >> assembly_node

    # 错误处理：任何节点返回"error"都结束流程
    # pocketflow会自动处理没有后续节点的情况

    # 创建带tracing的异步子流程
    subflow = TracedKeywordResearchFlow(start=search_node)

    return subflow
