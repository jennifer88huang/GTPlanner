"""
URL解析节点 (Node_URL)

解析网页内容，提取有用信息。
基于架构文档中定义的输入输出规格实现。

功能描述：
- URL有效性验证
- 网页内容抓取
- HTML解析和清理
- 文本提取和结构化
- 元数据提取和验证
"""

import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse
from pocketflow import Node
from ..utils.URL_to_Markdown import JinaWebClient


class NodeURL(Node):
    """URL解析节点"""
    
    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化URL解析节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)

        # 初始化Jina Web客户端
        try:
            self.web_client = JinaWebClient()
            self.client_available = True
        except ValueError:
            self.web_client = None
            self.client_available = False
            print("⚠️ URL解析API未配置，将使用模拟结果")

        # 配置
        self.max_content_length = 10000  # 默认最大内容长度
    
    def prep(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从pocketflow字典共享变量获取URL和解析配置

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 从pocketflow字典共享变量获取URL和配置
            url = shared.get("url", "")
            extraction_type = shared.get("extraction_type", "full")
            target_selectors = shared.get("target_selectors", [])
            max_content_length = shared.get("max_content_length", self.max_content_length)

            # 如果没有URL参数，尝试从共享变量中获取（子流程模式）
            if not url and isinstance(shared, dict):
                first_search_result = shared.get("first_search_result", {})
                url = first_search_result.get("url", "")

            # 验证URL
            if not url:
                return {
                    "error": "No URL provided",
                    "url": "",
                    "extraction_type": extraction_type,
                    "target_selectors": target_selectors,
                    "max_content_length": max_content_length
                }
            
            # URL格式验证
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {
                    "error": f"Invalid URL format: {url}",
                    "url": url,
                    "extraction_type": extraction_type,
                    "target_selectors": target_selectors,
                    "max_content_length": max_content_length
                }
            
            return {
                "url": url,
                "extraction_type": extraction_type,
                "target_selectors": target_selectors,
                "max_content_length": max_content_length,
                "parsed_url": parsed_url
            }
            
        except Exception as e:
            return {
                "error": f"URL preparation failed: {str(e)}",
                "url": "",
                "extraction_type": "full",
                "target_selectors": [],
                "max_content_length": self.max_content_length
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：执行URL解析
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        url = prep_res["url"]
        extraction_type = prep_res["extraction_type"]
        target_selectors = prep_res["target_selectors"]
        max_content_length = prep_res["max_content_length"]
        
        try:
            start_time = time.time()

            if self.client_available and self.web_client:
                # 使用Jina Web API
                page_info = self.web_client.get_page_info(url)

                # 处理内容长度限制
                content = page_info.get("content", "")
                if len(content) > max_content_length:
                    content = content[:max_content_length] + "..."

                # 构建元数据
                metadata = {
                    "author": "",
                    "publish_date": "",
                    "tags": [],
                    "description": page_info.get("description", "")
                }

                processing_time = time.time() - start_time

                return {
                    "url": url,
                    "title": page_info.get("title", "无标题"),
                    "content": content,
                    "metadata": metadata,
                    "processing_status": "success",
                    "processing_time": round(processing_time * 1000),
                    "content_length": len(content)
                }
            else:
                # API未配置，返回错误
                raise RuntimeError(f"Web API not configured, cannot parse URL: {url}")
            
        except Exception as e:
            raise RuntimeError(f"URL parsing failed: {str(e)}")
    
    def post(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将解析结果存储到共享状态
        
        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                if hasattr(shared, 'record_error'):
                    shared.record_error(Exception(exec_res["error"]), "NodeURL.exec")
                return "error"

            # 检查是否是子流程的共享变量（字典类型）
            if isinstance(shared, dict):
                # 子流程模式：保存URL内容到共享变量
                shared["url_content"] = exec_res["content"]
                shared["url_title"] = exec_res["title"]
                shared["url_metadata"] = exec_res.get("metadata", {})
                return "success"

            # 主流程模式：保存到研究发现
            if not hasattr(shared.research_findings, 'url_contents'):
                shared.research_findings.url_contents = []

            # 创建内容记录
            content_record = {
                "url": exec_res["url"],
                "title": exec_res["title"],
                "content": exec_res["content"],
                "metadata": exec_res["metadata"],
                "extracted_sections": exec_res["extracted_sections"],
                "processing_status": exec_res["processing_status"],
                "processing_time": exec_res["processing_time"],
                "extracted_at": time.time()
            }

            shared.research_findings.url_contents.append(content_record)
            
            # 更新研究元数据
            shared.research_findings.research_metadata.update({
                "last_url_extraction_time": time.time(),
                "total_url_extractions": len(shared.research_findings.url_contents)
            })

            # 添加系统消息记录解析结果
            shared.add_system_message(
                f"URL解析完成: {exec_res['title'][:50]}...",
                agent_source="NodeURL",
                url=exec_res["url"],
                content_length=exec_res["content_length"],
                processing_time_ms=exec_res["processing_time"]
            )

            return "success"

        except Exception as e:
            if hasattr(shared, 'record_error'):
                shared.record_error(e, "NodeURL.post")
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
        url = prep_res.get("url", "")

        return {
            "error": f"URL parsing failed for {url}: {str(exc)}",
            "url": url,
            "processing_status": "failed"
        }
    



