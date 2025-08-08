"""
研究处理节点
负责管理研究处理状态，协调Research Agent的执行
"""

import time
import json
from pocketflow import AsyncNode
from ..flows.research_flow import ResearchFlow
from agent.llm_utils import call_llm_async


class ProcessResearch(AsyncNode):
    """研究处理节点 - 管理研究处理状态"""

    def __init__(self):
        super().__init__()
        self.subflow = ResearchFlow()


    async def prep_async(self, shared):
        """准备研究处理 - 直接从共享变量提取主agent注入的关键词"""
        # 获取主agent通过Function Calling注入的研究关键词
        research_keywords = shared.get("research_keywords", [])
        focus_areas = shared.get("focus_areas", [])
        project_context = shared.get("project_context", "")

        # 获取结构化需求
        structured_requirements = shared.get("structured_requirements", {})

        # 获取用户需求信息
        requirements = {}
        if structured_requirements:
            project_overview = structured_requirements.get("project_overview", {})
            requirements = {
                "project_title": project_overview.get("title", ""),
                "project_description": project_overview.get("description", ""),
                "objectives": project_overview.get("objectives", [])
            }

        # 如果主agent没有提供关键词，使用回退方案
        if not research_keywords:
            print("⚠️ 主agent未提供研究关键词，使用回退方案")
            research_keywords = self._extract_keywords_from_requirements(structured_requirements)

        print(f"🔍 获取到研究关键词: {research_keywords}")
        print(f"🎯 关注点: {focus_areas}")
        print(f"📝 项目背景: {project_context}")

        return {
            "research_keywords": research_keywords,
            "focus_areas": focus_areas,
            "project_context": project_context,
            "requirements": requirements,
            "total_keywords": len(research_keywords)
        }
    async def exec_async(self, data):
        """执行研究处理 - 使用LLM直接分析关键词"""
        research_keywords = data["research_keywords"]
        focus_areas = data["focus_areas"]
        project_context = data["project_context"]
        requirements = data["requirements"]
        total_keywords = data["total_keywords"]

        print(f"🔄 开始研究处理，关键词: {research_keywords}")

        try:
            # 使用LLM直接进行关键词调研分析
            research_result = await self._execute_keyword_research_with_llm(
                research_keywords, focus_areas, project_context
            )

            if not research_result.get("success"):
                raise Exception(f"LLM研究分析失败: {research_result.get('error', '未知错误')}")

            # 提取处理结果
            research_findings = research_result.get("result", {})
            research_report = research_findings.get("results", [])
            aggregated_summary = research_findings.get("summary", {})
            successful_keywords = len(research_report)

            print(f"✅ 研究处理完成，成功处理 {successful_keywords}/{total_keywords} 个关键词")

            return {
                "keywords": research_keywords,
                "result": research_findings,
                "processing_success": True,
                "research_report": research_report,
                "aggregated_summary": aggregated_summary,
                "successful_keywords": successful_keywords,
                "total_keywords": total_keywords
            }

        except Exception as e:
            error_msg = f"研究处理失败: {str(e)}"
            print(f"[ERROR] {error_msg}")

            return {
                "keywords": research_keywords,
                "result": None,
                "processing_success": False,
                "error": error_msg,
                "research_report": [],
                "aggregated_summary": {},
                "successful_keywords": 0,
                "total_keywords": total_keywords
            }

    async def _execute_keyword_research_with_llm(self, keywords: list, focus_areas: list, project_context: str) -> dict:
        """使用LLM执行基于关键词的技术调研"""
        try:
            # 构建调研提示词
            focus_description = "、".join(focus_areas)
            keywords_text = "、".join(keywords)

            prompt = f"""
请基于以下关键词进行技术调研分析：

关键词：{keywords_text}
关注点：{focus_description}
项目背景：{project_context}

请针对每个关键词，从指定的关注点角度进行深入分析，并以JSON格式返回结果：

{{
    "research_summary": {{
        "total_keywords": {len(keywords)},
        "focus_areas": {focus_areas},
        "analysis_depth": "detailed"
    }},
    "keyword_analysis": [
        {{
            "keyword": "关键词1",
            "analysis": {{
                "技术选型": "相关技术选型建议",
                "性能优化": "性能优化要点",
                "最佳实践": "行业最佳实践",
                "架构设计": "架构设计考虑"
            }},
            "recommendations": ["建议1", "建议2"],
            "relevance_score": 0.9
        }}
    ],
    "cross_keyword_insights": [
        "跨关键词的综合洞察1",
        "跨关键词的综合洞察2"
    ],
    "implementation_roadmap": [
        "实施步骤1",
        "实施步骤2"
    ]
}}

要求：
1. 针对每个关键词，从所有关注点角度进行分析
2. 提供具体、可操作的建议
3. 识别关键词之间的关联和协同效应
4. 给出实施路线图建议
"""

            print("🔧 使用LLM进行关键词调研分析...")
            result = await call_llm_async(prompt, is_json=True)

            if isinstance(result, str):
                result = json.loads(result)

            print("✅ 关键词调研分析完成")

            # 格式化为标准的research_findings格式
            research_findings = {
                "topics": keywords,
                "results": result.get("keyword_analysis", []),
                "summary": {
                    "total_keywords": len(keywords),
                    "focus_areas": focus_areas,
                    "cross_insights": result.get("cross_keyword_insights", []),
                    "roadmap": result.get("implementation_roadmap", [])
                }
            }

            return {
                "success": True,
                "result": research_findings
            }

        except Exception as e:
            print(f"❌ 关键词调研失败: {e}")
            return {
                "success": False,
                "error": f"Keyword research failed: {str(e)}"
            }

    def _extract_keywords_from_requirements(self, structured_requirements: dict) -> list:
        """基于规则从结构化需求中提取关键词（回退方案）"""
        research_keywords = []

        if not structured_requirements:
            return ["项目开发", "技术选型", "最佳实践"]

        # 从项目概览获取标题
        project_overview = structured_requirements.get("project_overview", {})
        project_title = project_overview.get("title", "")
        if project_title:
            research_keywords.append(project_title)

        # 从核心功能获取关键词
        functional_requirements = structured_requirements.get("functional_requirements", {})
        core_features = functional_requirements.get("core_features", [])
        for feature in core_features[:2]:  # 限制数量
            if isinstance(feature, dict):
                feature_name = feature.get("name", "")
            elif isinstance(feature, str):
                feature_name = feature
            else:
                feature_name = str(feature) if feature else ""

            if feature_name and feature_name not in research_keywords:
                research_keywords.append(feature_name)

        # 添加通用技术关键词
        if project_title:
            research_keywords.extend([
                f"{project_title} 技术方案",
                f"{project_title} 架构设计",
                "最佳实践",
                "技术选型"
            ])

        # 去重并限制数量
        research_keywords = list(set(research_keywords))[:5]

        if not research_keywords:
            research_keywords = ["项目开发", "技术选型", "最佳实践"]

        print(f"🔄 使用规则提取关键词: {research_keywords}")
        return research_keywords

    async def post_async(self, shared, prep_res, exec_res):
        """保存研究结果并更新状态 - 使用pocketflow字典共享变量"""
        # 检查执行结果
        if "error" in exec_res:
            shared["research_error"] = exec_res["error"]
            shared["current_stage"] = "research_failed"
            return "error"

        keywords = exec_res.get("keywords", [])
        result = exec_res.get("result")
        success = exec_res.get("processing_success", False)

        # 从子流程结果中提取数据
        research_report = exec_res.get("research_report", [])
        aggregated_summary = exec_res.get("aggregated_summary", {})
        successful_keywords = exec_res.get("successful_keywords", 0)
        total_keywords = exec_res.get("total_keywords", 0)

        # 保存研究结果到共享变量
        if success and result:
            # 创建研究发现数据结构
            research_findings = {
                "research_report": research_report,
                "aggregated_summary": aggregated_summary,
                "research_metadata": {
                    "research_keywords": keywords,
                    "total_keywords": total_keywords,
                    "successful_keywords": successful_keywords,
                    "success_rate": successful_keywords / total_keywords if total_keywords > 0 else 0,
                    "research_completed_at": time.time(),
                    "research_success": True
                }
            }

            # 保存到共享变量
            shared["research_findings"] = research_findings

        # 更新处理阶段
        shared["current_stage"] = "research_completed"

        # 添加系统消息
        system_messages = shared.get("system_messages", [])
        system_messages.append({
            "message": f"研究调研完成，成功处理 {successful_keywords}/{total_keywords} 个关键词",
            "agent_source": "ProcessResearch",
            "timestamp": time.time(),
            "keywords": keywords,
            "successful_keywords": successful_keywords,
            "total_keywords": total_keywords,
            "success": success
        })
        shared["system_messages"] = system_messages

        # 更新元数据
        metadata = shared.get("metadata", {})
        processing_stages = metadata.get("processing_stages", [])
        if "research" not in processing_stages:
            processing_stages.append("research")
        metadata.update({
            "processing_stages": processing_stages,
            "last_updated": time.time(),
            "total_processing_time": metadata.get("total_processing_time", 0) + 50.0  # 估算处理时间
        })
        shared["metadata"] = metadata

        print(f"✅ 研究处理完成，生成了 {len(research_report)} 个关键词报告")

        # 返回下一步动作 - 基于pocketflow最佳实践
        if success and successful_keywords > 0:
            return "success"  # 成功完成，可以继续下一个节点
        else:
            return "failed"   # 处理失败，需要错误处理
    
    def _build_analysis_requirements(self, requirements):
        """构建分析需求描述"""
        analysis_parts = []
        
        if requirements.get("project_title"):
            analysis_parts.append(f"项目背景：{requirements['project_title']}")
        
        if requirements.get("project_description"):
            analysis_parts.append(f"项目描述：{requirements['project_description']}")
        
        if requirements.get("objectives"):
            objectives_text = "、".join(requirements["objectives"])
            analysis_parts.append(f"项目目标：{objectives_text}")
        
        # 默认分析需求
        analysis_parts.append("请重点关注：技术实现方案、最佳实践、相关工具和框架、潜在问题和解决方案")
        
        return "\n".join(analysis_parts)
