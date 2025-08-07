"""
关键词研究子流程

使用箭头函数编排单个关键词的完整研究流程：
搜索 → URL解析 → LLM分析 → 结果组装
"""

from pocketflow import AsyncFlow
from ....nodes.node_search import NodeSearch
from ....nodes.node_url import NodeURL
from ..nodes.llm_analysis_node import LLMAnalysisNode
from ..nodes.result_assembly_node import ResultAssemblyNode


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
    
    # 使用pocketflow的条件转换语法 - 基于demo最佳实践
    search_node - "success" >> url_node
    url_node - "success" >> llm_analysis_node
    llm_analysis_node - "success" >> assembly_node

    # 错误处理：任何节点返回"error"都结束流程
    # pocketflow会自动处理没有后续节点的情况

    # 创建异步子流程
    subflow = AsyncFlow(start=search_node)

    return subflow
