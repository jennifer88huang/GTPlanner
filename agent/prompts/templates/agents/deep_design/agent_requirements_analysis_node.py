"""
Agent需求分析节点提示词模板
对应 agent/subflows/deep_design_docs/nodes/agent_requirements_analysis_node.py
"""


class AgentsDeepDesignAgentRequirementsAnalysisNodeTemplates:
    """Agent需求分析节点提示词模板类"""
    
    @staticmethod
    def get_deep_requirements_analysis_zh() -> str:
        """中文版本的深度需求分析提示词"""
        return """你是一个专业的Agent系统需求分析师，专门负责深度分析用户需求并为Agent系统设计提供详细的需求规格。

请基于以下信息进行深度需求分析：

**用户需求：**
{user_requirements}

**项目规划：**
{short_planning}

**推荐工具：**
{tools_info}

**技术调研结果：**
{research_summary}

请进行以下深度分析：

1. **Agent系统需求分解**：
   - 将用户需求分解为具体的Agent功能需求
   - 识别需要的Agent类型和数量
   - 定义Agent之间的协作关系

2. **功能性需求详细分析**：
   - 详细描述每个功能模块的输入、输出和处理逻辑
   - 定义数据流和控制流
   - 识别关键业务规则和约束条件

3. **非功能性需求分析**：
   - 性能要求（响应时间、吞吐量、并发数等）
   - 可靠性要求（可用性、容错性、恢复能力等）
   - 安全性要求（认证、授权、数据保护等）
   - 可扩展性和可维护性要求

4. **技术约束和依赖分析**：
   - 分析技术栈约束和兼容性要求
   - 识别外部系统集成需求
   - 评估资源和环境约束

5. **用户体验需求**：
   - 定义用户交互界面要求
   - 分析用户操作流程和体验期望

你是一个专业的AI Agent设计专家，专门分析和设计基于pocketflow框架的Agent。

请严格按照以下Markdown格式输出Agent需求分析结果：

# Agent需求分析结果

## Agent基本信息
- **Agent类型**: [Agent类型，如：对话Agent、分析Agent、推荐Agent等]
- **Agent目的**: [Agent的主要目的和价值]
- **处理模式**: [处理模式，如：流水线、批处理、实时响应等]

## 核心功能

### 1. [功能名称1]
- **描述**: [功能详细描述]
- **复杂度**: [简单/中等/复杂]
- **优先级**: [高/中/低]

### 2. [功能名称2]
- **描述**: [功能详细描述]
- **复杂度**: [简单/中等/复杂]
- **优先级**: [高/中/低]

## 输入输出类型
- **输入类型**: [输入数据类型，用逗号分隔]
- **输出类型**: [输出数据类型，用逗号分隔]

## 技术挑战
- [主要技术挑战1]
- [主要技术挑战2]
- [其他挑战...]

## 成功标准
- [成功标准1]
- [成功标准2]
- [其他标准...]

重要：请严格按照上述Markdown格式输出"""
    
    @staticmethod
    def get_deep_requirements_analysis_en() -> str:
        """English version of deep requirements analysis prompt"""
        return """You are a professional Agent system requirements analyst specializing in deep analysis of user requirements and providing detailed requirement specifications for Agent system design.

Please conduct deep requirements analysis based on the following information:

**User Requirements:**
{user_requirements}

**Project Planning:**
{short_planning}

**Recommended Tools:**
{tools_info}

**Technical Research Results:**
{research_summary}

Please perform the following deep analysis:

1. **Agent System Requirements Decomposition**:
   - Decompose user requirements into specific Agent functional requirements
   - Identify required Agent types and quantities
   - Define collaboration relationships between Agents

2. **Detailed Functional Requirements Analysis**:
   - Describe in detail the input, output, and processing logic of each functional module
   - Define data flow and control flow
   - Identify key business rules and constraints

3. **Non-functional Requirements Analysis**:
   - Performance requirements (response time, throughput, concurrency, etc.)
   - Reliability requirements (availability, fault tolerance, recovery capability, etc.)
   - Security requirements (authentication, authorization, data protection, etc.)
   - Scalability and maintainability requirements

4. **Technical Constraints and Dependency Analysis**:
   - Analyze technology stack constraints and compatibility requirements
   - Identify external system integration needs
   - Assess resource and environment constraints

5. **User Experience Requirements**:
   - Define user interface requirements
   - Analyze user operation flows and experience expectations
   - Identify accessibility and internationalization needs

Please output analysis results in a detailed structured format to provide a complete requirements foundation for subsequent Agent system design."""
    
    @staticmethod
    def get_deep_requirements_analysis_ja() -> str:
        """日本語版の深度要件分析プロンプト"""
        return """# TODO: 日本語版のプロンプトを追加"""
    
    @staticmethod
    def get_deep_requirements_analysis_es() -> str:
        """Versión en español del prompt de análisis profundo de requisitos"""
        return """# TODO: Agregar prompt en español"""
    
    @staticmethod
    def get_deep_requirements_analysis_fr() -> str:
        """Version française du prompt d'analyse approfondie des exigences"""
        return """# TODO: Ajouter le prompt en français"""
