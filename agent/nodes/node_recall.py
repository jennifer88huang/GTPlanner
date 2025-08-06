"""
文档召回节点 (Node_Recall)

从知识库中召回相关文档和信息。
完全基于LLM进行文档召回和相关性分析。

功能描述：
- 查询文本向量化
- 向量相似度计算
- 结果排序和过滤
- 内容摘要生成
- 相关性验证
"""

import time
import asyncio
import sys
import os
from typing import Dict, List, Any, Optional
from pocketflow import Node

# 添加utils路径以导入call_llm
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))
from call_llm import call_llm_async


class NodeRecall(Node):
    """文档召回节点 - 完全基于LLM进行知识召回"""
    
    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化文档召回节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
    
    def prep(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从pocketflow字典共享变量获取查询信息

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 从pocketflow字典共享变量获取查询配置
            query = shared.get("query", "")
            knowledge_base = shared.get("knowledge_base", "general")
            similarity_threshold = shared.get("similarity_threshold", 0.7)
            max_results = shared.get("max_results", 5)
            result_type = shared.get("result_type", "documents")
            
            # 如果没有提供查询，从共享状态中构建查询
            if not query:
                query = self._build_query_from_shared_state(shared)
            
            # 验证输入
            if not query:
                return {
                    "error": "No query provided and cannot build from shared state",
                    "query": "",
                    "knowledge_base": knowledge_base,
                    "similarity_threshold": similarity_threshold,
                    "max_results": max_results,
                    "result_type": result_type
                }
            
            return {
                "query": query,
                "knowledge_base": knowledge_base,
                "similarity_threshold": similarity_threshold,
                "max_results": max_results,
                "result_type": result_type,
                "query_length": len(query)
            }
            
        except Exception as e:
            return {
                "error": f"Recall preparation failed: {str(e)}",
                "query": "",
                "knowledge_base": "general",
                "similarity_threshold": 0.7,
                "max_results": 5,
                "result_type": "documents"
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：使用LLM执行文档召回
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        query = prep_res["query"]
        knowledge_base = prep_res["knowledge_base"]
        max_results = prep_res["max_results"]
        similarity_threshold = prep_res["similarity_threshold"]
        
        if not query.strip():
            raise ValueError("Empty query")
        
        try:
            start_time = time.time()
            
            # 使用LLM进行知识召回
            recall_result = asyncio.run(self._recall_with_llm(
                query, knowledge_base, max_results, similarity_threshold
            ))
            
            recall_time = time.time() - start_time
            
            return {
                "recalled_documents": recall_result.get("recalled_documents", []),
                "total_matches": recall_result.get("total_matches", 0),
                "recall_time": round(recall_time * 1000),  # 转换为毫秒
                "knowledge_base_used": knowledge_base,
                "query_processed": query,
                "similarity_threshold_used": similarity_threshold
            }
            
        except Exception as e:
            raise RuntimeError(f"Document recall failed: {str(e)}")
    
    def post(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将召回结果存储到共享状态
        
        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared.record_error(Exception(exec_res["error"]), "NodeRecall.exec")
                return "error"
            
            recalled_documents = exec_res["recalled_documents"]
            
            # 将召回结果添加到研究发现中
            if not hasattr(shared.research_findings, 'recalled_documents'):
                shared.research_findings.recalled_documents = []
            
            # 转换召回结果为研究源格式
            for doc in recalled_documents:
                research_source = {
                    "source_id": doc.get("document_id", ""),
                    "title": doc.get("title", ""),
                    "url": "",  # 知识库文档通常没有URL
                    "content_summary": doc.get("content", ""),
                    "relevance_score": doc.get("similarity_score", 0.0),
                    "credibility_score": 0.8,  # 知识库文档通常可信度较高
                    "extracted_insights": [],
                    "key_data_points": [],
                    "recall_metadata": {
                        "knowledge_base": exec_res.get("knowledge_base_used", ""),
                        "query": exec_res.get("query_processed", ""),
                        "recall_time": exec_res.get("recall_time", 0)
                    }
                }
                shared.research_findings.recalled_documents.append(research_source)
            
            # 更新研究元数据
            shared.research_findings.research_metadata.update({
                "last_recall_time": time.time(),
                "total_recalled_documents": len(shared.research_findings.recalled_documents),
                "recall_query": prep_res["query"]
            })
            
            # 添加系统消息记录召回结果
            shared.add_system_message(
                f"文档召回完成，找到 {exec_res['total_matches']} 个相关文档",
                agent_source="NodeRecall",
                query=prep_res["query"],
                documents_count=exec_res["total_matches"],
                recall_time_ms=exec_res["recall_time"]
            )
            
            return "success"
            
        except Exception as e:
            shared.record_error(e, "NodeRecall.post")
            return "error"
    
    def exec_fallback(self, prep_res: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        执行失败时的降级处理 - 直接返回错误

        Args:
            prep_res: 准备阶段结果
            exc: 异常对象

        Returns:
            错误信息
        """
        return {
            "error": f"Document recall failed: {str(exc)}",
            "recalled_documents": [],
            "total_matches": 0
        }
    
    def _build_query_from_shared_state(self, shared) -> str:
        """从pocketflow字典共享变量构建查询"""
        query_parts = []

        # 从用户意图中获取关键词
        user_intent = shared.get("user_intent", {})
        extracted_keywords = user_intent.get("extracted_keywords", [])
        if extracted_keywords:
            query_parts.extend(extracted_keywords[:3])  # 最多3个关键词

        # 从项目标题中获取信息
        structured_requirements = shared.get("structured_requirements", {})
        project_overview = structured_requirements.get("project_overview", {})
        title = project_overview.get("title", "")
        if title:
            query_parts.append(title)

        # 从用户消息中获取最新内容
        dialogue_history = shared.get("dialogue_history", {})
        messages = dialogue_history.get("messages", [])
        if messages:
            # 找到最后一条用户消息
            for message in reversed(messages):
                if isinstance(message, dict) and message.get("role") == "user":
                    content = message.get("content", "")
                    if content:
                        # 取前50个字符作为查询的一部分
                        query_parts.append(content[:50])
                        break

        return " ".join(query_parts) if query_parts else ""
    
    async def _recall_with_llm(self, query: str, knowledge_base: str,
                              max_results: int, similarity_threshold: float) -> Dict[str, Any]:
        """使用LLM进行文档召回 - 需要真实的知识库实现"""

        # 这里应该连接真实的知识库系统，而不是生成mock数据
        # 目前抛出异常，表明功能未实现
        raise NotImplementedError(
            f"Document recall not implemented. "
            f"Need real knowledge base connection for query: {query}"
        )
