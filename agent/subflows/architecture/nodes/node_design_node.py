"""
Node Design Node

第五步：基于数据结构设计，详细设计每个Node的prep/exec/post三阶段逻辑。
专注于每个Node的具体实现细节和职责分离。
"""

import time
import json
import asyncio
from typing import Dict, Any
from pocketflow import Node

# 导入LLM调用工具
from agent.common import call_llm_async
import asyncio


class NodeDesignNode(Node):
    """Node设计节点 - 详细设计每个Node的实现"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignNode"
        self.description = "详细设计每个Node的prep/exec/post三阶段实现"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取Flow设计结果"""
        try:
            # 获取Flow设计结果
            flow_design = shared.get("flow_design", {})

            # 获取已识别的Node列表
            identified_nodes = shared.get("identified_nodes", [])

            # 获取数据结构设计
            data_structure = shared.get("data_structure", {})

            # 获取Agent分析结果
            agent_analysis = shared.get("agent_analysis", {})

            # 检查必需的输入
            if not flow_design:
                return {"error": "缺少Flow设计结果"}

            if not identified_nodes:
                return {"error": "缺少已识别的Node列表"}

            if not data_structure:
                return {"error": "缺少数据结构设计"}

            return {
                "flow_design": flow_design,
                "identified_nodes": identified_nodes,
                "data_structure": data_structure,
                "agent_analysis": agent_analysis,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node design preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：设计每个Node的详细实现"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            identified_nodes = prep_result["identified_nodes"]

            # 为每个Node设计详细实现
            detailed_nodes = []

            for node_info in identified_nodes:
                node_name = node_info.get("node_name", "UnknownNode")
                print(f"🔧 设计Node: {node_name}")
                
                # 构建Node设计提示词
                prompt = self._build_node_design_prompt(prep_result, node_info)
                
                # 调用LLM设计Node
                node_design = asyncio.run(self._design_single_node(prompt))
                
                # 解析Node设计结果
                parsed_node = self._parse_node_design(node_design, node_info)
                detailed_nodes.append(parsed_node)
            
            return {
                "detailed_nodes": detailed_nodes,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Node design failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存Node设计"""
        try:
            if "error" in exec_res:
                shared["node_design_error"] = exec_res["error"]
                print(f"❌ Node设计失败: {exec_res['error']}")
                return "error"
            
            # 保存Node设计
            detailed_nodes = exec_res["detailed_nodes"]
            shared["detailed_nodes"] = detailed_nodes
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design",
                "status": "completed",
                "message": f"Node设计完成：{len(detailed_nodes)}个节点"
            })

            # 生成文件输出
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("node_design", detailed_nodes, shared)

            print(f"✅ Node设计完成")
            print(f"   设计节点数: {len(detailed_nodes)}")

            return "nodes_designed"
            
        except Exception as e:
            shared["node_design_post_error"] = str(e)
            print(f"❌ Node设计后处理失败: {str(e)}")
            return "error"
    
    def _build_node_design_prompt(self, prep_result: Dict[str, Any], node_info: Dict[str, Any]) -> str:
        """构建Node设计提示词"""
        flow_design = prep_result["flow_design"]
        agent_analysis = prep_result.get("agent_analysis", {})

        node_name = node_info.get("node_name", "UnknownNode")
        node_type = node_info.get("node_type", "Node")
        node_purpose = node_info.get("purpose", "")

        # 分析此Node在Flow中的位置和连接关系
        connections = flow_design.get("connections", [])
        incoming_nodes = [conn for conn in connections if conn.get("to_node") == node_name]
        outgoing_nodes = [conn for conn in connections if conn.get("from_node") == node_name]

        # 分析前置和后置Node的信息
        context_info = {
            "incoming_connections": incoming_nodes,
            "outgoing_connections": outgoing_nodes,
            "position_in_flow": self._analyze_node_position(node_name, flow_design)
        }

        prompt = f"""你是一个专业的pocketflow Node设计师。请为以下Node设计详细的实现方案。

**Node基本信息：**
- 名称: {node_name}
- 类型: {node_type}
- 目的: {node_purpose}

**Node在Flow中的位置和连接关系：**
{json.dumps(context_info, indent=2, ensure_ascii=False)}

**完整Flow设计：**
{json.dumps(flow_design, indent=2, ensure_ascii=False)}

**Agent分析结果：**
{json.dumps(agent_analysis, indent=2, ensure_ascii=False)}

请设计这个Node的详细实现，输出JSON格式结果：

{{
    "node_name": "{node_name}",
    "node_type": "{node_type}",
    "purpose": "节点目的",
    "design_details": {{
        "prep_stage": {{
            "description": "prep阶段的详细描述",
            "input_from_shared": ["从shared读取的数据字段"],
            "validation_logic": "数据验证逻辑",
            "preparation_steps": ["准备步骤1", "准备步骤2"],
            "output_prep_res": "prep_res的结构描述"
        }},
        "exec_stage": {{
            "description": "exec阶段的详细描述",
            "core_logic": "核心处理逻辑描述",
            "processing_steps": ["处理步骤1", "处理步骤2"],
            "error_handling": "错误处理策略",
            "output_exec_res": "exec_res的结构描述"
        }},
        "post_stage": {{
            "description": "post阶段的详细描述",
            "result_processing": "结果处理逻辑",
            "shared_updates": ["更新到shared的数据"],
            "action_logic": "Action决策逻辑",
            "possible_actions": ["可能返回的Action列表"]
        }}
    }},
    "data_access": {{
        "reads_from_shared": ["读取的shared字段"],
        "writes_to_shared": ["写入的shared字段"],
        "temp_variables": ["临时变量"]
    }},
    "retry_config": {{
        "max_retries": 3,
        "wait": 1.0,
        "retry_conditions": ["重试条件"]
    }}
}}

**设计要求：**
1. 严格遵循prep/exec/post三阶段分离
2. exec阶段不能直接访问shared
3. 明确的Action驱动逻辑
4. 考虑错误处理和重试
5. 确保与Flow中其他Node的协调

请确保设计符合pocketflow的最佳实践。

**重要：请严格按照上述JSON格式输出，不要添加任何额外的文字说明、代码块标记或其他内容。直接输出纯JSON数据。**"""
        
        return prompt
    
    async def _design_single_node(self, prompt: str) -> str:
        """调用LLM设计单个Node"""
        try:
            # 使用重试机制调用LLM
            result = await call_llm_async(prompt, is_json=True, max_retries=3, retry_delay=2)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    def _design_single_node_detailed(self, prep_result: Dict[str, Any], node_info: Dict[str, Any]) -> Dict[str, Any]:
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
            design_result = asyncio.run(self._design_single_node(prompt))
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
