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
        准备阶段：从参数获取URL和解析配置
        
        Args:
            shared: 共享状态对象
            
        Returns:
            准备结果字典
        """
        try:
            # 从节点参数获取URL和配置
            url = self.params.get("url", "")
            extraction_type = self.params.get("extraction_type", "full")
            target_selectors = self.params.get("target_selectors", [])
            max_content_length = self.params.get("max_content_length", self.max_content_length)

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

                # 从Markdown内容中提取结构化信息
                extracted_sections = self._extract_sections_from_markdown(content)

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
                    "extracted_sections": extracted_sections,
                    "processing_status": "success",
                    "processing_time": round(processing_time * 1000),
                    "content_length": len(content)
                }
            else:
                # 使用模拟结果
                return self._generate_mock_result(url, max_content_length)
            
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
        执行失败时的降级处理
        
        Args:
            prep_res: 准备阶段结果
            exc: 异常对象
            
        Returns:
            降级结果
        """
        url = prep_res.get("url", "")
        
        return {
            "url": url,
            "title": "解析失败",
            "content": f"无法解析URL内容: {str(exc)}",
            "metadata": {
                "author": "",
                "publish_date": "",
                "tags": [],
                "description": ""
            },
            "extracted_sections": {
                "headings": [],
                "key_points": [],
                "code_blocks": []
            },
            "processing_status": "failed",
            "processing_time": 0,
            "content_length": 0,
            "fallback_reason": str(exc)
        }
    
    def _generate_mock_result(self, url: str, max_content_length: int) -> Dict[str, Any]:
        """生成模拟URL解析结果"""
        mock_content = f"这是来自 {url} 的模拟内容。由于API未配置，无法获取真实内容。"

        return {
            "url": url,
            "title": f"模拟页面标题 - {url}",
            "content": mock_content,
            "metadata": {
                "author": "",
                "publish_date": "",
                "tags": [],
                "description": "模拟页面描述"
            },
            "extracted_sections": {
                "headings": ["模拟标题1", "模拟标题2"],
                "key_points": ["模拟要点1", "模拟要点2"],
                "code_blocks": []
            },
            "processing_status": "mock",
            "processing_time": 100,
            "content_length": len(mock_content)
        }

    def _extract_sections_from_markdown(self, markdown_content: str) -> Dict[str, List[str]]:
        """从Markdown内容中提取结构化信息"""
        sections = {
            "headings": [],
            "key_points": [],
            "code_blocks": []
        }

        lines = markdown_content.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 提取标题（以#开头）
            if line.startswith('#'):
                heading = line.lstrip('#').strip()
                if heading:
                    sections["headings"].append(heading)

            # 提取列表项（以-或*开头）
            elif line.startswith(('-', '*', '+')):
                point = line[1:].strip()
                if point and len(point) < 200:
                    sections["key_points"].append(point)

            # 提取代码块（以```包围）
            elif line.startswith('```') and len(line) > 3:
                code = line[3:].strip()
                if code and len(code) < 500:
                    sections["code_blocks"].append(code)

        # 限制数量
        sections["headings"] = sections["headings"][:10]
        sections["key_points"] = sections["key_points"][:20]
        sections["code_blocks"] = sections["code_blocks"][:5]

        return sections
