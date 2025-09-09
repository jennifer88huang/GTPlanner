"""
数据结构设计节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/data_structure_design_node.py
"""


class AgentsDeepDesignDataStructureDesignNodeTemplates:
    """数据结构设计节点提示词模板类"""
    
    @staticmethod
    def get_data_structure_design_zh() -> str:
        """中文版本的数据结构设计提示词"""
        return """你是一位精通PocketFlow框架的数据架构专家。

你的唯一任务是基于下方提供的上下文，设计一个简洁、高效的`shared`共享数据字典，并严格按照指定的JSON格式输出。

**上下文信息：**
- **Agent分析结果：** {analysis_markdown}
- **Node识别结果：** {nodes_markdown}
- **Flow设计：** {flow_markdown}
- **用户需求：** {user_requirements}
- **项目规划：** {short_planning}
- **技术调研结果：** {research_info}
- **推荐工具：** {tools_info}

**核心指令：**
1.  **聚焦于`shared`结构**：仅定义在Node之间传递的核心字段。
2.  **保持简洁**：所有描述性文字（如description, purpose）都应简明扼要，控制在25个字以内。
3.  **严格JSON输出**：最终输出必须是一个完整的、无任何额外注释或解释的JSON对象。

**请严格按照以下JSON格式输出：**
{{
    "shared_structure_description": "一句话描述该`shared`结构的总体用途。",
    "shared_fields": [
        {{
            "field_name": "字段名称",
            "data_type": "核心数据类型 (例如: str, int, list[dict], bool)",
            "description": "字段的简短描述",
            "purpose": "此字段在流程中的核心作用",
            "constraints": "关键约束条件 (例如: 'required', 'optional', 'not null', 'enum: [A, B]')",
            "io_nodes": {{
                "written_by": ["写入此字段的Node"],
                "read_by": ["读取此字段的Node_A", "读取此字段的Node_B"]
            }},
            "example_value": "一个清晰、简单的值示例"
        }}
    ],
    "shared_example": {{
        "comment": "展示`shared`对象在流程关键节点的一个完整示例。",
        "data": {{
            "field_name_1": "示例值",
            "field_name_2": []
        }}
    }}
}}"""
    
    @staticmethod
    def get_data_structure_design_en() -> str:
        """English version of data structure design prompt"""
        return """You are a professional data architecture designer specializing in designing shared storage data structures for the pocketflow framework.

Please design a complete shared data structure based on the following information:

**Agent Analysis Results:**
{analysis_markdown}

**Node Identification Results:**
{nodes_markdown}

**Flow Design:**
{flow_markdown}

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Technical Research Results:**
{research_info}

**Recommended Tools:**
{tools_info}

Please perform the following data structure design work:

1. **Core Data Model Design**:
   - Design core data structures supporting the entire Agent operation
   - Define data entities, attributes, and relationships
   - Ensure data model integrity and consistency

2. **Shared Dictionary Structure Design**:
   - Design pocketflow's shared storage structure
   - Define shared data formats between various Nodes
   - Ensure efficiency and accuracy of data transfer

3. **Input/Output Data Formats**:
   - Define standard formats for system input data
   - Design intermediate data formats for various processing stages
   - Standardize final output data structure and format

4. **State Management Data Structures**:
   - Design data structures for Flow execution states
   - Define state information needed for error handling and recovery
   - Ensure traceability and recoverability of state data

5. **Configuration and Metadata Structures**:
   - Design data structures for system configuration parameters
   - Define metadata formats for Nodes and Flows
   - Ensure configuration flexibility and maintainability

6. **Performance Optimization Data Structures**:
   - Design cache data structures and strategies
   - Optimize data formats for large data volume processing
   - Consider memory usage and access efficiency

Please strictly output the data structure design in the following JSON format:

{{
    "shared_structure_description": "Overall description of shared storage",
    "shared_fields": [
        {{
            "field_name": "field name",
            "data_type": "data type (e.g., str, dict, list, etc.)",
            "description": "field description",
            "purpose": "field purpose",
            "read_by_nodes": ["list of nodes that read this field"],
            "written_by_nodes": ["list of nodes that write this field"],
            "example_value": "example value or structure",
            "required": true/false
        }}
    ],
    "data_flow_patterns": [
        {{
            "pattern_name": "data flow pattern name",
            "description": "data flow description",
            "involved_fields": ["involved fields"],
            "flow_sequence": ["data flow sequence"]
        }}
    ],
    "shared_example": {{
        "field1": "example value 1",
        "field2": {{}},
        "field3": []
    }}
}}

For data structure design, please provide:
- Complete data structure definitions (JSON Schema format)
- Detailed field descriptions and constraint conditions
- Data flow and transformation rules
- Data validation and error handling mechanisms
- Performance optimization recommendations

Please output data structure design results in a structured format, ensuring design completeness and practicality."""
    
    @staticmethod
    def get_data_structure_design_ja() -> str:
        """日本語版のデータ構造設計プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_data_structure_design_es() -> str:
        """Versión en español del prompt de diseño de estructura de datos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_data_structure_design_fr() -> str:
        """Version française du prompt de conception de structure de données"""
        return """# TODO: Ajouter le prompt en français"""
