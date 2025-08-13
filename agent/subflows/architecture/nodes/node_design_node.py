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
from agent.llm_utils import call_llm_async


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

            # 模拟Node内容（实际应该从nodes_markdown中解析）
            node_content = """ExampleNode

- **Node类型**: AsyncNode
- **目的**: 示例节点
- **职责**: 演示节点设计
- **输入期望**: 示例输入
- **输出期望**: 示例输出
- **复杂度**: 简单
- **处理类型**: 示例处理
- **推荐重试**: 否"""

            print(f"🔧 设计Node")

            # 构建Node设计提示词
            prompt = self._build_node_design_prompt(context_data, node_content)

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
                print(f"❌ Node设计失败: {exec_res['error']}")
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

            # 使用简化文件工具直接写入markdown
            from ..utils.simple_file_util import write_file_directly
            write_file_directly("05_node_design.md", node_design_markdown, shared)

            print(f"✅ Node设计完成")

            return "nodes_designed"
            
        except Exception as e:
            shared["node_design_post_error"] = str(e)
            print(f"❌ Node设计后处理失败: {str(e)}")
            return "error"
    
    def _build_node_design_prompt(self, context_data: Dict[str, Any], node_content: str) -> str:
        """构建Node设计提示词"""
        prompt = f"""为以下Node设计详细的实现方案。

**Node信息：**
{node_content}

**Agent分析结果：**
{context_data.get("analysis_markdown", "")}

**Flow设计：**
{context_data.get("flow_markdown", "")}

**数据结构设计：**
{context_data.get("data_structure_json", "")}

请分析上述信息，设计出详细的Node实现方案。"""
        
        return prompt
    
    async def _design_single_node(self, prompt: str) -> str:
        """调用LLM设计单个Node"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的pocketflow Node设计师，专门设计基于pocketflow框架的Node实现。

请严格按照以下Markdown格式输出Node设计结果：

# Node详细设计结果

## [Node名称]

### 基本信息
- **Node类型**: [Node类型]
- **目的**: [Node目的]

### Prep阶段设计
- **描述**: [prep阶段的详细描述]
- **从shared读取**: [从shared读取的数据字段，用逗号分隔]
- **验证逻辑**: [数据验证逻辑]
- **准备步骤**: [准备步骤，用分号分隔]

### Exec阶段设计
- **描述**: [exec阶段的详细描述]
- **核心逻辑**: [核心处理逻辑描述]
- **处理步骤**: [处理步骤，用分号分隔]
- **错误处理**: [错误处理策略]

### Post阶段设计
- **描述**: [post阶段的详细描述]
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
1. 严格遵循prep/exec/post三阶段分离
2. exec阶段不能直接访问shared
3. 明确的Action驱动逻辑
4. 考虑错误处理和重试
5. 确保与Flow中其他Node的协调

重要：请严格按照上述Markdown格式输出，不要输出JSON格式！直接输出完整的Markdown文档。"""

            # 使用系统提示词调用LLM
            result = await call_llm_async(prompt, is_json=False, system_prompt=system_prompt)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    async def _design_single_node_detailed(self, prep_result: Dict[str, Any], node_info: Dict[str, Any]) -> Dict[str, Any]:
        """为单个Node执行详细设计（供批处理聚合器调用）"""
        try:
            node_name = node_info.get('node_name', 'Unknown')
            print(f"         🔧 开始详细设计Node: {node_name}")

            # 构建设计提示词
            print(f"         📝 构建设计提示词...")
            prompt = self._build_node_design_prompt(prep_result, node_info)
            prompt_length = len(prompt)
            print(f"         📏 提示词长度: {prompt_length} 字符")

            # 调用LLM设计
            print(f"         🤖 调用LLM API...")
            import asyncio
            import time

            llm_start = time.time()
            design_result = await self._design_single_node(prompt)
            llm_duration = time.time() - llm_start

            print(f"         ✅ LLM API调用成功 (耗时: {llm_duration:.2f}秒)")
            print(f"         📊 LLM返回结果长度: {len(str(design_result))} 字符")

            # 解析设计结果
            print(f"         🔍 解析设计结果...")
            parsed_result = self._parse_node_design(design_result, node_info)

            if parsed_result:
                print(f"         ✅ 设计结果解析成功")
                print(f"            Node名称: {parsed_result.get('node_name', 'Unknown')}")
                print(f"            设计阶段: {len(parsed_result.get('design_details', {}))} 个")
            else:
                print(f"         ❌ 设计结果解析失败")

            return parsed_result

        except Exception as e:
            print(f"         ❌ Node详细设计异常: {e}")
            import traceback
            print(f"         📋 异常堆栈: {traceback.format_exc()}")
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
                print(f"         ⚠️ LLM返回列表格式，取第一个元素")
            elif isinstance(parsed_data, dict):
                parsed_node = parsed_data
            else:
                raise Exception(f"LLM返回了不支持的数据类型: {type(parsed_data)}")

            print(f"         🔍 解析后的数据类型: {type(parsed_node)}")
            print(f"         📋 包含字段: {list(parsed_node.keys()) if isinstance(parsed_node, dict) else 'Not a dict'}")

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
                    print(f"         ⚠️ 缺少{stage}设计，将使用默认值")
                    design_details[stage] = {
                        "description": f"默认{stage}描述",
                        "steps": []
                    }
            
            return parsed_node
            
        except json.JSONDecodeError as e:
            raise Exception(f"Node设计JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"Node设计解析失败: {e}")

    def _analyze_node_position(self, node_name: str, flow_design: Dict[str, Any]) -> Dict[str, Any]:
        """分析Node在Flow中的位置和角色"""
        try:
            connections = flow_design.get("connections", [])
            start_node = flow_design.get("start_node", "")

            # 找到所有相关连接
            incoming_connections = [conn for conn in connections if conn.get("to_node") == node_name]
            outgoing_connections = [conn for conn in connections if conn.get("from_node") == node_name]

            # 分析节点类型
            node_type = "unknown"
            if node_name == start_node or not incoming_connections:
                node_type = "entry_point"  # 入口节点
            elif not outgoing_connections:
                node_type = "exit_point"   # 出口节点
            elif len(incoming_connections) > 1:
                node_type = "convergence"  # 汇聚节点
            elif len(outgoing_connections) > 1:
                node_type = "divergence"   # 分叉节点
            else:
                node_type = "processing"   # 处理节点

            # 计算节点深度（从起始节点的距离）
            depth = self._calculate_node_depth(node_name, connections, start_node)

            # 分析前置节点
            predecessor_nodes = [conn.get("from_node") for conn in incoming_connections]
            predecessor_actions = [conn.get("action", "default") for conn in incoming_connections]

            # 分析后续节点
            successor_nodes = [conn.get("to_node") for conn in outgoing_connections]
            successor_actions = [conn.get("action", "default") for conn in outgoing_connections]

            # 分析数据流特征
            data_flow_pattern = self._analyze_data_flow_pattern(
                node_name, incoming_connections, outgoing_connections
            )

            return {
                "node_type": node_type,
                "depth_from_start": depth,
                "is_start_node": node_name == start_node,
                "is_end_node": len(outgoing_connections) == 0,
                "predecessor_count": len(predecessor_nodes),
                "successor_count": len(successor_nodes),
                "predecessor_nodes": predecessor_nodes,
                "successor_nodes": successor_nodes,
                "incoming_actions": predecessor_actions,
                "outgoing_actions": successor_actions,
                "data_flow_pattern": data_flow_pattern,
                "complexity_level": self._assess_node_complexity(
                    len(incoming_connections), len(outgoing_connections)
                )
            }

        except Exception as e:
            # 如果分析失败，返回基本信息
            return {
                "node_type": "unknown",
                "depth_from_start": 0,
                "is_start_node": False,
                "is_end_node": False,
                "error": str(e)
            }

    def _calculate_node_depth(self, target_node: str, connections: list, start_node: str) -> int:
        """计算节点从起始节点的深度"""
        if target_node == start_node:
            return 0

        # 使用BFS计算最短路径
        from collections import deque

        queue = deque([(start_node, 0)])
        visited = {start_node}

        while queue:
            current_node, depth = queue.popleft()

            # 找到当前节点的所有后续节点
            for conn in connections:
                if conn.get("from_node") == current_node:
                    next_node = conn.get("to_node")
                    if next_node == target_node:
                        return depth + 1
                    if next_node not in visited:
                        visited.add(next_node)
                        queue.append((next_node, depth + 1))

        return -1  # 无法到达

    def _analyze_data_flow_pattern(self, node_name: str, incoming: list, outgoing: list) -> str:
        """分析节点的数据流模式"""
        incoming_count = len(incoming)
        outgoing_count = len(outgoing)

        if incoming_count == 0 and outgoing_count == 1:
            return "source"      # 数据源
        elif incoming_count == 1 and outgoing_count == 0:
            return "sink"        # 数据汇
        elif incoming_count == 1 and outgoing_count == 1:
            return "transform"   # 数据转换
        elif incoming_count > 1 and outgoing_count == 1:
            return "merge"       # 数据合并
        elif incoming_count == 1 and outgoing_count > 1:
            return "split"       # 数据分发
        elif incoming_count > 1 and outgoing_count > 1:
            return "hub"         # 数据枢纽
        else:
            return "isolated"    # 孤立节点

    def _assess_node_complexity(self, incoming_count: int, outgoing_count: int) -> str:
        """评估节点复杂度"""
        total_connections = incoming_count + outgoing_count

        if total_connections <= 2:
            return "simple"
        elif total_connections <= 4:
            return "moderate"
        else:
            return "complex"
