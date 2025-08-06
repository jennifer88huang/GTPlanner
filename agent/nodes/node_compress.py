"""
上下文压缩节点 (Node_Compress)

压缩长文本内容，保留关键信息。
完全基于LLM进行智能文本压缩和关键信息提取。

功能描述：
- 文本分段和结构分析
- 重要性评分计算
- 关键信息提取
- 内容重组和压缩
- 质量评估和优化
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


class NodeCompress(Node):
    """上下文压缩节点 - 完全基于LLM进行智能压缩"""
    
    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化上下文压缩节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
    
    def prep(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从pocketflow字典共享变量获取压缩配置

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 从pocketflow字典共享变量获取压缩配置
            content = shared.get("content", "")
            compression_ratio = shared.get("compression_ratio", 0.3)
            focus_keywords = shared.get("focus_keywords", [])
            preserve_structure = shared.get("preserve_structure", True)
            output_format = shared.get("output_format", "summary")
            
            # 如果没有提供内容，从共享状态中获取
            if not content:
                content = self._extract_content_from_shared_state(shared)
            
            # 验证输入
            if not content:
                return {
                    "error": "No content provided for compression",
                    "content": "",
                    "compression_ratio": compression_ratio,
                    "focus_keywords": focus_keywords,
                    "preserve_structure": preserve_structure,
                    "output_format": output_format
                }
            
            # 验证压缩比例
            if not (0.1 <= compression_ratio <= 0.8):
                compression_ratio = 0.3  # 默认值
            
            return {
                "content": content,
                "compression_ratio": compression_ratio,
                "focus_keywords": focus_keywords,
                "preserve_structure": preserve_structure,
                "output_format": output_format,
                "original_length": len(content)
            }
            
        except Exception as e:
            return {
                "error": f"Compression preparation failed: {str(e)}",
                "content": "",
                "compression_ratio": 0.3,
                "focus_keywords": [],
                "preserve_structure": True,
                "output_format": "summary"
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：使用LLM执行内容压缩
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        content = prep_res["content"]
        compression_ratio = prep_res["compression_ratio"]
        focus_keywords = prep_res["focus_keywords"]
        preserve_structure = prep_res["preserve_structure"]
        output_format = prep_res["output_format"]
        original_length = prep_res["original_length"]
        
        if not content.strip():
            raise ValueError("Empty content")
        
        try:
            start_time = time.time()
            
            # 使用LLM进行内容压缩
            compression_result = asyncio.run(self._compress_with_llm(
                content, compression_ratio, focus_keywords, preserve_structure, output_format
            ))
            
            processing_time = time.time() - start_time
            compressed_content = compression_result.get("compressed_content", "")
            compressed_length = len(compressed_content)
            
            # 计算实际压缩比
            actual_compression_ratio = compressed_length / original_length if original_length > 0 else 0
            
            return {
                "compressed_content": compressed_content,
                "key_points": compression_result.get("key_points", []),
                "preserved_sections": compression_result.get("preserved_sections", []),
                "compression_stats": {
                    "original_length": original_length,
                    "compressed_length": compressed_length,
                    "compression_ratio": actual_compression_ratio,
                    "information_density": compression_result.get("information_density", 0.5)
                },
                "processing_time": round(processing_time * 1000),  # 转换为毫秒
                "compression_method": "llm_based"
            }
            
        except Exception as e:
            raise RuntimeError(f"Content compression failed: {str(e)}")
    
    def post(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将压缩结果存储到共享状态
        
        Args:
            shared: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared.record_error(Exception(exec_res["error"]), "NodeCompress.exec")
                return "error"
            
            # 将压缩结果添加到研究发现中
            if not hasattr(shared.research_findings, 'compressed_contents'):
                shared.research_findings.compressed_contents = []
            
            # 创建压缩内容记录
            compression_record = {
                "compressed_content": exec_res["compressed_content"],
                "key_points": exec_res["key_points"],
                "preserved_sections": exec_res["preserved_sections"],
                "compression_stats": exec_res["compression_stats"],
                "processing_time": exec_res["processing_time"],
                "compression_method": exec_res["compression_method"],
                "compressed_at": time.time(),
                "original_content_preview": prep_res["content"][:200] + "..." if len(prep_res["content"]) > 200 else prep_res["content"]
            }
            
            shared.research_findings.compressed_contents.append(compression_record)
            
            # 更新研究元数据
            shared.research_findings.research_metadata.update({
                "last_compression_time": time.time(),
                "total_compressions": len(shared.research_findings.compressed_contents),
                "compression_ratio_achieved": exec_res["compression_stats"]["compression_ratio"]
            })
            
            # 添加系统消息记录压缩结果
            shared.add_system_message(
                f"内容压缩完成，压缩比: {exec_res['compression_stats']['compression_ratio']:.2f}",
                agent_source="NodeCompress",
                original_length=exec_res["compression_stats"]["original_length"],
                compressed_length=exec_res["compression_stats"]["compressed_length"],
                processing_time_ms=exec_res["processing_time"]
            )
            
            return "success"
            
        except Exception as e:
            shared.record_error(e, "NodeCompress.post")
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
        content = prep_res.get("content", "")
        original_length = len(content)
        
        # 简单的截断压缩作为降级
        target_length = int(original_length * prep_res.get("compression_ratio", 0.3))
        compressed_content = content[:target_length] + "..." if len(content) > target_length else content
        
        return {
            "compressed_content": compressed_content,
            "key_points": ["压缩失败，使用简单截断"],
            "preserved_sections": [],
            "compression_stats": {
                "original_length": original_length,
                "compressed_length": len(compressed_content),
                "compression_ratio": len(compressed_content) / original_length if original_length > 0 else 0,
                "information_density": 0.1
            },
            "processing_time": 0,
            "compression_method": "fallback_truncation",
            "fallback_reason": str(exc)
        }
    
    def _extract_content_from_shared_state(self, shared) -> str:
        """从pocketflow字典共享变量中提取需要压缩的内容"""
        content_parts = []

        # 从研究发现中提取内容
        research_findings = shared.get("research_findings", [])
        if isinstance(research_findings, list):
            for finding in research_findings[:3]:  # 最多3个研究结果
                if isinstance(finding, dict):
                    title = finding.get("title", "")
                    content = finding.get("content", "")
                    if title and content:
                        content_parts.append(f"标题: {title}\n内容: {content[:500]}...")

        # 从URL内容中提取
        url_content = shared.get("url_content", "")
        if url_content:
            content_parts.append(f"网页内容: {url_content[:1000]}...")

        # 从召回文档中提取
        recalled_documents = shared.get("recalled_documents", [])
        for doc in recalled_documents[:2]:  # 最多2个召回文档
            if isinstance(doc, dict):
                title = doc.get("title", "")
                content = doc.get("content", "")
                if title and content:
                    content_parts.append(f"文档: {title}\n内容: {content[:500]}...")

        return "\n\n".join(content_parts) if content_parts else ""
    
    async def _compress_with_llm(self, content: str, compression_ratio: float, 
                                focus_keywords: List[str], preserve_structure: bool, 
                                output_format: str) -> Dict[str, Any]:
        """使用LLM进行内容压缩"""
        
        target_length = int(len(content) * compression_ratio)
        keywords_text = ", ".join(focus_keywords) if focus_keywords else "无特定关键词"
        
        prompt = f"""
请对以下内容进行智能压缩，保留最重要的信息。

原始内容：
{content}

压缩要求：
- 目标压缩比例：{compression_ratio} (目标长度约{target_length}字符)
- 重点关键词：{keywords_text}
- 保留结构：{preserve_structure}
- 输出格式：{output_format}

请以JSON格式返回压缩结果：
{{
    "compressed_content": "压缩后的内容，保留核心信息和关键细节",
    "key_points": ["关键点1", "关键点2", "关键点3"],
    "preserved_sections": ["保留的重要段落1", "保留的重要段落2"],
    "information_density": 0.8
}}

请确保：
1. 压缩后的内容保留原文的核心信息
2. 如果有重点关键词，确保相关内容被优先保留
3. 保持逻辑连贯性和可读性
4. 提取3-5个最重要的关键点
5. 信息密度评分应该反映压缩质量（0-1之间）
"""
        
        try:
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            # LLM调用失败，直接抛出异常
            raise e
