"""
Architecture Agent 文件输出工具

提供统一的文件输出功能，在每个Node的post阶段调用。
根据阶段和数据自动生成相应的Markdown文件。
"""

import time
import json
from typing import Dict, Any, Optional


def generate_stage_file(stage: str, data: Any, shared: Dict[str, Any]) -> bool:
    """
    根据阶段生成相应的输出文件
    
    Args:
        stage: 阶段名称 (agent_analysis, node_identification, flow_design, data_structure, node_design)
        data: 该阶段的数据
        shared: 共享变量字典
        
    Returns:
        bool: 是否成功生成文件
    """
    try:
        # 导入NodeOutput
        from agent.nodes.node_output import NodeOutput
        
        # 生成文件内容
        filename = _get_filename(stage)
        content = _generate_content(stage, data)
        
        if not content:
            print(f"⚠️ {stage}阶段无内容可生成")
            return False
        
        # 准备文件数据
        files_to_generate = [
            {
                "filename": filename,
                "content": content
            }
        ]
        
        # 更新shared变量
        shared["files_to_generate"] = files_to_generate
        
        # 创建NodeOutput并生成文件
        node_output = NodeOutput(output_dir="output")
        result = node_output.generate_files_directly(files_to_generate)
        
        if result["status"] == "success":
            # 更新或初始化生成的文件信息
            if "generated_files" not in shared:
                shared["generated_files"] = []
            shared["generated_files"].extend(result["generated_files"])
            shared["output_directory"] = result["output_directory"]
            
            print(f"📄 {stage}阶段文件已生成: {result['output_directory']}/{filename}")
            return True
        else:
            print(f"⚠️ {stage}阶段文件生成失败: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"⚠️ {stage}阶段文件生成出错: {str(e)}")
        return False


def _get_filename(stage: str) -> str:
    """获取阶段对应的文件名"""
    filename_mapping = {
        "agent_analysis": "01_agent_analysis.md",
        "node_identification": "02_identified_nodes.md",
        "flow_design": "03_flow_design.md",
        "data_structure": "04_data_structure.md",
        "node_design": "05_node_design.md",
        "document_generation": "06_agent_design_complete.md"
    }
    return filename_mapping.get(stage, f"{stage}.md")


def _generate_content(stage: str, data: Any) -> str:
    """根据阶段和数据生成文件内容"""
    if stage == "agent_analysis":
        return _generate_agent_analysis_content(data)
    elif stage == "node_identification":
        return _generate_node_identification_content(data)
    elif stage == "flow_design":
        return _generate_flow_design_content(data)
    elif stage == "data_structure":
        return _generate_data_structure_content(data)
    elif stage == "node_design":
        return _generate_node_design_content(data)
    elif stage == "document_generation":
        return data  # 文档生成阶段直接返回生成的文档内容
    else:
        return f"# {stage.title()} 结果\n\n```json\n{json.dumps(data, indent=2, ensure_ascii=False)}\n```"


def _generate_agent_analysis_content(agent_analysis: Dict[str, Any]) -> str:
    """生成Agent分析文件内容"""
    content = f"""# Agent需求分析结果

## Agent基本信息
- **Agent类型**: {agent_analysis.get('agent_type', 'Unknown')}
- **Agent目的**: {agent_analysis.get('agent_purpose', 'Unknown')}
- **处理模式**: {agent_analysis.get('processing_pattern', 'Unknown')}

## 核心功能
"""
    
    core_functions = agent_analysis.get('core_functions', [])
    for i, func in enumerate(core_functions, 1):
        if isinstance(func, dict):
            content += f"""
### {i}. {func.get('function_name', 'Unknown')}
- **描述**: {func.get('description', '')}
- **复杂度**: {func.get('complexity', 'Unknown')}
- **优先级**: {func.get('priority', 'Unknown')}
"""
    
    content += f"""
## 输入输出类型
- **输入类型**: {', '.join(agent_analysis.get('input_types', []))}
- **输出类型**: {', '.join(agent_analysis.get('output_types', []))}

## 技术挑战
"""
    for challenge in agent_analysis.get('key_challenges', []):
        content += f"- {challenge}\n"
    
    content += f"""
## 成功标准
"""
    for criteria in agent_analysis.get('success_criteria', []):
        content += f"- {criteria}\n"
    
    content += f"""
---
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return content


def _generate_node_identification_content(identified_nodes: list) -> str:
    """生成Node识别文件内容"""
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
    
    # 统计Node类型
    node_types = {}
    for node in identified_nodes:
        if isinstance(node, dict):
            node_type = node.get('node_type', 'Unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
    
    content += f"""
## Node类型统计
"""
    for node_type, count in node_types.items():
        content += f"- **{node_type}**: {count}个\n"
    
    content += f"""
---
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return content


def _generate_flow_design_content(flow_design: Dict[str, Any]) -> str:
    """生成Flow设计文件内容"""
    content = f"""# Flow设计结果

## Flow概述
- **Flow名称**: {flow_design.get('flow_name', 'Unknown')}
- **Flow描述**: {flow_design.get('flow_description', '')}
- **起始节点**: {flow_design.get('start_node', 'Unknown')}

## Flow图表

```mermaid
{flow_design.get('mermaid_diagram', '// Mermaid图表生成失败')}
```

## 节点连接关系
"""
    
    connections = flow_design.get('connections', [])
    for i, conn in enumerate(connections, 1):
        content += f"""
### 连接 {i}
- **源节点**: {conn.get('from_node', 'Unknown')}
- **目标节点**: {conn.get('to_node', 'Unknown')}
- **触发Action**: {conn.get('action', 'default')}
- **转换条件**: {conn.get('condition', '')}
- **传递数据**: {conn.get('data_passed', '')}
"""
    
    content += f"""
## 执行流程
"""
    
    execution_flow = flow_design.get('execution_flow', [])
    for step in execution_flow:
        content += f"""
### 步骤 {step.get('step', 'Unknown')}
- **节点**: {step.get('node', 'Unknown')}
- **描述**: {step.get('description', '')}
- **输入数据**: {step.get('input_data', '')}
- **输出数据**: {step.get('output_data', '')}
"""
    
    content += f"""
## 设计理由
{flow_design.get('design_rationale', '')}

---
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return content


def _generate_data_structure_content(data_structure: Dict[str, Any]) -> str:
    """生成数据结构文件内容"""
    content = f"""# 数据结构设计结果

## 整体描述
{data_structure.get('shared_structure_description', '')}

## Shared字段定义
"""
    
    shared_fields = data_structure.get('shared_fields', [])
    for field in shared_fields:
        content += f"""
### {field.get('field_name', 'Unknown')}
- **数据类型**: {field.get('data_type', 'Unknown')}
- **描述**: {field.get('description', '')}
- **用途**: {field.get('purpose', '')}
- **读取节点**: {', '.join(field.get('read_by_nodes', []))}
- **写入节点**: {', '.join(field.get('written_by_nodes', []))}
- **是否必需**: {'是' if field.get('required', False) else '否'}
- **示例值**: `{field.get('example_value', 'N/A')}`
"""
    
    content += f"""
## 数据流模式
"""
    
    data_flow_patterns = data_structure.get('data_flow_patterns', [])
    for pattern in data_flow_patterns:
        content += f"""
### {pattern.get('pattern_name', 'Unknown')}
- **描述**: {pattern.get('description', '')}
- **涉及字段**: {', '.join(pattern.get('involved_fields', []))}
- **流转顺序**: {' → '.join(pattern.get('flow_sequence', []))}
"""
    
    content += f"""
## Shared存储示例结构

```json
{json.dumps(data_structure.get('shared_example', {}), indent=2, ensure_ascii=False)}
```

---
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return content


def _generate_node_design_content(detailed_nodes: list) -> str:
    """生成Node设计文件内容"""
    content = f"""# Node详细设计结果

## 概述
共设计了{len(detailed_nodes)}个Node的详细实现：

"""
    
    for i, node in enumerate(detailed_nodes, 1):
        if isinstance(node, dict):
            design_details = node.get('design_details', {})
            prep_stage = design_details.get('prep_stage', {})
            exec_stage = design_details.get('exec_stage', {})
            post_stage = design_details.get('post_stage', {})
            
            content += f"""## {i}. {node.get('node_name', 'Unknown')}

### 基本信息
- **Node类型**: {node.get('node_type', 'Unknown')}
- **目的**: {node.get('purpose', '')}

### Prep阶段设计
- **描述**: {prep_stage.get('description', '')}
- **从shared读取**: {', '.join(prep_stage.get('input_from_shared', []))}
- **验证逻辑**: {prep_stage.get('validation_logic', '')}
- **准备步骤**: {'; '.join(prep_stage.get('preparation_steps', []))}

### Exec阶段设计
- **描述**: {exec_stage.get('description', '')}
- **核心逻辑**: {exec_stage.get('core_logic', '')}
- **处理步骤**: {'; '.join(exec_stage.get('processing_steps', []))}
- **错误处理**: {exec_stage.get('error_handling', '')}

### Post阶段设计
- **描述**: {post_stage.get('description', '')}
- **结果处理**: {post_stage.get('result_processing', '')}
- **更新shared**: {', '.join(post_stage.get('shared_updates', []))}
- **Action逻辑**: {post_stage.get('action_logic', '')}
- **可能Actions**: {', '.join(post_stage.get('possible_actions', []))}

### 数据访问
- **读取字段**: {', '.join(node.get('data_access', {}).get('reads_from_shared', []))}
- **写入字段**: {', '.join(node.get('data_access', {}).get('writes_to_shared', []))}

### 重试配置
- **最大重试**: {node.get('retry_config', {}).get('max_retries', 0)}次
- **等待时间**: {node.get('retry_config', {}).get('wait', 0)}秒

"""
    
    content += f"""
---
*生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
"""
    return content
