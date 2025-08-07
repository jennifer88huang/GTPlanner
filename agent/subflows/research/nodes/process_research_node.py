"""
研究处理节点
负责管理研究处理状态，协调Research Agent的执行
"""

import json
import time
from pocketflow import AsyncNode
from ..flows.research_flow import ResearchFlow
from agent.shared_migration import field_validation_decorator


class ProcessResearch(AsyncNode):
    """研究处理节点 - 管理研究处理状态"""

    def __init__(self):
        super().__init__()
        self.subflow = ResearchFlow()


    
    @field_validation_decorator(validation_enabled=True, strict_mode=False)



    
    async def prep_async(self, shared):
        """准备研究处理 - 使用pocketflow字典共享变量"""
        # 从共享变量中提取研究关键词
        research_keywords = []

        # 从用户意图中获取关键词
        user_intent = shared.get("user_intent", {})
        extracted_keywords = user_intent.get("extracted_keywords", [])
        if extracted_keywords:
            research_keywords.extend(extracted_keywords[:3])

        # 从结构化需求中获取关键词
        structured_requirements = shared.get("structured_requirements", {})
        if structured_requirements:
            # 从项目概览获取标题
            project_overview = structured_requirements.get("project_overview", {})
            project_title = project_overview.get("title", "")
            if project_title and project_title not in research_keywords:
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

        # 去重并限制数量
        research_keywords = list(set(research_keywords))[:5]

        if not research_keywords:
            # 如果无法提取关键词，使用默认关键词
            research_keywords = ["项目开发", "技术选型", "最佳实践"]
            print("⚠️ 无法从共享状态提取关键词，使用默认关键词")

        # 获取用户需求
        requirements = {}
        if structured_requirements:
            project_overview = structured_requirements.get("project_overview", {})
            requirements = {
                "project_title": project_overview.get("title", ""),
                "project_description": project_overview.get("description", ""),
                "objectives": project_overview.get("objectives", [])
            }

        return {
            "research_keywords": research_keywords,
            "requirements": requirements,
            "total_keywords": len(research_keywords)
        }
    
    @field_validation_decorator(validation_enabled=True, strict_mode=False)

    
    async def exec_async(self, data):
        """执行研究处理 - 按照架构文档实现"""
        research_keywords = data["research_keywords"]
        requirements = data["requirements"]
        total_keywords = data["total_keywords"]
        
        print(f"🔄 开始研究处理，关键词: {research_keywords}")
        
        try:
            # 构建分析需求描述
            analysis_requirements = self._build_analysis_requirements(requirements)

            # 使用子流程处理研究关键词（按照架构文档的流程）
            result = self.subflow.process_research_keywords(research_keywords, analysis_requirements)

            if not result.get("success"):
                raise Exception(f"研究子流程处理失败: {result.get('error', '未知错误')}")

            # 提取处理结果
            research_report = result.get("research_report", [])
            aggregated_summary = result.get("aggregated_summary", {})
            successful_keywords = result.get("successful_keywords", 0)

            print(f"✅ 研究处理完成，成功处理 {successful_keywords}/{total_keywords} 个关键词")

            return {
                "keywords": research_keywords,
                "result": result,
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
    
    @field_validation_decorator(validation_enabled=True, strict_mode=False)

    
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
