"""
Data Structure Design Node

第四步：基于Flow和Node设计，设计shared存储的数据结构。
专注于Agent间数据传递和存储的设计。
"""

import time
import json
from typing import Dict, Any
from pocketflow import Node

# 导入LLM调用工具
from agent.common import call_llm_async
import asyncio


class DataStructureDesignNode(Node):
    """数据结构设计节点 - 设计shared存储结构"""
    
    def __init__(self):
        super().__init__()
        self.name = "DataStructureDesignNode"
        self.description = "设计pocketflow Agent的shared存储数据结构"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：获取Flow和Node设计结果"""
        try:
            # 获取Flow设计结果
            flow_design = shared.get("flow_design", {})
            
            # 获取已识别的Node列表
            identified_nodes = shared.get("identified_nodes", [])

            # 获取Agent分析结果
            agent_analysis = shared.get("agent_analysis", {})

            # 检查必需的输入
            if not flow_design:
                return {"error": "缺少Flow设计结果"}

            if not identified_nodes:
                return {"error": "缺少已识别的Node列表"}
            
            return {
                "flow_design": flow_design,
                "identified_nodes": identified_nodes,
                "agent_analysis": agent_analysis,
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Data structure design preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：设计shared数据结构"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            # 构建数据结构设计提示词
            prompt = self._build_data_structure_prompt(prep_result)
            
            # 调用LLM设计数据结构
            data_structure = asyncio.run(self._design_data_structure(prompt))
            
            # 解析数据结构设计结果
            parsed_structure = self._parse_data_structure(data_structure)
            
            return {
                "data_structure": parsed_structure,
                "raw_data_structure": data_structure,
                "design_success": True
            }
            
        except Exception as e:
            return {"error": f"Data structure design failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存数据结构设计"""
        try:
            if "error" in exec_res:
                shared["data_structure_error"] = exec_res["error"]
                print(f"❌ 数据结构设计失败: {exec_res['error']}")
                return "error"
            
            # 保存数据结构设计
            data_structure = exec_res["data_structure"]
            shared["data_structure"] = data_structure
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "data_structure_design",
                "status": "completed",
                "message": f"数据结构设计完成：{len(data_structure.get('shared_fields', []))}个字段"
            })

            # 生成文件输出
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("data_structure", data_structure, shared)

            print(f"✅ 数据结构设计完成")
            print(f"   共享字段数: {len(data_structure.get('shared_fields', []))}")

            return "data_structure_complete"
            
        except Exception as e:
            shared["data_structure_post_error"] = str(e)
            print(f"❌ 数据结构设计后处理失败: {str(e)}")
            return "error"
    
    def _build_data_structure_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建数据结构设计提示词"""
        flow_design = prep_result["flow_design"]
        identified_nodes = prep_result["identified_nodes"]
        agent_analysis = prep_result.get("agent_analysis", {})

        # 基于Flow设计和Node信息分析数据需求
        nodes_summary = []
        for node in identified_nodes:
            node_name = node.get("node_name", "Unknown")
            purpose = node.get("purpose", "")
            nodes_summary.append({
                "node": node_name,
                "purpose": purpose,
                "expected_inputs": node.get("input_expectations", ""),
                "expected_outputs": node.get("output_expectations", "")
            })
        
        prompt = f"""你是一个专业的数据架构设计师。基于以下Flow和Node设计，设计完整的shared存储数据结构。

**Agent分析结果：**
{json.dumps(agent_analysis, indent=2, ensure_ascii=False)}

**Flow设计：**
{json.dumps(flow_design, indent=2, ensure_ascii=False)}

**Node信息汇总：**
{json.dumps(nodes_summary, indent=2, ensure_ascii=False)}

请设计完整的shared存储数据结构，输出JSON格式结果：

{{
    "shared_structure_description": "shared存储的整体描述",
    "shared_fields": [
        {{
            "field_name": "字段名称",
            "data_type": "数据类型（如：str, dict, list等）",
            "description": "字段描述",
            "purpose": "字段用途",
            "read_by_nodes": ["读取此字段的Node列表"],
            "written_by_nodes": ["写入此字段的Node列表"],
            "example_value": "示例值或结构",
            "required": true/false
        }}
    ],
    "data_flow_patterns": [
        {{
            "pattern_name": "数据流模式名称",
            "description": "数据流描述",
            "involved_fields": ["涉及的字段"],
            "flow_sequence": ["数据流转顺序"]
        }}
    ],
    "shared_example": {{
        "// 完整的shared存储示例结构": "注释",
        "field1": "示例值1",
        "field2": {{}},
        "field3": []
    }}
}}

**设计要求：**
1. 确保所有Node的数据需求都被满足
2. 避免数据冗余和冲突
3. 清晰的数据流转路径
4. 考虑数据的生命周期
5. 遵循pocketflow的shared存储最佳实践

请确保设计的数据结构能够支持整个Agent的正常运行。

**重要：请严格按照上述JSON格式输出，不要添加任何额外的文字说明、代码块标记或其他内容。直接输出纯JSON数据。**"""
        
        return prompt
    
    async def _design_data_structure(self, prompt: str) -> str:
        """调用LLM设计数据结构"""
        try:
            # 使用重试机制调用LLM
            result = await call_llm_async(prompt, is_json=True, max_retries=3, retry_delay=2)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    
    def _parse_data_structure(self, data_structure: str) -> Dict[str, Any]:
        """解析数据结构设计结果"""
        try:
            # 尝试解析JSON
            if isinstance(data_structure, str):
                parsed_structure = json.loads(data_structure)
            else:
                parsed_structure = data_structure
            
            # 验证必需字段
            required_fields = ["shared_fields", "shared_example"]
            for field in required_fields:
                if field not in parsed_structure:
                    if field == "shared_fields":
                        parsed_structure[field] = []
                    elif field == "shared_example":
                        parsed_structure[field] = {}
            
            # 验证shared_fields结构
            for field_info in parsed_structure.get("shared_fields", []):
                if "field_name" not in field_info:
                    raise Exception("shared_fields中缺少field_name")
                if "data_type" not in field_info:
                    field_info["data_type"] = "unknown"
                if "description" not in field_info:
                    field_info["description"] = "待描述"
            
            return parsed_structure
            
        except json.JSONDecodeError as e:
            raise Exception(f"数据结构设计JSON解析失败: {e}")
        except Exception as e:
            raise Exception(f"数据结构设计解析失败: {e}")
