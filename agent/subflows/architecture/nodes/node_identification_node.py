"""
Node Identification Node

第二步：基于Agent需求分析，确定需要哪些Node。
专注于识别完成Agent功能所需的所有Node，为后续Flow编排提供基础。
"""

import time
import json
import time
from typing import Dict, Any
from pocketflow import Node

# 导入LLM调用工具
from agent.common import call_llm_async
import asyncio


class NodeIdentificationNode(Node):
    """Node识别节点 - 确定Agent需要的所有Node"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeIdentificationNode"
        self.description = "基于Agent需求分析，识别需要的所有Node"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取Agent分析结果"""
        try:
            # 获取Agent分析结果
            agent_analysis = shared.get("agent_analysis", {})
            
            # 获取原始需求信息
            structured_requirements = shared.get("structured_requirements", {})
            user_input = shared.get("user_input", "")
            
            # 检查必需的输入
            if not agent_analysis:
                return {"error": "缺少Agent分析结果"}
            
            return {
                "agent_analysis": agent_analysis,
                "structured_requirements": structured_requirements,
                "user_input": user_input,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node identification preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：识别所需的Node"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建Node识别提示词
            prompt = self._build_node_identification_prompt(prep_result)
            
            # 调用LLM识别Node
            node_list = asyncio.run(self._identify_nodes(prompt))
            
            # 解析Node识别结果
            parsed_nodes = self._parse_node_list(node_list)
            
            return {
                "identified_nodes": parsed_nodes,
                "raw_node_list": node_list,
                "identification_success": True
            }
            
        except Exception as e:
            return {"error": f"Node identification failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存识别的Node列表"""
        try:
            if "error" in exec_res:
                shared["node_identification_error"] = exec_res["error"]
                print(f"❌ Node识别失败: {exec_res['error']}")
                return "error"
            
            # 保存识别的Node列表
            identified_nodes = exec_res["identified_nodes"]
            shared["identified_nodes"] = identified_nodes
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_identification",
                "status": "completed",
                "message": f"Node识别完成：{len(identified_nodes)}个节点"
            })
            
            # 生成文件输出
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("node_identification", identified_nodes, shared)

            print(f"✅ Node识别完成")
            print(f"   识别节点数: {len(identified_nodes)}")
            for node in identified_nodes:
                print(f"   - {node.get('node_name', 'Unknown')}: {node.get('purpose', '')}")

            return "nodes_identified"
            
        except Exception as e:
            shared["node_identification_post_error"] = str(e)
            print(f"❌ Node识别后处理失败: {str(e)}")
            return "error"
    
    def _build_node_identification_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建Node识别提示词"""
        agent_analysis = prep_result["agent_analysis"]
        user_input = prep_result.get("user_input", "")
        
        # 提取核心功能
        core_functions = agent_analysis.get("core_functions", [])
        agent_type = agent_analysis.get("agent_type", "")
        processing_pattern = agent_analysis.get("processing_pattern", "")
        
        prompt = f"""你是一个专业的pocketflow架构师。基于以下Agent需求分析结果，识别完成此Agent功能所需的所有Node。

**Agent分析结果：**
{json.dumps(agent_analysis, indent=2, ensure_ascii=False)}

**原始结构化需求：**
{json.dumps(prep_result.get('structured_requirements', {}), indent=2, ensure_ascii=False)}

请分析Agent的核心功能，识别需要的所有Node。输出JSON格式结果：

{{
    "nodes_overview": "Node设计的整体思路",
    "nodes": [
        {{
            "node_name": "Node名称（清晰描述性的名称）",
            "node_type": "Node类型（Node/AsyncNode/BatchNode等）",
            "purpose": "Node的具体目的和职责",
            "responsibility": "Node负责的具体功能",
            "input_expectations": "期望的输入数据类型",
            "output_expectations": "期望的输出数据类型",
            "complexity_level": "复杂度（简单/中等/复杂）",
            "processing_type": "处理类型（数据预处理/核心计算/结果后处理/IO操作等）",
            "retry_recommended": true/false
        }}
    ],
    "design_rationale": "为什么选择这些Node的设计理由"
}}

