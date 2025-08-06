"""
Research Agent主流程

按照架构文档实现：并行批处理版本
对每个关键词执行完整的子流程，最后聚合结果
"""

import concurrent.futures
from .keyword_research_flow import create_keyword_research_subflow
from ..utils.research_aggregator import ResearchAggregator


class ResearchFlow:
    """研究调研子流程包装器"""
    
    def __init__(self):
        self.subflow = create_keyword_research_subflow()
        self.aggregator = ResearchAggregator()
    
    def process_research_keywords(self, search_keywords, analysis_requirements):
        """
        使用并发批处理处理研究关键词

        对每个关键词并发执行完整的子流程：搜索 → URL解析 → LLM分析 → 结果组装

        Args:
            search_keywords: 搜索关键词列表
            analysis_requirements: 分析需求描述

        Returns:
            research_report: 聚合后的研究报告列表
        """
        print(f"🔄 开始并发研究处理，关键词: {search_keywords}")

        research_report = []

        try:
            # 使用线程池并发处理关键词
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(search_keywords), 3)) as executor:
                # 提交所有关键词处理任务
                future_to_keyword = {
                    executor.submit(self._process_single_keyword, keyword, analysis_requirements): keyword
                    for keyword in search_keywords
                }

                # 收集结果
                for future in concurrent.futures.as_completed(future_to_keyword):
                    keyword = future_to_keyword[future]
                    try:
                        keyword_result = future.result()
                        if keyword_result and keyword_result.get("success"):
                            research_report.append(keyword_result["keyword_report"])
                            print(f"✅ 完成关键词: {keyword}")
                        else:
                            print(f"❌ 关键词处理失败: {keyword}")
                    except Exception as e:
                        print(f"❌ 关键词 {keyword} 处理出错: {e}")

            # 3. 结果聚合
            aggregated_report = self.aggregator.aggregate_research_results(research_report)

            print(f"✅ 并发研究处理完成，生成 {len(research_report)} 个关键词报告")

            return {
                "success": True,
                "research_report": research_report,
                "aggregated_summary": aggregated_report,
                "total_keywords": len(search_keywords),
                "successful_keywords": len(research_report)
            }

        except Exception as e:
            print(f"❌ 并发研究处理失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "research_report": research_report,
                "total_keywords": len(search_keywords),
                "successful_keywords": len(research_report)
            }

    def _process_single_keyword(self, keyword, analysis_requirements):
        """处理单个关键词"""
        print(f"🔍 处理关键词: {keyword}")

        # 为每个关键词创建独立的子流程实例
        subflow = create_keyword_research_subflow()

        # 准备子流程的共享变量
        subflow_shared = {
            "current_keyword": keyword,
            "analysis_requirements": analysis_requirements,
            "search_keywords": [keyword],  # 传递给搜索节点
            "max_search_results": 5,

            # 用于存储流程中的数据
            "first_search_result": {},
            "url_content": "",
            "llm_analysis": {},
            "keyword_report": {}
        }

        try:
            # 执行子流程
            flow_result = subflow.run(subflow_shared)

            # 检查flow_result和共享变量中的结果
            keyword_report = subflow_shared.get("keyword_report", {})

            # 验证流程是否成功执行
            if flow_result and keyword_report:
                return {
                    "success": True,
                    "keyword_report": keyword_report,
                    "flow_result": flow_result
                }
            else:
                return {
                    "success": False,
                    "error": f"Flow execution failed or no report generated",
                    "flow_result": flow_result
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "flow_result": None
            }

    def run(self, shared: dict) -> bool:
        """
        运行研究调研流程（兼容ReAct系统）

        Args:
            shared: 共享状态字典

        Returns:
            bool: 执行是否成功
        """
        try:
            print("🔄 启动研究调研流程...")

            # 从共享状态获取结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            if not structured_requirements:
                print("❌ 缺少结构化需求数据")
                return False

            # 提取项目信息生成研究关键词
            project_overview = structured_requirements.get("project_overview", {})
            project_title = project_overview.get("title", "项目")
            project_description = project_overview.get("description", "")

            # 生成研究关键词
            search_keywords = [
                f"{project_title} 技术方案",
                f"{project_title} 架构设计",
                "最佳实践",
                "技术选型"
            ]

            # 分析需求
            analysis_requirements = f"针对{project_title}项目进行技术调研，项目描述：{project_description}"

            # 执行研究
            research_results = self.process_research_keywords(search_keywords, analysis_requirements)

            # 保存结果到共享状态
            shared["research_findings"] = {
                "topics": search_keywords,
                "results": research_results,
                "summary": f"完成了{len(search_keywords)}个主题的技术调研"
            }

            print("✅ 研究调研流程完成")
            return True

        except Exception as e:
            print(f"❌ 研究调研流程失败: {e}")
            shared["research_error"] = str(e)
            return False

    async def run_async(self, shared: dict) -> bool:
        """异步运行研究调研流程"""
        import asyncio
        import concurrent.futures

        # 在线程池中运行同步方法
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await asyncio.get_event_loop().run_in_executor(
                executor, self.run, shared
            )
        return result
