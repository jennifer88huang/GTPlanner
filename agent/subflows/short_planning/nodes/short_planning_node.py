"""
Short Planning Node

基于用户需求生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度。
"""

import time
import json
from typing import Dict, Any

# 导入LLM工具
from agent.llm_utils import call_llm_async


from pocketflow import AsyncNode


class ShortPlanningNode(AsyncNode):
    """短规划节点 - 生成精炼的短规划文档"""

    def __init__(self):
        super().__init__()
        self.name = "ShortPlanningNode"
        self.description = "生成精炼的短规划文档，用于和用户确认项目核心范围与颗粒度"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取用户需求和历史规划"""
        try:
            # 获取用户需求
            user_requirements = shared.get("user_requirements", "")
            if not user_requirements:
                return {"error": "用户需求不能为空"}

            # 获取上一版本的规划（可选）
            previous_planning = shared.get("previous_planning", "")

            # 获取改进点（可选）
            improvement_points = shared.get("improvement_points", [])

            return {
                "user_requirements": user_requirements,
                "previous_planning": previous_planning,
                "improvement_points": improvement_points,
                "generation_timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"短规划准备阶段失败: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行短规划文档生成"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            user_requirements = prep_result["user_requirements"]
            previous_planning = prep_result["previous_planning"]
            improvement_points = prep_result["improvement_points"]

            # 使用异步LLM生成步骤化规划文档（纯文本）
            planning_document = await self._generate_planning_document(
                user_requirements, previous_planning, improvement_points
            )

            return {
                "planning_document": planning_document,
                "generation_success": True
            }

        except Exception as e:
            raise e

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存短规划文档结果"""
        if "error" in exec_res:
            shared["planning_error"] = exec_res["error"]
            return "error"

        # 保存短规划文档
        shared["planning_document"] = exec_res["planning_document"]

        return "planning_complete"

    async def _generate_planning_document(self, user_requirements: str,
                                        previous_planning: str = "",
                                        improvement_points: list = None) -> str:
        """使用异步LLM生成步骤化的规划文档（纯文本）。"""

        # 构建LLM提示词
        prompt = self._build_planning_prompt(user_requirements, previous_planning, improvement_points or [])

        # 调用异步LLM，不再要求JSON格式
        result_str = await call_llm_async(prompt, is_json=False)

        # 直接返回纯文本结果
        return result_str.strip()

    def _build_planning_prompt(self, user_requirements: str,
                             previous_planning: str = "",
                             improvement_points: list = None) -> str:
        """
        构建生成步骤化流程的LLM提示词。
        """
        # 将所有需求、历史规划和改进点整合为一个完整的需求描述
        req_parts = [user_requirements]
        if previous_planning:
            req_parts.append("\n---参考的先前规划---")
            req_parts.append(str(previous_planning))
        if improvement_points:
            req_parts.append("\n---需要重点改进的方面---")
            req_parts.append("\n".join(f"- {point}" for point in improvement_points))
            req_parts.append("\n请综合以上所有信息，特别是改进点，生成一个全新的、更优化的流程。")

        # 将所有部分连接成一个字符串
        req_content = "\n".join(req_parts)

        prompt = f"""# 角色
你是一个经验丰富的系统架构师和工作流设计师。

# 任务
根据用户提供的【用户需求】和可选的【可用工具/MCP清单】，生成一个清晰、简洁的步骤化流程，用于实现该需求。

# 输入
1. **用户需求：**
   ```   
   {req_content}
   ```
2. **可用工具/MCP清单 (可选)：**
   ```
   ```

# 输出要求
1. **步骤化流程：**
   * 列出清晰的、序号化的步骤。
   * 每个步骤应描述一个核心动作/阶段。
   * 如果【可用工具/MCP清单】中有合适的工具，请在步骤中指明使用哪个工具。格式如：`步骤X：[动作描述] (使用：[工具名称])`。
   * 如果无完全匹配工具，或为了通用性，步骤应足够通用，允许用户后续集成自己的服务。
   * 指明可选步骤（例如，使用 `(可选)` 标记）。
   * 如果合适，可以建议并行处理的步骤。
2. **设计考虑 (可选，但推荐)：**
   * 简要说明一些关键的设计决策或灵活性考虑，例如数据格式转换、错误处理思路等。

# 示例（用于理解输出格式和风格）
**用户需求示例：** YouTube视频总结器：将视频总结为Topic和QA。
**可用工具/MCP清单示例：**
youtube_audio_fetch: 获取YouTube视频的音频
ASR_MCP: 将音频转换为文本

**期望输出示例：**
1. Fetch: 获取YouTube视频内容 (如果输入是视频链接，可考虑使用 youtube_audio_fetch MCP 获取音频；如果直接是音频文件，则跳过此工具)。
2. ToText (可选): 如果上一步获取的是音频，将音频转换为文本 (可考虑使用 ASR_MCP)。如果输入已是文本，则跳过此步骤。
3. Extract: 从文本中提取关键主题 (Topics) 和潜在问题 (Questions)。
4. Process:
   * 并行处理每个Topic：为每个Topic生成总结。
   * 并行处理每个Question：为每个Question生成或定位答案的亮点。
5. Output: 生成结构化的输出，例如JSON或可视化的HTML信息图，包含Topic总结和QA对。
---

**输出：步骤化流程：**(只输出步骤化流程，不需要有多余的解释)
"""
        return prompt
