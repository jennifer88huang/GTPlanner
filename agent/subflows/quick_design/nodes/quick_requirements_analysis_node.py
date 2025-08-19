"""
Quick Requirements Analysis Node

复制 nodes.py 中 AsyncRequirementsAnalysisNode 的完整实现，
移除多语言支持功能，保持相同的数据处理逻辑和提示词模板。
"""

from typing import Dict, Any
from pocketflow import AsyncNode
from utils.openai_client import get_openai_client


class QuickRequirementsAnalysisNode(AsyncNode):
    """快速需求分析节点 - 复制 AsyncRequirementsAnalysisNode 的逻辑"""

    def __init__(self):
        super().__init__()
        self.name = "QuickRequirementsAnalysisNode"
        self.description = "快速分析需求，复制原有逻辑但移除多语言支持"

    async def prep_async(self, shared):
        """准备数据进行需求分析"""
        # 提取用户需求（与上游字段名保持一致）
        user_requirements = shared.get("user_requirements", "")
        
        # 提取项目规划
        short_planning = shared.get("short_planning", "")

        # 格式化推荐工具信息
        tools_info = self._format_tools_info(shared.get("recommended_tools", []))

        # 格式化技术调研结果
        research_summary = self._format_research_summary(shared.get("research_findings", {}))

        return {
            "user_requirements": user_requirements,
            "short_planning": short_planning,
            "tools_info": tools_info,
            "research_summary": research_summary,
        }

    async def exec_async(self, input_data):
        """使用LLM分析需求"""
        # 构建需求分析提示词，使用新的数据结构
        prompt = self._build_requirements_analysis_prompt(
            user_requirements=input_data["user_requirements"],
            short_planning=input_data["short_planning"],
            tools_info=input_data["tools_info"],
            research_summary=input_data["research_summary"]
        )

        # 调用LLM分析需求
        client = get_openai_client()
        response = await client.chat_completion(
            messages=[{"role": "user", "content": prompt}]
        )
        llm_response = response.choices[0].message.content if response.choices else ""

        return llm_response

    async def post_async(self, shared, prep_res, exec_res):
        """将分析的需求存储到共享存储中并生成文件"""
        try:
            # exec_res 是字符串类型的LLM响应，不是字典
            if not exec_res or not exec_res.strip():
                shared["quick_requirements_analysis_error"] = "需求分析结果为空"
                print(f"❌ 快速需求分析失败: 需求分析结果为空")
                return "error"

            # 保存需求分析结果
            requirements = exec_res
            shared["requirements"] = requirements
            # 存储语言为中文（默认）
            shared["language"] = "zh"

            # 使用简化文件工具生成需求分析文件
            from ....utils.simple_file_util import write_file_directly
            await write_file_directly("quick_requirements_analysis.md", requirements, shared)

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": __import__('time').time(),
                "stage": "quick_requirements_analysis",
                "status": "completed",
                "message": "快速需求分析完成"
            })

            print("✅ 快速需求分析完成")
            return "default"

        except Exception as e:
            shared["quick_requirements_analysis_post_error"] = str(e)
            print(f"❌ 快速需求分析后处理失败: {str(e)}")
            return "error"

    def _build_requirements_analysis_prompt(self, user_requirements: str,
                                          short_planning: str,
                                          tools_info: str,
                                          research_summary: str) -> str:
        """构建需求分析提示词，使用新的数据结构"""
        # 导入模板
        from ..utils.quick_design_templates import QuickDesignTemplates

        # 使用模板并填充数据
        template = QuickDesignTemplates.get_requirements_analysis_zh()
        prompt = template.format(
            user_requirements=user_requirements,
            short_planning=short_planning if short_planning else "无项目规划",
            tools_info=tools_info if tools_info else "无推荐工具",
            research_summary=research_summary if research_summary else "无技术调研结果"
        )

        return prompt

    def _format_tools_info(self, recommended_tools: list) -> str:
        """格式化推荐工具信息"""
        if not recommended_tools:
            return "无推荐工具"

        tools_list = []
        for tool in recommended_tools[:5]:  # 只取前5个
            name = tool.get('name', 'Unknown')
            description = tool.get('description', 'No description')
            tools_list.append(f"- {name}: {description}")

        return "\n".join(tools_list)

    def _format_research_summary(self, research_findings: dict) -> str:
        """格式化技术调研结果"""
        if not research_findings:
            return "无技术调研结果"

        if "research_summary" in research_findings:
            return research_findings["research_summary"]
        elif "key_findings" in research_findings:
            findings = research_findings["key_findings"]
            if isinstance(findings, list):
                return "关键技术发现：\n" + "\n".join(f"- {finding}" for finding in findings[:3])

        return "无技术调研结果"
