"""
搜索引擎节点 (Node_Search)

基于关键词进行网络搜索，返回相关结果。
基于架构文档中定义的输入输出规格实现。

功能描述：
- 关键词优化和组合
- 多搜索引擎API调用
- 结果去重和排序
- 相关性评分计算
- 结果格式标准化
"""

import time
from typing import Dict, List, Any, Optional
from pocketflow import AsyncNode
from ..utils.search import JinaSearchClient


class NodeSearch(AsyncNode):
    """搜索引擎节点"""
    
    def __init__(self, max_retries: int = 3, wait: float = 2.0):
        """
        初始化搜索引擎节点
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        self.name = "NodeSearch"
        
        # 初始化搜索客户端
        try:
            self.search_client = JinaSearchClient()
            self.search_available = True
        except ValueError:
            self.search_client = None
            self.search_available = False
            print("⚠️ 搜索API未配置")

        # 搜索配置
        self.default_max_results = 10
        self.default_language = "zh-CN"
        self.timeout = 30

        # 相关性评分权重
        self.title_weight = 0.4
        self.snippet_weight = 0.3
        self.url_weight = 0.2
        self.source_weight = 0.1
    
    async def prep_async(self, shared) -> Dict[str, Any]:
        """
        准备阶段：从pocketflow字典共享变量获取搜索关键词

        Args:
            shared: pocketflow字典共享变量

        Returns:
            准备结果字典
        """
        try:
            # 🔧 支持单个关键词输入
            current_keyword = shared.get("current_keyword")
            search_keywords = shared.get("search_keywords", [])
            search_type = shared.get("search_type", "web")
            max_results = shared.get("max_results", self.default_max_results)
            language = shared.get("language", self.default_language)

            # 优先使用单个关键词，如果没有则使用关键词列表
            if current_keyword:
                search_keywords = [current_keyword]
            elif not search_keywords:
                search_keywords = self._extract_keywords_from_shared_state(shared)

            # 验证输入
            if not search_keywords:
                return self._create_error_result("No search keywords provided", search_type)
            
            # 优化关键词
            optimized_keywords = self._optimize_keywords(search_keywords)
            
            return {
                "search_keywords": optimized_keywords,
                "search_type": search_type,
                "max_results": max_results,
                "language": language,
                "original_keywords": search_keywords,
                "keyword_count": len(optimized_keywords)
            }
            
        except Exception as e:
            return self._create_error_result(f"Search preparation failed: {str(e)}")
    
    async def exec_async(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：执行搜索操作
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        search_keywords = prep_res["search_keywords"]
        max_results = prep_res["max_results"]
        
        if not search_keywords:
            raise ValueError("Empty search keywords")
        
        try:
            start_time = time.time()
            
            # 执行搜索
            all_results = []
            
            for keyword in search_keywords:
                try:
                    if self.search_available and self.search_client:
                        # 使用真实搜索API - 异步调用
                        results = await self.search_client.search_simple(keyword, count=max_results)

                        # 转换为标准格式
                        formatted_results = []
                        for i, result in enumerate(results):
                            formatted_result = {
                                "title": result.get("title", ""),
                                "url": result.get("url", ""),
                                "snippet": result.get("description", ""),
                                "search_keyword": keyword,
                                "rank": i + 1,
                                "source_type": self._classify_source_type(result.get("url", "")),
                                "content": result.get("content", "")
                            }
                            formatted_result["relevance_score"] = self._calculate_relevance_score(
                                formatted_result, keyword
                            )
                            formatted_results.append(formatted_result)

                        all_results.extend(formatted_results)
                    else:
                        # 搜索API不可用，跳过此关键词
                        print(f"⚠️ 搜索API不可用，跳过关键词: {keyword}")
                        continue

                    # 避免请求过于频繁
                    time.sleep(0.5)

                except Exception as e:
                    # 单个关键词搜索失败不影响其他关键词
                    print(f"❌ 搜索失败，关键词 '{keyword}': {str(e)}")
                    continue
            
            # 去重和排序
            deduplicated_results = self._deduplicate_results(all_results)
            sorted_results = self._sort_results(deduplicated_results)
            
            # 限制结果数量
            final_results = sorted_results[:max_results]
            
            search_time = time.time() - start_time
            
            return {
                "search_results": final_results,
                "total_found": len(final_results),
                "search_time": round(search_time * 1000),  # 转换为毫秒
                "keywords_processed": len(search_keywords),
                "deduplication_stats": {
                    "original_count": len(all_results),
                    "deduplicated_count": len(deduplicated_results),
                    "final_count": len(final_results)
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Search execution failed: {str(e)}")
    
    async def post_async(self, shared, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：将搜索结果存储到共享状态

        Args:
            shared: 共享状态字典
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果

        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                # 记录错误到shared字典
                if "errors" not in shared:
                    shared["errors"] = []
                shared["errors"].append({
                    "source": "NodeSearch.exec",
                    "error": exec_res["error"],
                    "timestamp": prep_res.get("timestamp", "")
                })
                return "error"

            search_results = exec_res["search_results"]

            # 统一使用字典模式存储搜索结果
            if search_results:
                shared["first_search_result"] = search_results[0]
                shared["all_search_results"] = search_results




            print(f"✅ 搜索完成，找到 {len(search_results)} 个结果")
            return "search_complete"

        except Exception as e:
            print(f"❌ NodeSearch post处理失败: {e}")
            # 记录错误到shared字典
            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append({
                "source": "NodeSearch.post",
                "error": str(e),
                "timestamp": prep_res.get("timestamp", "")
            })
            return "error"
    



    
    def _extract_keywords_from_shared_state(self, shared) -> List[str]:
        """从共享状态中提取搜索关键词"""
        # 直接从shared字典获取搜索关键词
        search_keywords = shared.get("search_keywords", [])

        # 去重并返回
        return list(set(search_keywords))[:5]  # 最多返回5个关键词
    

    


    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重搜索结果"""
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduplicated.append(result)
        
        return deduplicated
    
    def _sort_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """按相关性评分排序结果"""
        return sorted(results, key=lambda x: x.get("relevance_score", 0), reverse=True)
    

    

