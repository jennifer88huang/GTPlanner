"""
Node Design Node

第五步：基于数据结构设计，详细设计每个Node的prep/exec/post三阶段逻辑。
专注于每个Node的具体实现细节和职责分离。
"""

import time
import json
import asyncio
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入LLM调用工具
from utils.openai_client import get_openai_client
from agent.streaming import (
    emit_processing_status,
    emit_error
)


class NodeDesignNode(AsyncNode):
    """Node设计节点 - 详细设计每个Node的实现"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignNode"
        self.description = "详细设计每个Node的prep/exec/post三阶段实现"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取Flow设计结果"""
        try:
            # 获取markdown格式的设计结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")
            flow_markdown = shared.get("flow_markdown", "")
            data_structure_json = shared.get("data_structure_json", "")

            # 获取项目状态信息
            short_planning = shared.get("short_planning", "")
            user_requirements = shared.get("user_requirements", "")
            research_findings = shared.get("research_findings", {})
            recommended_tools = shared.get("recommended_tools", [])

            # 检查必需的输入
            if not analysis_markdown:
                return {"error": "缺少Agent分析结果"}

            if not nodes_markdown:
                return {"error": "缺少Node识别结果"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "flow_markdown": flow_markdown,
                "data_structure_json": data_structure_json,
                "short_planning": short_planning,
                "user_requirements": user_requirements,
                "research_findings": research_findings,
                "recommended_tools": recommended_tools,
                "streaming_session": shared.get("streaming_session"),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：设计每个Node的详细实现"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建上下文数据
            context_data = {
                "analysis_markdown": prep_result.get("analysis_markdown", ""),
                "nodes_markdown": prep_result.get("nodes_markdown", ""),
                "flow_markdown": prep_result.get("flow_markdown", ""),
                "data_structure_json": prep_result.get("data_structure_json", "")
            }


            # 发送处理状态事件
            streaming_session = prep_result.get("streaming_session")
            if streaming_session:
                from agent.streaming import emit_processing_status_from_prep
                await emit_processing_status_from_prep(prep_result, "🔧 设计Node")

            # 构建Node设计提示词
            prompt = self._build_node_design_prompt(context_data)

            # 异步调用LLM设计Node，直接输出markdown
            node_design_markdown = await self._design_single_node(prompt)

            return {
                "node_design_markdown": node_design_markdown,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Node design failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存Node设计"""
        try:
            if "error" in exec_res:
                shared["node_design_error"] = exec_res["error"]
                await emit_error(shared, f"❌ Node设计失败: {exec_res['error']}")
                return "error"
            
            # 保存Node设计markdown
            node_design_markdown = exec_res["node_design_markdown"]
            shared["node_design_markdown"] = node_design_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design",
                "status": "completed",
                "message": "Node设计完成"
            })

            # 使用流式事件发送设计文档
            from agent.streaming import emit_design_document
            await emit_design_document(shared, "05_node_design.md", node_design_markdown)

            await emit_processing_status(shared, "✅ Node设计完成")

            return "nodes_designed"

        except Exception as e:
            shared["node_design_post_error"] = str(e)
            await emit_error(shared, f"❌ Node设计后处理失败: {str(e)}")
            return "error"
    
    def _build_node_design_prompt(self, context_data: Dict[str, Any], node_info: Dict[str, Any] = None) -> str:
        """构建Node设计提示词"""

        # 构建推荐工具信息
        recommended_tools = context_data.get("recommended_tools", [])
        tools_info = ""
        if recommended_tools:
            tools_list = []
            for tool in recommended_tools:
                # 添加 None 检查，防止 tool 为 None
                if tool and isinstance(tool, dict):
                    tool_name = tool.get("name", tool.get("id", "未知工具"))
                    tool_type = tool.get("type", "")
                    tool_summary = tool.get("summary", tool.get("description", ""))
                    tools_list.append(f"- {tool_name} ({tool_type}): {tool_summary}")
            tools_info = "\n".join(tools_list)

        # 构建技术调研信息
        research_findings = context_data.get("research_findings", {})
        research_info = ""
        if research_findings and isinstance(research_findings, dict):
            # 使用正确的字段名
            if research_findings.get("summary"):
                research_info += f"**调研摘要：**\n{research_findings['summary']}\n\n"

            # 从关键词结果中提取关键信息
            keyword_results = research_findings.get("keyword_results", [])
            if keyword_results:
                successful_results = [r for r in keyword_results if r.get("success", False)]
                if successful_results:
                    research_info += "**关键发现：**\n"
                    for result in successful_results[:3]:  # 只显示前3个结果
                        keyword = result.get("keyword", "")
                        result_data = result.get("result", {})
                        if result_data and result_data.get("summary"):
                            research_info += f"- {keyword}: {result_data['summary'][:100]}...\n"
                    research_info += "\n"

        # 如果提供了特定的node_info，使用它；否则使用通用的nodes_markdown
        node_info_text = ""
        if node_info:
            node_info_text = f"**当前设计的Node：**\n{node_info}\n\n"

        prompt = f"""为以下Node设计详细的实现方案。

{node_info_text}**Node信息：**
{context_data.get("nodes_markdown")}

**Agent分析结果：**
{context_data.get("analysis_markdown", "")}

**Flow设计：**
{context_data.get("flow_markdown", "")}

**数据结构设计：**
{context_data.get("data_structure_json", "")}

**用户需求：**
{context_data.get("user_requirements", "未提供用户需求")}

**项目规划：**
{context_data.get("short_planning", "未提供项目规划")}

**技术调研结果：**
{research_info if research_info else "未提供技术调研结果"}

**推荐工具：**
{tools_info if tools_info else "无推荐工具"}

请分析上述信息，设计出详细的Node实现方案。"""
        
        return prompt
    
    async def _design_single_node(self, prompt: str) -> str:
        """调用LLM设计单个Node"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的pocketflow Node设计师，专门设计基于pocketflow框架的Node实现。

**重要：Node类型和方法名约定**
- **AsyncNode**: 使用异步方法名 prep_async、exec_async、post_async
- **同步Node**: 使用同步方法名 prep、exec、post

请根据Node类型选择正确的方法名，并严格按照以下Markdown格式输出Node设计结果：

# Node详细设计结果

## [Node名称]

### 基本信息
- **Node类型**: [AsyncNode 或 Node]
- **目的**: [Node目的]

### Prep阶段设计 (AsyncNode使用PrepAsync阶段设计)
- **描述**: [prep/prep_async阶段的详细描述]
- **从shared读取**: [从shared读取的数据字段，用逗号分隔]
- **验证逻辑**: [数据验证逻辑]
- **准备步骤**: [准备步骤，用分号分隔]

### Exec阶段设计 (AsyncNode使用ExecAsync阶段设计)
- **描述**: [exec/exec_async阶段的详细描述]
- **核心逻辑**: [核心处理逻辑描述]
- **处理步骤**: [处理步骤，用分号分隔]
- **错误处理**: [错误处理策略]

### Post阶段设计 (AsyncNode使用PostAsync阶段设计)
- **描述**: [post/post_async阶段的详细描述]
- **结果处理**: [结果处理逻辑]
- **更新shared**: [更新到shared的数据，用逗号分隔]
- **Action逻辑**: [Action决策逻辑]
- **可能Actions**: [可能返回的Action列表，用逗号分隔]

### 数据访问
- **读取字段**: [读取的shared字段，用逗号分隔]
- **写入字段**: [写入的shared字段，用逗号分隔]

### 重试配置
- **最大重试**: [最大重试次数]次
- **等待时间**: [等待时间]秒

设计要求：
1. **方法名约定**：
   - AsyncNode: 严格遵循prep_async/exec_async/post_async三阶段分离
   - 同步Node: 严格遵循prep/exec/post三阶段分离
2. exec/exec_async阶段不能直接访问shared
3. 明确的Action驱动逻辑
4. 考虑错误处理和重试
5. 确保与Flow中其他Node的协调

重要：请严格按照上述Markdown格式输出，不要输出JSON格式！直接输出完整的Markdown文档。"""

            # 使用系统提示词调用LLM
            client = get_openai_client()
            response = await client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                system_prompt=system_prompt
            )
            result = response.choices[0].message.content if response.choices else ""
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    async def _design_single_node_detailed(self, prep_result: Dict[str, Any], node_info: Dict[str, Any]) -> Dict[str, Any]:
        """为单个Node执行详细设计（供批处理聚合器调用）"""
        try:
            # 构建设计提示词
            prompt = self._build_node_design_prompt(prep_result, node_info)

            # 调用LLM设计
            design_result = await self._design_single_node(prompt)

            # 解析设计结果
            parsed_result = self._parse_node_design(design_result, node_info)

            return parsed_result

        except Exception as e:
            # 简化错误处理，移除详细的 print 语句
            raise Exception(f"单个Node设计失败: {str(e)}")

    def _parse_node_design(self, node_design: str, original_node_info: Dict[str, Any]) -> Dict[str, Any]:
        """解析Node设计结果"""
        try:
            # 尝试解析JSON
            if isinstance(node_design, str):
                parsed_data = json.loads(node_design)
            else:
                parsed_data = node_design

            # 处理LLM可能返回列表的情况
            if isinstance(parsed_data, list):
                if len(parsed_data) == 0:
                    raise Exception("LLM返回空列表")
                # 取第一个元素
                parsed_node = parsed_data[0]
            elif isinstance(parsed_data, dict):
                parsed_node = parsed_data
            else:
                raise Exception(f"LLM返回了不支持的数据类型: {type(parsed_data)}")

            # 验证必需字段
            if not isinstance(parsed_node, dict):
                raise Exception(f"解析后的Node数据不是字典类型: {type(parsed_node)}")

            if "node_name" not in parsed_node:
                parsed_node["node_name"] = original_node_info.get("node_name", "UnknownNode")
            
            if "node_type" not in parsed_node:
                parsed_node["node_type"] = original_node_info.get("node_type", "Node")
            
            if "design_details" not in parsed_node:
                raise Exception("缺少design_details字段")
            
            # 验证design_details结构
            design_details = parsed_node["design_details"]
            if not isinstance(design_details, dict):
                raise Exception(f"design_details不是字典类型: {type(design_details)}")

            required_stages = ["prep_stage", "exec_stage", "post_stage"]

            for stage in required_stages:
                if stage not in design_details:
                    # 简化日志，移除 print 语句
                    design_details[stage] = {
                        "description": f"默认{stage}描述",
                        "steps": []
                    }
            
            return parsed_node
            
        except json.JSONDecodeError as e:
            raise Exception(f"Node设计JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"Node设计解析失败: {e}")
