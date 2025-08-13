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
            # 获取markdown格式的设计结果
            analysis_markdown = shared.get("analysis_markdown", "")
            nodes_markdown = shared.get("nodes_markdown", "")

            # 获取原始需求信息
            structured_requirements = shared.get("structured_requirements", {})

            # 检查必需的输入
            if not analysis_markdown:
                return {"error": "缺少Agent分析结果"}

            if not nodes_markdown:
                return {"error": "缺少Node识别结果"}

            return {
                "analysis_markdown": analysis_markdown,
                "nodes_markdown": nodes_markdown,
                "structured_requirements": structured_requirements,
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

            # 异步调用LLM设计Flow，直接输出markdown
            flow_markdown = await self._design_flow_architecture(prompt)

            return {
                "flow_markdown": flow_markdown,
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
            
            # 保存Flow设计markdown
            flow_markdown = exec_res["flow_markdown"]
            shared["flow_markdown"] = flow_markdown

            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []

            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "flow_design",
                "status": "completed",
                "message": "Flow设计完成"
            })

            # 使用简化文件工具直接写入markdown
            from ..utils.simple_file_util import write_file_directly
            write_file_directly("03_flow_design.md", flow_markdown, shared)

            print(f"✅ Flow设计完成")

            return "flow_designed"
            
        except Exception as e:
            shared["flow_design_post_error"] = str(e)
            print(f"❌ Flow设计后处理失败: {str(e)}")
            return "error"
    
    def _build_flow_design_prompt(self, prep_result: Dict[str, Any]) -> str:
        """构建Flow设计提示词"""
        analysis_markdown = prep_result.get("analysis_markdown", "")
        nodes_markdown = prep_result.get("nodes_markdown", "")

        prompt = f"""基于以下已识别的Node列表，设计完整的Flow编排。

**Agent分析结果：**
{analysis_markdown}

**已识别的Node列表：**
{nodes_markdown}

**原始结构化需求：**
{json.dumps(prep_result.get('structured_requirements', {}), indent=2, ensure_ascii=False)}

请分析上述信息，设计出完整的Flow编排方案。"""
        
        return prompt
    
    async def _design_flow_architecture(self, prompt: str) -> str:
        """调用LLM设计Flow架构"""
        try:
            # 构建系统提示词
            system_prompt = """你是一个专业的pocketflow架构设计师，专门设计基于pocketflow框架的Flow编排。

请严格按照以下Markdown格式输出Flow设计结果：

# Flow设计结果

## Flow概述
- **Flow名称**: [Flow名称]
- **Flow描述**: [Flow的整体描述]
- **起始节点**: [起始节点名称，必须来自已识别的Node列表]

## Flow图表

```mermaid
flowchart TD
    [在这里生成完整的Mermaid flowchart TD代码]
```

## 节点连接关系

### 连接 1
- **源节点**: [源节点名称]
- **目标节点**: [目标节点名称]
- **触发Action**: [default或具体action名]
- **转换条件**: [转换条件描述]
- **传递数据**: [传递的数据描述]

## 执行流程

### 步骤 1
- **节点**: [节点名称]
- **描述**: [此步骤的作用]
- **输入数据**: [输入数据来源]
- **输出数据**: [输出数据去向]

## 设计理由
[Flow编排的设计理由]

编排要求：
1. 只能使用已识别的Node列表中的Node
2. 确保数据流的完整性和逻辑性
3. 使用Action驱动的转换逻辑
4. 考虑错误处理和分支逻辑
5. Mermaid图要清晰展示所有连接和数据流
6. 确保每个Node都有明确的前置和后置关系

重要：请严格按照上述Markdown格式输出，不要输出JSON格式！直接输出完整的Markdown文档。"""

            # 使用系统提示词调用LLM
            result = await call_llm_async(prompt, is_json=False, system_prompt=system_prompt)
            return result
        except Exception as e:
            raise Exception(f"LLM调用失败: {str(e)}")
    

