"""
Flow Design Node

第三步：基于已识别的Node列表，设计pocketflow的Flow架构。
专注于设计Node之间的连接、Action驱动的转换逻辑。
"""

import time
import json
from typing import Dict, Any
from pocketflow import AsyncNode

# 导入LLM调用工具
from agent.llm_utils import call_llm_async
import asyncio


class FlowDesignNode(AsyncNode):
    """Flow设计节点 - 设计pocketflow的Flow架构"""
    
    def __init__(self):
        super().__init__()
        self.name = "FlowDesignNode"
        self.description = "设计pocketflow的Flow架构和Node连接逻辑"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取已识别的Node列表"""
        try:
            # 获取已识别的Node列表
            identified_nodes = shared.get("identified_nodes", [])

            # 获取Agent分析结果
            agent_analysis = shared.get("agent_analysis", {})

            # 获取原始需求信息
            user_input = shared.get("user_input", "")

            # 检查必需的输入
            if not identified_nodes:
                return {"error": "缺少已识别的Node列表"}

            if not agent_analysis:
                return {"error": "缺少Agent分析结果"}

            return {
                "identified_nodes": identified_nodes,
                "agent_analysis": agent_analysis,
                "user_input": user_input,
                "timestamp": time.time()
            }

        except Exception as e:
            return {"error": f"Flow design preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行阶段：设计Flow架构"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建Flow设计提示词
            prompt = self._build_flow_design_prompt(prep_result)
            
            # 异步调用LLM设计Flow
            flow_design = await self._design_flow_architecture(prompt)

            
            # 解析Flow设计结果
            parsed_flow = self._parse_flow_design(flow_design)
            
            return {
                "flow_design": parsed_flow,
                "raw_flow_design": flow_design,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Flow design failed: {str(e)}"}
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存Flow设计"""
        try:
            if "error" in exec_res:
                shared["flow_design_error"] = exec_res["error"]
                print(f"❌ Flow设计失败: {exec_res['error']}")
                return "error"
            
            # 保存Flow设计
            flow_design = exec_res["flow_design"]
            shared["flow_design"] = flow_design
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "flow_design",
                "status": "completed",
                "message": f"Flow设计完成：{len(flow_design.get('nodes', []))}个节点"
            })
            
            # 生成文件输出
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("flow_design", flow_design, shared)

            print(f"✅ Flow设计完成")
            print(f"   节点数量: {len(flow_design.get('nodes', []))}")
            print(f"   连接数量: {len(flow_design.get('connections', []))}")

            return "flow_designed"
            
        except Exception as e:
            shared["flow_design_post_error"] = str(e)
            print(f"❌ Flow设计后处理失败: {str(e)}")
            return "error"
    
    def _build_flow_design_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建Flow设计提示词"""
        identified_nodes = prep_result["identified_nodes"]
        agent_analysis = prep_result["agent_analysis"]

        prompt = f"""你是一个专业的pocketflow架构设计师。基于以下已识别的Node列表，设计完整的Flow编排。

**已识别的Node列表：**
{json.dumps(identified_nodes, indent=2, ensure_ascii=False)}

**Agent分析结果：**
{json.dumps(agent_analysis, indent=2, ensure_ascii=False)}

**原始结构化需求：**
{json.dumps(prep_result.get('structured_requirements', {}), indent=2, ensure_ascii=False)}

请基于上述已识别的Node列表，设计完整的Flow编排，输出JSON格式结果：

{{
    "flow_name": "Flow名称",
    "flow_description": "Flow描述",
    "start_node": "起始节点名称（必须来自已识别的Node列表）",
    "connections": [
        {{
            "from_node": "源节点（必须来自已识别的Node列表）",
            "to_node": "目标节点（必须来自已识别的Node列表）",
            "action": "触发的Action（default或具体action名）",
            "condition": "转换条件描述",
            "data_passed": "传递的数据描述"
        }}
    ],
    "execution_flow": [
        {{
            "step": 1,
            "node": "节点名称",
            "description": "此步骤的作用",
            "input_data": "输入数据来源",
            "output_data": "输出数据去向"
        }}
    ],
    "mermaid_diagram": "完整的Mermaid flowchart TD代码",
    "design_rationale": "Flow编排的设计理由"
}}

**编排要求：**
1. 只能使用已识别的Node列表中的Node
2. 确保数据流的完整性和逻辑性
3. 使用Action驱动的转换逻辑
4. 考虑错误处理和分支逻辑
5. Mermaid图要清晰展示所有连接和数据流
6. 确保每个Node都有明确的前置和后置关系

请确保Flow编排能够完整实现Agent的功能，并且数据流转合理。

**重要：请严格按照上述JSON格式输出，不要添加任何额外的文字说明、代码块标记或其他内容。直接输出纯JSON数据。**"""
        
        return prompt
    
    async def _design_flow_architecture(self, prompt: str) -> str:
        """调用LLM设计Flow架构"""
        try:
            # 使用重试机制调用LLM
            result = await call_llm_async(prompt, is_json=True)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    def _parse_flow_design(self, flow_design: str) -> Dict[str, Any]:
        """解析Flow设计结果"""
        try:
            # 尝试解析JSON
            if isinstance(flow_design, str):
                parsed_flow = json.loads(flow_design)
            else:
                parsed_flow = flow_design
            
            # 验证必需字段
            required_fields = ["flow_name", "nodes", "connections"]
            for field in required_fields:
                if field not in parsed_flow:
                    if field == "nodes":
                        parsed_flow[field] = []
                    elif field == "connections":
                        parsed_flow[field] = []
                    else:
                        parsed_flow[field] = f"未指定{field}"
            
            # 验证节点结构
            for node in parsed_flow.get("nodes", []):
                if "node_name" not in node:
                    node["node_name"] = "UnnamedNode"
                if "node_type" not in node:
                    node["node_type"] = "Node"
                if "purpose" not in node:
                    node["purpose"] = "待定义"
            
            # 验证连接结构
            for conn in parsed_flow.get("connections", []):
                if "from_node" not in conn:
                    conn["from_node"] = "unknown"
                if "to_node" not in conn:
                    conn["to_node"] = "unknown"
                if "action" not in conn:
                    conn["action"] = "default"
            
            return parsed_flow
            
        except json.JSONDecodeError as e:
            raise Exception(f"Flow设计JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"Flow设计解析失败: {e}")