**识别要求：**
1. 每个Node都有明确的单一职责
2. Node之间职责不重叠
3. 覆盖Agent的所有核心功能
4. 考虑数据流的完整性（输入→处理→输出）
5. 优先使用AsyncNode提高性能
6. 考虑错误处理和重试需求

**常见Node模式参考：**
- InputValidationNode: 输入验证和预处理
- DataRetrievalNode: 数据获取和检索
- CoreProcessingNode: 核心业务逻辑处理
- ResultFormattingNode: 结果格式化
- OutputDeliveryNode: 结果输出和传递

请确保识别的Node能够完整实现Agent的所有功能需求。

**重要：请严格按照上述JSON数组格式输出，不要添加任何额外的文字说明、代码块标记或其他内容。直接输出纯JSON数据。**"""
        
        return prompt
    
    async def _identify_nodes(self, prompt: str) -> str:
        """调用LLM识别Node"""
        try:
            # 使用重试机制调用LLM
            result = await call_llm_async(prompt, is_json=True, max_retries=3, retry_delay=2)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")

    def _generate_nodes_file(self, shared: Dict[str, Any], identified_nodes: list):
        """生成Node识别结果文件"""
        try:
            # 导入Node_Output
            from agent.nodes.node_output import NodeOutput

            node_output = NodeOutput(output_dir="output")

            # 构建文件内容
            content = f"""# Node识别结果

## 概述
基于Agent需求分析，识别出以下{len(identified_nodes)}个Node：

"""

            for i, node in enumerate(identified_nodes, 1):
                if isinstance(node, dict):
                    content += f"""## {i}. {node.get('node_name', 'Unknown')}

- **Node类型**: {node.get('node_type', 'Unknown')}
- **目的**: {node.get('purpose', '')}
- **职责**: {node.get('responsibility', '')}
- **输入期望**: {node.get('input_expectations', '')}
- **输出期望**: {node.get('output_expectations', '')}
- **复杂度**: {node.get('complexity_level', 'Unknown')}
- **处理类型**: {node.get('processing_type', 'Unknown')}
- **推荐重试**: {'是' if node.get('retry_recommended', False) else '否'}

"""

            content += f"""
## Node类型统计
"""

            # 统计Node类型
            node_types = {}
            for node in identified_nodes:
                if isinstance(node, dict):
                    node_type = node.get('node_type', 'Unknown')
                    node_types[node_type] = node_types.get(node_type, 0) + 1

            for node_type, count in node_types.items():
                content += f"- **{node_type}**: {count}个\n"

            content += f"""
---
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""

            # 准备文件数据
            files_to_generate = [
                {
                    "filename": "02_identified_nodes.md",
                    "content": content
                }
            ]

            # 生成文件
            result = node_output.generate_files_directly(files_to_generate)

            if result["status"] == "success":
                # 更新或初始化生成的文件信息
                if "generated_files" not in shared:
                    shared["generated_files"] = []
                shared["generated_files"].extend(result["generated_files"])
                shared["output_directory"] = result["output_directory"]
                print(f"📄 Node识别文件已生成: {result['output_directory']}/02_identified_nodes.md")
            else:
                print(f"⚠️ Node识别文件生成失败: {result.get('error', '未知错误')}")

        except Exception as e:
            print(f"⚠️ Node识别文件生成出错: {str(e)}")
            # 即使文件生成失败，也不影响主流程
    
    def _parse_node_list(self, node_list: str) -> list:
        """解析Node识别结果"""
        try:
            # 尝试解析JSON
            if isinstance(node_list, str):
                parsed_result = json.loads(node_list)
            else:
                parsed_result = node_list
            
            # 获取nodes列表
            nodes = parsed_result.get("nodes", [])
            
            if not nodes:
                raise Exception("没有识别到任何Node")
            
            # 验证每个Node的必需字段
            for i, node in enumerate(nodes):
                if "node_name" not in node:
                    raise Exception(f"Node {i} 缺少node_name字段")
                if "purpose" not in node:
                    node["purpose"] = "待定义目的"
                if "node_type" not in node:
                    node["node_type"] = "Node"
                if "responsibility" not in node:
                    node["responsibility"] = "待定义职责"
            
            return nodes
            
        except json.JSONDecodeError as e:
            raise Exception(f"Node识别JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"Node识别结果解析失败: {e}")
