"""
Multilingual prompt template system for GTPlanner.

This module provides a flexible system for managing prompt templates
across different languages with proper fallback mechanisms.
"""

from enum import Enum
from typing import Any, Dict, Optional

from utils.language_detection import SupportedLanguage
from utils.prompt_templates_extended import ExtendedPromptTemplates


class PromptType(Enum):
    """Types of prompts used in the system."""

    GENERATE_STEPS = "generate_steps"
    OPTIMIZE_STEPS = "optimize_steps"
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    DESIGN_OPTIMIZATION = "design_optimization"
    DOCUMENTATION_GENERATION = "documentation_generation"


class PromptTemplateManager:
    """Manages multilingual prompt templates."""

    def __init__(self, default_language: SupportedLanguage = SupportedLanguage.ENGLISH):
        """Initialize the prompt template manager.

        Args:
            default_language: The default language for fallback
        """
        self.default_language = default_language
        self._templates = self._load_templates()

    def _load_templates(self) -> Dict[PromptType, Dict[SupportedLanguage, str]]:
        """Load all prompt templates organized by type and language.

        Returns:
            Dictionary of prompt templates
        """
        return {
            PromptType.GENERATE_STEPS: {
                SupportedLanguage.ENGLISH: self._get_generate_steps_en(),
                SupportedLanguage.CHINESE: self._get_generate_steps_zh(),
                SupportedLanguage.SPANISH: self._get_generate_steps_es(),
                SupportedLanguage.FRENCH: self._get_generate_steps_fr(),
                SupportedLanguage.JAPANESE: self._get_generate_steps_ja(),
            },
            PromptType.OPTIMIZE_STEPS: {
                SupportedLanguage.ENGLISH: self._get_optimize_steps_en(),
                SupportedLanguage.CHINESE: self._get_optimize_steps_zh(),
                SupportedLanguage.SPANISH: self._get_optimize_steps_es(),
                SupportedLanguage.FRENCH: self._get_optimize_steps_fr(),
                SupportedLanguage.JAPANESE: self._get_optimize_steps_ja(),
            },
            PromptType.REQUIREMENTS_ANALYSIS: {
                SupportedLanguage.ENGLISH: self._get_requirements_analysis_en(),
                SupportedLanguage.CHINESE: self._get_requirements_analysis_zh(),
                SupportedLanguage.SPANISH: self._get_requirements_analysis_es(),
                SupportedLanguage.FRENCH: self._get_requirements_analysis_fr(),
                SupportedLanguage.JAPANESE: self._get_requirements_analysis_ja(),
            },
            PromptType.DESIGN_OPTIMIZATION: {
                SupportedLanguage.ENGLISH: self._get_design_optimization_en(),
                SupportedLanguage.CHINESE: self._get_design_optimization_zh(),
                SupportedLanguage.SPANISH: self._get_design_optimization_es(),
                SupportedLanguage.FRENCH: self._get_design_optimization_fr(),
                SupportedLanguage.JAPANESE: self._get_design_optimization_ja(),
            },
        }

    def get_template(self, prompt_type: PromptType, language: SupportedLanguage) -> str:
        """Get a prompt template for the specified type and language.

        Args:
            prompt_type: The type of prompt needed
            language: The target language

        Returns:
            The prompt template string
        """
        templates_for_type = self._templates.get(prompt_type, {})

        # Try to get the requested language
        template = templates_for_type.get(language)

        # Fallback to default language if not found
        if template is None:
            template = templates_for_type.get(self.default_language)

        # Final fallback to English if default is not available
        if template is None:
            template = templates_for_type.get(SupportedLanguage.ENGLISH)

        if template is None:
            raise ValueError(
                f"No template found for {prompt_type} in any supported language"
            )

        return template

    def _get_generate_steps_en(self) -> str:
        """English template for generating steps."""
        return """# Role
You are an experienced system architect and workflow designer.

# Task
Based on the user's requirements and optional available tools/MCP list, generate a clear, concise step-by-step workflow to implement the requirements.

# Input
1. **User Requirements:**
   ```
   {req}
   ```
2. **Available Tools/MCP List (Optional):**
   ```
   ```

# Output Requirements
1. **Step-by-step Workflow:**
   * List clear, numbered steps.
   * Each step should describe a core action/phase.
   * If suitable tools are available in the MCP list, specify which tool to use in the step. Format: `Step X: [Action Description] (Use: [Tool Name])`.
   * If no perfect match exists or for generality, steps should be generic enough to allow users to integrate their own services later.
   * Mark optional steps (e.g., use `(Optional)` marker).
   * Suggest parallel processing steps when appropriate.
2. **Design Considerations (Optional but recommended):**
   * Briefly explain key design decisions or flexibility considerations, such as data format conversion, error handling approaches, etc.

# Example (for understanding output format and style)
**Example User Requirements:** YouTube Video Summarizer: Summarize videos into Topics and QA.
**Example Available Tools/MCP List:**
youtube_audio_fetch: Get YouTube video audio
ASR_MCP: Convert audio to text

**Expected Output Example:**
1. Fetch: Get YouTube video content (If input is video link, consider using youtube_audio_fetch MCP to get audio; if direct audio file, skip this tool).
2. ToText (Optional): If previous step got audio, convert audio to text (consider using ASR_MCP). If input is already text, skip this step.
3. Extract: Extract key topics and potential questions from text.
4. Process:
   * Process each Topic in parallel: Generate summary for each Topic.
   * Process each Question in parallel: Generate or locate answer highlights for each Question.
5. Output: Generate structured output, such as JSON or visual HTML infographic, containing Topic summaries and QA pairs.
---

Please generate the workflow based on the following actual input:

**User Requirements:**
{req}

**Available Tools/MCP List:**


**Output: Step-by-step Workflow:** (Only output the step-by-step workflow, no additional explanations needed)
"""

    def _get_generate_steps_zh(self) -> str:
        """Chinese template for generating steps."""
        return """# 角色
你是一个经验丰富的系统架构师和工作流设计师。

# 任务
根据用户提供的【用户需求】和可选的【可用工具/MCP清单】，生成一个清晰、简洁的步骤化流程，用于实现该需求。

# 输入
1. **用户需求：**
   ```
   {req}
   ```
2. **可用工具/MCP清单 (可选)：**
   ```
   ```

# 输出要求
1. **步骤化流程：**
   * 列出清晰的、序号化的步骤。
   * 每个步骤应描述一个核心动作/阶段。
   * 如果【可用工具/MCP清单】中有合适的工具，请在步骤中指明使用哪个工具。格式如：`步骤X：[动作描述] (使用：[工具名称])`。
   * 如果无完全匹配工具，或为了通用性，步骤应足够通用，允许用户后续集成自己的服务。
   * 指明可选步骤（例如，使用 `(可选)` 标记）。
   * 如果合适，可以建议并行处理的步骤。
2. **设计考虑 (可选，但推荐)：**
   * 简要说明一些关键的设计决策或灵活性考虑，例如数据格式转换、错误处理思路等。

# 示例（用于理解输出格式和风格）
**用户需求示例：** YouTube视频总结器：将视频总结为Topic和QA。
**可用工具/MCP清单示例：**
youtube_audio_fetch: 获取YouTube视频的音频
ASR_MCP: 将音频转换为文本

**期望输出示例：**
1. Fetch: 获取YouTube视频内容 (如果输入是视频链接，可考虑使用 youtube_audio_fetch MCP 获取音频；如果直接是音频文件，则跳过此工具)。
2. ToText (可选): 如果上一步获取的是音频，将音频转换为文本 (可考虑使用 ASR_MCP)。如果输入已是文本，则跳过此步骤。
3. Extract: 从文本中提取关键主题 (Topics) 和潜在问题 (Questions)。
4. Process:
   * 并行处理每个Topic：为每个Topic生成总结。
   * 并行处理每个Question：为每个Question生成或定位答案的亮点。
5. Output: 生成结构化的输出，例如JSON或可视化的HTML信息图，包含Topic总结和QA对。
---

请根据以下实际输入生成流程：

**用户需求：**
{req}

**可用工具/MCP清单：**


**输出：步骤化流程：**(只输出步骤化流程，不需要有多余的解释)
"""

    def _get_generate_steps_es(self) -> str:
        """Spanish template for generating steps."""
        return """# Rol
Eres un arquitecto de sistemas experimentado y diseñador de flujos de trabajo.

# Tarea
Basándote en los requisitos del usuario y la lista opcional de herramientas/MCP disponibles, genera un flujo de trabajo paso a paso claro y conciso para implementar los requisitos.

# Entrada
1. **Requisitos del Usuario:**
   ```
   {req}
   ```
2. **Lista de Herramientas/MCP Disponibles (Opcional):**
   ```
   ```

# Requisitos de Salida
1. **Flujo de Trabajo Paso a Paso:**
   * Lista pasos claros y numerados.
   * Cada paso debe describir una acción/fase central.
   * Si hay herramientas adecuadas en la lista MCP, especifica qué herramienta usar. Formato: `Paso X: [Descripción de Acción] (Usar: [Nombre de Herramienta])`.
   * Si no hay coincidencia perfecta o para generalidad, los pasos deben ser lo suficientemente genéricos para permitir a los usuarios integrar sus propios servicios más tarde.
   * Marca pasos opcionales (ej., usar marcador `(Opcional)`).
   * Sugiere pasos de procesamiento paralelo cuando sea apropiado.

**Requisitos del Usuario:**
{req}

**Lista de Herramientas/MCP Disponibles:**


**Salida: Flujo de Trabajo Paso a Paso:** (Solo salida del flujo de trabajo paso a paso, no se necesitan explicaciones adicionales)
"""

    def _get_generate_steps_fr(self) -> str:
        """French template for generating steps."""
        return """# Rôle
Vous êtes un architecte système expérimenté et concepteur de flux de travail.

# Tâche
Basé sur les exigences de l'utilisateur et la liste optionnelle d'outils/MCP disponibles, générez un flux de travail étape par étape clair et concis pour implémenter les exigences.

# Entrée
1. **Exigences de l'Utilisateur:**
   ```
   {req}
   ```
2. **Liste d'Outils/MCP Disponibles (Optionnel):**
   ```
   ```

# Exigences de Sortie
1. **Flux de Travail Étape par Étape:**
   * Listez des étapes claires et numérotées.
   * Chaque étape doit décrire une action/phase centrale.
   * S'il y a des outils appropriés dans la liste MCP, spécifiez quel outil utiliser. Format: `Étape X: [Description d'Action] (Utiliser: [Nom d'Outil])`.
   * S'il n'y a pas de correspondance parfaite ou pour la généralité, les étapes doivent être assez génériques pour permettre aux utilisateurs d'intégrer leurs propres services plus tard.
   * Marquez les étapes optionnelles (ex., utiliser le marqueur `(Optionnel)`).
   * Suggérez des étapes de traitement parallèle quand approprié.

**Exigences de l'Utilisateur:**
{req}

**Liste d'Outils/MCP Disponibles:**


**Sortie: Flux de Travail Étape par Étape:** (Seulement la sortie du flux de travail étape par étape, aucune explication supplémentaire nécessaire)
"""

    def _get_generate_steps_ja(self) -> str:
        """Japanese template for generating steps."""
        return """# 役割
あなたは経験豊富なシステムアーキテクトとワークフローデザイナーです。

# タスク
ユーザーの要件とオプションの利用可能なツール/MCPリストに基づいて、要件を実装するための明確で簡潔なステップバイステップのワークフローを生成してください。

# 入力
1. **ユーザー要件:**
   ```
   {req}
   ```
2. **利用可能なツール/MCPリスト（オプション）:**
   ```
   ```

# 出力要件
1. **ステップバイステップワークフロー:**
   * 明確で番号付きのステップをリストしてください。
   * 各ステップは中核的なアクション/フェーズを記述する必要があります。
   * MCPリストに適切なツールがある場合、どのツールを使用するかを指定してください。形式: `ステップX: [アクション説明] (使用: [ツール名])`.
   * 完全な一致がない場合や汎用性のために、ステップは後でユーザーが独自のサービスを統合できるよう十分に汎用的である必要があります。
   * オプションのステップをマークしてください（例：`（オプション）`マーカーを使用）。
   * 適切な場合は並列処理ステップを提案してください。

**ユーザー要件:**
{req}

**利用可能なツール/MCPリスト:**


**出力: ステップバイステップワークフロー:** (ステップバイステップワークフローの出力のみ、追加の説明は不要)
"""

    def _get_optimize_steps_en(self) -> str:
        """English template for optimizing steps."""
        return """# Role
You are an experienced system architect and workflow designer, currently helping me optimize and refine a preliminary workflow plan.

# Task
Based on my feedback and modification suggestions, adjust and update the previously generated workflow. Ensure the modified workflow remains clear, coherent, meets my latest requirements, and preserves reasonable parts of the original workflow.

# Context Information
1. **Previously Generated Workflow (Version V{prev_version}):**
   ```
   {steps}
   ```
   *(V{prev_version} indicates the current version number, e.g., V1, V2...)*

2. **My Feedback/New Requirements for Version V{prev_version}:**
   ```
   {feedback}
   ```
   *(e.g., "Please add a data cleaning step between step 2 and step 3." or "I think extracting Topics and Questions can be merged into one step." or "In addition to HTML output format, I want to add a JSON format.")*

# Output Requirements (Only output the complete modified workflow, no additional explanations needed)
   **Complete Modified Workflow**
   * Clearly list all steps, including unchanged, modified, and newly added steps.
   * Ensure the workflow's logic and completeness.
"""

    def _get_optimize_steps_zh(self) -> str:
        """Chinese template for optimizing steps."""
        return """# 角色
你是一个经验丰富的系统架构师和工作流设计师，目前正在帮助我优化和完善一个已经初步拟定的流程方案。

# 任务
根据我提出的【修改意见】，调整和更新【先前生成的流程】。请确保修改后的流程仍然清晰、连贯、满足我的最新要求，并尽可能保留原流程中合理的部分。

# 上下文信息
1. **先前生成的流程 (版本 V{prev_version})：**
   ```
   {steps}
   ```
   *(这里的 V{prev_version} 表示当前是第几版，例如 V1, V2...)*

2. **我对版本 V{prev_version} 的修改意见/新要求：**
   ```
   {feedback}
   ```
   *(例如："请在第二步和第三步之间增加一个数据清洗步骤。" 或者 "我觉得提取Topic和Question可以合并为一个步骤。" 或者 "输出格式除了HTML，我还想增加一个JSON格式。")*

# 输出要求(仅输出修改后的完整流程，不需要有多余的解释)
   **修改后的完整流程**
   * 清晰地列出所有步骤，包括未修改、已修改以及新增的步骤。
   * 请确保流程的逻辑性和完整性。
"""

    def _get_optimize_steps_es(self) -> str:
        """Spanish template for optimizing steps."""
        return """# Rol
Eres un arquitecto de sistemas experimentado y diseñador de flujos de trabajo, actualmente ayudándome a optimizar y refinar un plan de flujo de trabajo preliminar.

# Tarea
Basándote en mis comentarios y sugerencias de modificación, ajusta y actualiza el flujo de trabajo generado previamente. Asegúrate de que el flujo de trabajo modificado permanezca claro, coherente, cumpla con mis últimos requisitos y preserve las partes razonables del flujo de trabajo original.

# Información de Contexto
1. **Flujo de Trabajo Generado Previamente (Versión V{prev_version}):**
   ```
   {steps}
   ```

2. **Mis Comentarios/Nuevos Requisitos para la Versión V{prev_version}:**
   ```
   {feedback}
   ```

# Requisitos de Salida (Solo salida del flujo de trabajo modificado completo, no se necesitan explicaciones adicionales)
   **Flujo de Trabajo Modificado Completo**
   * Lista claramente todos los pasos, incluyendo pasos sin cambios, modificados y recién agregados.
   * Asegura la lógica y completitud del flujo de trabajo.
"""

    def _get_optimize_steps_fr(self) -> str:
        """French template for optimizing steps."""
        return """# Rôle
Vous êtes un architecte système expérimenté et concepteur de flux de travail, m'aidant actuellement à optimiser et affiner un plan de flux de travail préliminaire.

# Tâche
Basé sur mes commentaires et suggestions de modification, ajustez et mettez à jour le flux de travail généré précédemment. Assurez-vous que le flux de travail modifié reste clair, cohérent, répond à mes dernières exigences et préserve les parties raisonnables du flux de travail original.

# Informations de Contexte
1. **Flux de Travail Généré Précédemment (Version V{prev_version}):**
   ```
   {steps}
   ```

2. **Mes Commentaires/Nouvelles Exigences pour la Version V{prev_version}:**
   ```
   {feedback}
   ```

# Exigences de Sortie (Seulement la sortie du flux de travail modifié complet, aucune explication supplémentaire nécessaire)
   **Flux de Travail Modifié Complet**
   * Listez clairement toutes les étapes, y compris les étapes inchangées, modifiées et nouvellement ajoutées.
   * Assurez la logique et la complétude du flux de travail.
"""

    def _get_optimize_steps_ja(self) -> str:
        """Japanese template for optimizing steps."""
        return """# 役割
あなたは経験豊富なシステムアーキテクトとワークフローデザイナーで、現在私の予備的なワークフロープランの最適化と改良を手伝っています。

# タスク
私のフィードバックと修正提案に基づいて、以前に生成されたワークフローを調整し更新してください。修正されたワークフローが明確で一貫性があり、私の最新の要件を満たし、元のワークフローの合理的な部分を保持することを確認してください。

# コンテキスト情報
1. **以前に生成されたワークフロー（バージョンV{prev_version}）:**
   ```
   {steps}
   ```

2. **バージョンV{prev_version}に対する私のフィードバック/新しい要件:**
   ```
   {feedback}
   ```

# 出力要件（完全な修正されたワークフローの出力のみ、追加の説明は不要）
   **完全な修正されたワークフロー**
   * 変更されていない、修正された、新しく追加されたステップを含むすべてのステップを明確にリストしてください。
   * ワークフローの論理性と完全性を確保してください。
"""

    def _get_requirements_analysis_en(self) -> str:
        """English template for requirements analysis."""
        return ExtendedPromptTemplates.get_requirements_analysis_en()

    def _get_requirements_analysis_zh(self) -> str:
        """Chinese template for requirements analysis."""
        return ExtendedPromptTemplates.get_requirements_analysis_zh()

    def _get_requirements_analysis_es(self) -> str:
        """Spanish template for requirements analysis."""
        return ExtendedPromptTemplates.get_requirements_analysis_es()

    def _get_requirements_analysis_fr(self) -> str:
        """French template for requirements analysis."""
        return ExtendedPromptTemplates.get_requirements_analysis_fr()

    def _get_requirements_analysis_ja(self) -> str:
        """Japanese template for requirements analysis."""
        return ExtendedPromptTemplates.get_requirements_analysis_ja()

    def _get_design_optimization_en(self) -> str:
        """English template for design optimization."""
        return """**You are a professional AI assistant skilled in editing and optimizing Markdown-formatted software development design documents based on user needs.** **Documents you generate must strictly adhere to a specific project design document format based on the Node/Flow architecture** (including core abstract concepts such as `Node`, `Flow`, `BatchNode`, `BatchFlow`, `AsyncNode`, `AsyncFlow`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`, collectively referred to as the "Core Design Pattern").

**Your task** is to receive:
1.  A **Previous Markdown Document** (may be empty if this is the initial creation),
2.  **Deficiencies and Optimization Guidelines** (generated from prior analysis),
3.  **User's Specific Requests and Modification Instructions for this Iteration**,
4.  **The Complete Workflow of the User's Overall Requirements**.

You must carefully analyze all inputs and output a **comprehensive, optimized Markdown document** that integrates all information. **The structure and content details of this document must strictly comply with the requirements of the "Core Design Pattern" and reference the provided example outputs and detailed explanations of this pattern.**

**Please adhere to the following rules:**

1.  **Prioritize User Instructions:** The **[User's Specific Requests and Modification Instructions for this Iteration]** have the highest priority. You must ensure these instructions are accurately executed while appropriately integrating them into the "Core Design Pattern" document structure.
2.  **Reference Optimization Guidelines:** When executing user instructions, actively reference the suggestions in the **[Deficiencies and Optimization Guidelines]**. Ensure these suggestions are applied in compliance with the "Core Design Pattern" specifications and document structure.
3.  **Integration and Update:**
    *   If the **[Previous Markdown Document]** is not empty, your task is to modify and supplement it to make it fully compliant with the "Core Design Pattern".
    *   If the **[Previous Markdown Document]** is empty, your task is to create a new document fully compliant with the "Core Design Pattern" from scratch, based on the user instructions and optimization guidelines.
    *   Ensure that actionable suggestions from the **[User's Specific Requests and Modification Instructions for this Iteration]** and the **[Deficiencies and Optimization Guidelines]** are appropriately integrated into the relevant sections of the document, strictly following the "Core Design Pattern" norms.
4.  **Ensure Completeness:** The output must be a **complete** Markdown document covering all relevant sections required by the "Core Design Pattern".
5.  **Strictly Adhere to the "Core Design Pattern" and Reflect its Design Methodology:**
    *   **Document Structure and Headings:** The output Markdown document must strictly follow the section structure and heading naming conventions (e.g., `# [Project Title]`, `## Project Requirements`, `## Utility Functions` (if applicable), `## Flow Design`, `### Flow Diagram`, `## Data Structure`, `## Node Designs`, `### N. NodeName`, etc.) used in the "Core Design Pattern" examples.
    *   **Flow Design Content & Methodology:** Flow design must clearly describe how it orchestrates one or more Nodes to achieve more complex business processes. Content must include:
        *   **Node Connections & Action-Driven Transitions:** Use explicit notation (e.g., `node_A >> node_B` indicates `node_A` transitions to `node_B` after its `post` method returns the `"default"` Action; `node_A - "action_name" >> node_B` indicates `node_A` transitions to `node_B` after returning the specific `"action_name"` Action) to show execution order and conditional branching logic based on Actions. Explain the meaning of each critical Action.
        *   **Complete Process Logic Description:** Accurately describe the start node (`start` node), any branching judgment logic, looping mechanisms (e.g., how a node might return to a previous node based on an Action).
        *   **Nested Flow (Sub-Flow) Design:** If nested Flows are used (i.e., one Flow acting as a "super node" within another Flow's graph), explain how the child Flow is invoked and managed by the parent Flow and its behavior as a Node (e.g., the child Flow executes its own `prep` and `post` methods, but its `exec` method is not executed; its `post` method receives `exec_res` as `None`; results are typically stored/passed internally within the child Flow via `shared` and ultimately influence the parent Flow's decision).
        *   **Special Considerations for Async/Parallel Flows:** For `AsyncFlow` or `AsyncParallelBatchFlow`, explain how they manage and schedule the execution of their internal async/parallel Nodes, and the overall organization and control strategy for concurrent workflows.
        *   **`### Flow Diagram`:** Must use Mermaid `flowchart TD` syntax to visualize the process accurately, clearly, and completely, including all Nodes, the main transition paths between them, and key Action labels.
    *   **Node Design Content & Methodology:** Each Node description must include its **Purpose**, **Design** (specify type e.g., `Node`, `BatchNode`, `AsyncNode`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`, etc.; *Node types should preferably be asynchronous* and include failure handling parameters such as `max_retries` (e.g., `max_retries=3`, default=1 meaning no retries) and `wait` (e.g., `wait=10` seconds, default=0)), **Data Access** (details on how the Node interacts with `shared` storage and `params`). The content must clearly reflect the following **core design principles and methodology**:
        *   **`prep(shared)` Method Design:** Clearly describe how this phase reads and preprocesses data from `shared` storage to prepare inputs for subsequent steps, and explicitly state what is returned (`prep_res`).
        *   **`exec(prep_res)` Method Design:** Clearly describe the core computational logic and business processing in this phase. **Emphasize that this phase must NOT directly access `shared` storage** to ensure purity of computation. If retries are enabled, the implementation should be idempotent. Explain how it uses `prep_res` and what it returns (`exec_res`).
        *   **`post(shared, prep_res, exec_res)` Method Design:** Clearly describe how this phase post-processes `exec_res`, writes final results or state updates back to `shared` storage, and decides & returns the next `Action` string based on the outcome (if nothing is returned, it defaults to `"default"`), which drives the Flow.
        *   **Separation of Concerns Principle:** Node design must strictly embody the separation of concerns into `prep` (data preparation & read), `exec` (core computation & logic execution), and `post` (data write & state update / Action decision), ensuring each phase has a single, well-defined responsibility.
        *   **`exec_fallback(prep_res, exc)` Method Design** (if defined): If graceful degradation logic is defined for the Node, describe how this method handles the exception `exc` after all retries of `exec` have failed and provides an alternative `exec_res` result, instead of aborting the flow.
        *   **Special Considerations for Async/Parallel Nodes:** For nodes like `AsyncNode`, `AsyncParallelBatchNode`, the design of their `prep_async`, `exec_async`, `post_async` (and `exec_fallback_async`) methods also follows the above principles for separation of concerns and data flow. Additionally, elaborate on their asynchronous execution characteristics, such as non-blocking I/O handling, concurrent task design (e.g., whether tasks are independent, how concurrency is managed to avoid rate limits).
    *   **Data Structure Content:** The `## Data Structure` section must clearly define the structure of the `shared` storage (e.g., represented using Python dictionary notation), explaining the meaning and purpose of key data fields. If `params` is used for specific scenarios (like `BatchFlow`), this should also be explained.
    *   **Accurate Terminology and Principle Usage:** All design descriptions must accurately use the core abstract concepts, terminology, and working principles defined in the "Core Design Pattern" (e.g., Node lifecycle & three-phase responsibilities, Flow graph orchestration & Action-driven mechanism, different parameter passing & execution in `BatchNode` vs. `BatchFlow`, impact of Async/Parallel on execution models, distinct roles of `Shared Store` vs. `Params` in communication).

6.  **No Additional Dialogue:** Your output should **contain solely and exclusively** the optimized, complete Markdown document content.
​​
7. Example Output:​
```markdown
# Explain Youtube Podcast To Me Like I'm 5
## Project Requirements
This project takes a YouTube podcast URL, extracts the transcript, identifies key topics and Q&A pairs, simplifies them for children, and generates an HTML report with the results.

## Utility Functions

1. **LLM Calls** (`utils/call_llm.py`)

2. **YouTube Processing** (`utils/youtube_processor.py`)
   - Get video title, transcript and thumbnail

3. **HTML Generator** (`utils/html_generator.py`)
   - Create formatted report with topics, Q&As and simple explanations

## Flow Design

The application flow consists of several key steps organized in a directed graph:

1. **Video Processing**: Extract transcript and metadata from YouTube URL
2. **Topic Extraction**: Identify the most interesting topics (max 5)
3. **Question Generation**: For each topic, generate interesting questions (3 per topic)
4. **Topic Processing**: Batch process each topic to:
   - Rephrase the topic title for clarity
   - Rephrase the questions
   - Generate ELI5 answers
5. **HTML Generation**: Create final HTML output

### Flow Diagram

```mermaid
flowchart TD
    videoProcess[Process YouTube URL] --> topicsQuestions[Extract Topics & Questions]
    topicsQuestions --> contentBatch[Content Processing]
    contentBatch --> htmlGen[Generate HTML]
    
    subgraph contentBatch[Content Processing]
        topicProcess[Process Topic]
    end
```

## Data Structure

The shared memory structure will be organized as follows:

```python
shared = {{
    "video_info": {{
        "url": str,            # YouTube URL
        "title": str,          # Video title
        "transcript": str,     # Full transcript
        "thumbnail_url": str,  # Thumbnail image URL
        "video_id": str        # YouTube video ID
    }},
    "topics": [
        {{
            "title": str,              # Original topic title
            "rephrased_title": str,    # Clarified topic title
            "questions": [
                {{
                    "original": str,      # Original question
                    "rephrased": str,     # Clarified question
                    "answer": str         # ELI5 answer
                }},
                # ... more questions
            ]
        }},
        # ... more topics
    ],
    "html_output": str  # Final HTML content
}}
```

## Node Designs

### 1. ProcessYouTubeURL
- **Purpose**: Process YouTube URL to extract video information
- **Design**: Regular Node (no batch/async)
- **Data Access**: 
  - Read: URL from shared store
  - Write: Video information to shared store

### 2. ExtractTopicsAndQuestions
- **Purpose**: Extract interesting topics from transcript and generate questions for each topic
- **Design**: Regular Node (no batch/async)
- **Data Access**:
  - Read: Transcript from shared store
  - Write: Topics with questions to shared store
- **Implementation Details**:
  - First extracts up to 5 interesting topics from the transcript
  - For each topic, immediately generates 3 relevant questions
  - Returns a combined structure with topics and their associated questions

### 3. ProcessTopic
- **Purpose**: Batch process each topic for rephrasing and answering
- **Design**: BatchNode (process each topic)
- **Data Access**:
  - Read: Topics and questions from shared store
  - Write: Rephrased content and answers to shared store

### 4. GenerateHTML
- **Purpose**: Create final HTML output
- **Design**: Regular Node (no batch/async)
- **Data Access**:
  - Read: Processed content from shared store
  - Write: HTML output to shared store
```
---
**[Previous Markdown Document]:**
{parsed_documents}

**[Deficiencies and Optimization Ideas]:**
{requirements}

**[User's Specific Requirements and Modification Instructions for this iteration]:**
{user_instructions}

**[User's Overall Requirements Flow]:**
{short_flow_steps}

**[Output: Optimized Markdown Document]:**
"""

    def _get_design_optimization_zh(self) -> str:
        """Chinese template for design optimization."""
        return """你是一个专业的AI助手，擅长根据用户需求编辑和优化 Markdown 格式的软件开发设计文档。**你生成的文档必须严格遵循特定的项目设计文档格式，该格式基于Node/Flow架构（包括Node, Flow, BatchNode, BatchFlow, AsyncNode, AsyncFlow, AsyncParallelBatchNode, AsyncParallelBatchFlow 等核心抽象概念，下文统称为“核心设计模式”）。**

你的任务是接收一份【之前的Markdown文档】（可能是空的，如果是首次创建）、一份指导性的【不足之处与优化思路】（由之前的分析产生），一份用户针对本轮迭代的【用户本轮具体需求与修改指令】,以及【用户总体需求的完整流程】。

你需要仔细分析所有输入，然后输出一份整合了所有信息、完整的、【优化后的Markdown文档】。**该文档的结构和内容细节必须严格符合“核心设计模式”的要求，并参照所提供的该模式的示例输出和详细说明。**

请遵循以下规则：

1.  **优先处理用户指令：** 【用户本轮具体需求与修改指令】具有最高优先级。你需要确保这些指令被准确执行，同时将其恰当地融入到“核心设计模式”的文档结构中。
2.  **参考优化思路：** 在执行用户指令时，请积极参考【不足之处与优化思路】中的建议。确保这些建议在应用时也符合“核心设计模式”的规范和文档结构。
3.  **整合与更新：**
    * 如果【之前的Markdown文档】非空，你的任务是在其基础上进行修改和补充，使其完全符合“核心设计模式”。
    * 如果【之前的Markdown文档】为空，你的任务是根据用户指令和优化思路从头开始创建完全符合“核心设计模式”的文档。
    * 确保将【用户本轮具体需求与修改指令】和【不足之处与优化思路】中的可操作建议，恰当地融入文档的相应章节，并严格遵循“核心设计模式”的规范。
4.  **保持完整性：** 输出的必须是**完整的** Markdown 文档，覆盖“核心设计模式”中要求的所有相关部分。
5.  **严格遵循“核心设计模式”并体现其设计方法：**
    * **文档结构与标题：** 输出的Markdown文档必须严格遵循“核心设计模式”示例中的章节结构和标题命名约定（例如：`# [项目标题]`, `## Project Requirements`, `## Utility Functions` (若适用), `## Flow Design`, `### Flow Diagram`, `## Data Structure`, `## Node Designs`, `### N. NodeName`等）。
    * **Flow Design 内容与设计方法：** Flow的设计应清晰描述其如何编排一个或多个Node，以完成更复杂的业务流程。内容需包含：
        * **节点连接与Action驱动的转换**：使用明确的表示法（例如 `node_A >> node_B` 表示 `node_A` 在其 `post` 方法返回 `"default"` Action后转换到 `node_B`；`node_A - "action_name" >> node_B` 表示 `node_A` 在返回特定 `"action_name"` Action后转换到 `node_B`）来展示节点间的执行顺序和基于Action的条件跳转逻辑。解释每个关键Action的含义。
        * **流程逻辑的完整表述**：准确描述Flow中的起始节点（`start` node）、任何分支（branching）判断逻辑、循环（looping）机制（例如，某个节点如何根据Action返回到之前的节点）。
        * **嵌套Flow (Nested Flows)的设计**：如果使用了嵌套Flow（即一个Flow作为另一个Flow图中的一个“超级节点”），需要说明子Flow如何被父Flow调用和管理，以及它作为Node时的行为特征（例如，子Flow会执行其自身的 `prep` 和 `post` 方法，但其 `exec` 方法不执行，其 `post` 方法接收到的 `exec_res` 为 `None`，结果通常通过 `shared` 存储在子Flow内部节点间传递并最终影响父Flow的决策）。
        * **异步/并行Flow的特殊考量**：对于 `AsyncFlow` 或 `AsyncParallelBatchFlow`，需要说明其如何管理和调度其内部的异步/并行Node的执行，以及并发流程的整体组织和控制策略。
        * **`### Flow Diagram`**：必须使用Mermaid的 `flowchart TD` 语法，准确、清晰、完整地可视化上述流程，包括所有Node、它们之间的主要转换路径以及关键的Action标签。
    * **Node Design 内容与设计方法：** 每个Node的描述必须包含其 **Purpose**（目的）、**Design**（设计，明确类型如 `Node`, `BatchNode`, `AsyncNode`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`等，Node类型要尽量异步,并注明如 `max_retries`（最大重试次数，例如 `max_retries=3`，默认为1即不重试） 和 `wait`（重试等待时间，例如 `wait=10`秒，默认为0）等故障转移参数）、**Data Access**（数据访问，详细说明该Node如何与 `shared` 共享存储及 `params` 参数交互）。
        其内容必须清晰反映以下**核心设计原则和方法**：
        * **`prep(shared)` 方法设计**：清晰描述此阶段如何从 `shared` 存储中读取和预处理数据，为后续步骤准备输入，并明确返回什么 (`prep_res`) 。
        * **`exec(prep_res)` 方法设计**：清晰描述此阶段的核心计算逻辑和业务处理。**强调此阶段不应直接访问 `shared` 存储**，以保证计算逻辑的纯粹性。如果启用了重试，则实现应具有幂等性。说明它如何使用 `prep_res` 并返回什么 (`exec_res`)。
        * **`post(shared, prep_res, exec_res)` 方法设计**：清晰描述此阶段如何对 `exec_res` 进行后处理，并将最终结果或状态更新写回 `shared` 存储。同时，明确此阶段如何根据处理结果决定并返回下一个 `Action` 字符串（如果未返回，则默认为 `"default"`），用于驱动Flow的流转。
        * **关注点分离原则 (Separation of Concerns)**：Node的设计应严格体现 `prep`（数据准备与读取）、`exec`（核心计算与逻辑执行）、`post`（数据写入与状态更新/Action决策）三阶段的关注点分离，确保每个阶段职责单一明确。
        * **`exec_fallback(prep_res, exc)` 方法设计**（若有定义）：如果为Node定义了优雅降级逻辑，需说明在 `exec` 方法所有重试均失败后，此方法如何处理异常 `exc` 并提供一个备选的 `exec_res` 结果，而不是让流程中断。
        * **异步/并行Node的特殊考量**：对于 `AsyncNode`, `AsyncParallelBatchNode` 等异步/并行节点，其 `prep_async`, `exec_async`, `post_async` (以及 `exec_fallback_async`) 方法的设计同样遵循上述关注点分离和数据流原则，并需额外阐述其异步执行的特性，如I/O操作的非阻塞处理、并发任务的设计（例如任务是否独立，如何管理并发量以避免速率限制问题等）。
    * ** Flow Diagram 内容与设计方法**：
        * **`### Flow Diagram`**：必须使用Mermaid的 `flowchart TD` 语法，准确、清晰、完整地可视化上述流程，包括所有Node和FLow,包含的节点只能是flow或node.它们之间的主要转换路径以及关键的Action标签。
    

    * **Data Structure 内容：** `## Data Structure` 部分需清晰定义 `shared` 共享存储的结构 (例如，可以使用Python字典的表示法进行示意)，并解释各个关键数据字段的含义和用途。同时，如果 `params` 被用于特定场景（如 `BatchFlow`），也应予以说明。

    * **术语与原理的准确运用：** 所有设计描述必须准确运用“核心设计模式”中定义的核心抽象概念、术语和工作原理（例如Node的生命周期与三阶段职责、Flow的图状编排与Action驱动机制、Batch处理中 `BatchNode` 与 `BatchFlow` 的不同参数传递与执行方式、Async/Parallel对执行模型的影响、Shared Store与Params在通信中的不同角色等）。

6.  **无额外对话：** 你的输出应该**只有且仅有**优化后的完整 Markdown 文档内容。

7.  **示例输出：**
```markdown
# YouTube播客儿童版解释器
## 项目需求
本项目接收一个YouTube播客URL，提取其文字记录（transcript），识别关键主题和问答对，并将其简化为儿童可理解的内容，然后生成包含结果的HTML报告。

## 工具函数

1. **大语言模型调用** (`utils/call_llm.py`)

2. **YouTube处理** (`utils/youtube_processor.py`)
   - 获取视频标题、文字记录和缩略图

3. **HTML生成器** (`utils/html_generator.py`)
   - 创建包含主题、问答和简化解释的格式化报告

## Flow设计

应用程序流由多个关键步骤组成，组织为有向图：

1. **视频处理**：从YouTube URL提取文字记录和元数据
2. **主题提取**：识别最有趣的主题（最多5个）
3. **问题生成**：为每个主题生成有趣的问题（每个主题3个）
4. **主题处理**：批量处理每个主题：
   - 重写主题标题使其更清晰
   - 重写问题
   - 生成ELI5(5岁水平)答案
5. **HTML生成**：创建最终HTML输出

### Flow图表

```mermaid
flowchart TD
    videoProcess[处理YouTube URL] --> topicsQuestions[提取主题和问题]
    topicsQuestions --> contentBatch[内容处理]
    contentBatch --> htmlGen[生成HTML]
    
    subgraph contentBatch[内容处理]
        topicProcess[处理主题]
    end
```

## 数据结构

共享内存结构组织如下：

```python
shared = {{
    "video_info": {{
        "url": str,            # YouTube URL
        "title": str,          # 视频标题
        "transcript": str,     # 完整文字记录
        "thumbnail_url": str,  # 缩略图URL
        "video_id": str        # YouTube视频ID
    }},
    "topics": [
        {{
            "title": str,              # 原始主题标题
            "rephrased_title": str,    # 重写后的主题标题
            "questions": [
                {{
                    "original": str,      # 原始问题
                    "rephrased": str,     # 重写后问题
                    "answer": str         # ELI5答案
                }},
                # ... 更多问题
            ]
        }},
        # ... 更多主题
    ],
    "html_output": str  # 最终HTML内容
}}
```

## Node设计

### 1. ProcessYouTubeURL
- **目的**：处理YouTube URL提取视频信息
- **设计**：常规Node（非批量/异步）
- **数据访问**： 
  - 读取：共享存储中的URL
  - 写入：视频信息到共享存储

### 2. ExtractTopicsAndQuestions
- **目的**：从文字记录提取有趣主题并为每个主题生成问题
- **设计**：常规Node（非批量/异步）
- **数据访问**：
  - 读取：共享存储中的文字记录
  - 写入：包含问题的主题到共享存储
- **实现细节**：
  - 首先从文字记录提取最多5个有趣主题
  - 为每个主题立即生成3个相关问题
  - 返回包含主题及其相关问题的组合结构

### 3. ProcessTopic
- **目的**：批量处理每个主题进行重写和回答
- **设计**：BatchNode（处理每个主题）
- **数据访问**：
  - 读取：共享存储中的主题和问题
  - 写入：重写内容和答案到共享存储

### 4. GenerateHTML
- **目的**：创建最终HTML输出
- **设计**：常规Node（非批量/异步）
- **数据访问**：
  - 读取：共享存储中处理后的内容
  - 写入：HTML输出到共享存储
```
---
**【之前的Markdown文档】:**
{parsed_documents}

**【不足之处与优化思路】:**
{requirements}

**【用户本轮具体需求与修改指令】:**
{user_instructions}

**【用户总体需求的流程】:**
{short_flow_steps}

**【输出：优化后的Markdown文档】:**
"""

    def _get_design_optimization_es(self) -> str:
        """Spanish template for design optimization."""
        return """
# Eres un asistente de IA profesional experto en editar y optimizar documentos de diseño de desarrollo de software formateados en Markdown según las necesidades del usuario.** Los documentos que generes deben adherirse estrictamente a un formato específico de documento de diseño de proyecto basado en la arquitectura Node/Flow** (incluyendo conceptos abstractos centrales como `Node`, `Flow`, `BatchNode`, `BatchFlow`, `AsyncNode`, `AsyncFlow`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`, denominados colectivamente el "Patrón de Diseño Central").

**Tu tarea** consiste en recibir:
1.  Un **Documento Markdown Previo** (puede estar vacío si es una creación inicial),
2.  **Deficiencias y Directrices de Optimización** (generadas a partir de análisis previos),
3.  **Solicitudes Específicas del Usuario e Instrucciones de Modificación para esta Iteración**,
4.  ​El Flujo de Trabajo Completo de los Requerimientos Generales del Usuario**.

Debes analizar cuidadosamente todas las entradas y generar un **documento Markdown integral y optimizado** que integre toda la información. **La estructura y los detalles del contenido de este documento deben cumplir estrictamente con los requisitos del "Patrón de Diseño Central" y hacer referencia a las salidas de ejemplo proporcionadas y a las explicaciones detalladas de este patrón.**

**Por favor, adhiérete a las siguientes reglas:**

1.  **Prioriza las Instrucciones del Usuario:** Las **[Solicitudes Específicas del Usuario e Instrucciones de Modificación para esta Iteración]** tienen la máxima prioridad. Debes asegurarte de que estas instrucciones se ejecuten con precisión mientras se integran adecuadamente en la estructura del documento del "Patrón de Diseño Central".
2.  **Referencia las Directrices de Optimización:** Al ejecutar las instrucciones del usuario, referencia activamente las sugerencias en las **[Deficiencias y Directrices de Optimización]**. Asegúrate de que estas sugerencias se apliquen cumpliendo con las especificaciones y la estructura del documento del "Patrón de Diseño Central".
3.  **Integración y Actualización:**
    *   Si el **[Documento Markdown Previo]** no está vacío, tu tarea es modificarlo y complementarlo para que cumpla plenamente con el "Patrón de Diseño Central".
    *   Si el **[Documento Markdown Previo]** está vacío, tu tarea es crear un documento nuevo desde cero que cumpla plenamente con el "Patrón de Diseño Central", basándote en las instrucciones del usuario y las directrices de optimización.
    *   Asegúrate de que las sugerencias accionables de las **[Solicitudes Específicas del Usuario e Instrucciones de Modificación para esta Iteración]** y las **[Deficiencias y Directrices de Optimización]** se integren adecuadamente en las secciones relevantes del documento, siguiendo estrictamente las normas del "Patrón de Diseño Central".
4.  **Garantiza la Completitud:** La salida debe ser un documento Markdown **completo** que cubra todas las secciones relevantes requeridas por el "Patrón de Diseño Central".
5.  **Adhiérete Estrictamente al "Patrón de Diseño Central" y Refleja su Metodología de Diseño:**
    *   **Estructura del Documento y Encabezados:** El documento Markdown de salida debe seguir estrictamente la estructura de secciones y convenciones de nomenclatura de encabezados (por ejemplo, `# [Título del Proyecto]`, `## Requerimientos del Proyecto`, `## Funciones de Utilidad` (si aplica), `## Diseño del Flujo`, `### Diagrama de Flujo`, `## Estructura de Datos`, `## Diseños de Nodos`, `### N. NombreDelNodo`, etc.) utilizadas en los ejemplos del "Patrón de Diseño Central".
    *   **Contenido y Metodología del Diseño del Flujo:** El diseño del flujo debe describir claramente cómo orquesta uno o más Nodos para lograr procesos de negocio más complejos. El contenido debe incluir:
        *   **Conexiones de Nodos y Transiciones Impulsadas por Acciones:** Usa notación explícita (por ejemplo, `nodo_A >> nodo_B` indica que `nodo_A` transita a `nodo_B` después de que su método `post` retorna la Acción `"default"`; `nodo_A - "nombre_accion" >> nodo_B` indica que `nodo_A` transita a `nodo_B` después de retornar la Acción específica `"nombre_accion"`) para mostrar el orden de ejecución y la lógica de bifurcación condicional basada en Acciones. Explica el significado de cada Acción crítica.
        *   **Descripción Lógica del Proceso Completo:** Describe con precisión el nodo de inicio (`start`), cualquier lógica de juicio de bifurcación, mecanismos de bucle (por ejemplo, cómo un nodo podría volver a un nodo anterior basado en una Acción).
        *   **Diseño de Flujo Anidado (Sub-Flujo):** Si se usan Flujos anidados (es decir, un Flujo que actúa como un "super nodo" dentro del grafo de otro Flujo), explica cómo el Flujo hijo es invocado y gestionado por el Flujo padre y su comportamiento como Nodo (por ejemplo, el Flujo hijo ejecuta sus propios métodos `prep` y `post`, pero su método `exec` no se ejecuta; su método `post` recibe `exec_res` como `None`; los resultados normalmente se almacenan/pasan internamente dentro del Flujo hijo a través de `shared` y finalmente influyen en la decisión del Flujo padre).
        *   **Consideraciones Especiales para Flujos Asíncronos/Paralelos:** Para `AsyncFlow` o `AsyncParallelBatchFlow`, explica cómo gestionan y programan la ejecución de sus Nodos asíncronos/paralelos internos, y la estrategia general de organización y control para flujos de trabajo concurrentes.
        *   **`### Diagrama de Flujo`:** Debe usar la sintaxis Mermaid `flowchart TD` para visualizar el proceso con precisión, claridad y completitud, incluyendo todos los Nodos, las rutas de transición principales entre ellos y las etiquetas de Acción clave.
    *   **Contenido y Metodología del Diseño de Nodos:** Cada descripción de Nodo debe incluir su **Propósito**, **Diseño** (especifica el tipo, por ejemplo, `Node`, `BatchNode`, `AsyncNode`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`, etc.; *los tipos de nodos preferiblemente deberían ser asíncronos* e incluir parámetros de manejo de fallos como `max_retries` (por ejemplo, `max_retries=3`, default=1 significa sin reintentos) y `wait` (por ejemplo, `wait=10` segundos, default=0)), **Acceso a Datos** (detalles sobre cómo el Nodo interactúa con el almacenamiento `shared` y `params`). El contenido debe reflejar claramente los siguientes **principios y metodología de diseño central**:
        *   **Diseño del Método `prep(shared)`:** Describe claramente cómo esta fase lee y preprocesa datos del almacenamiento `shared` para preparar entradas para pasos posteriores, y establece explícitamente lo que retorna (`prep_res`).
        *   **Diseño del Método `exec(prep_res)`:** Describe claramente la lógica computacional central y el procesamiento de negocio en esta fase. **Enfatiza que esta fase NO debe acceder directamente al almacenamiento `shared`** para garantizar la pureza del cálculo. Si los reintentos están habilitados, la implementación debería ser idempotente. Explica cómo utiliza `prep_res` y lo que retorna (`exec_res`).
        *   **Diseño del Método `post(shared, prep_res, exec_res)`:** Describe claramente cómo esta fase post-procesa `exec_res`, escribe resultados finales o actualizaciones de estado de vuelta al almacenamiento `shared`, y decide y retorna la siguiente cadena `Acción` basada en el resultado (si no se retorna nada, por defecto es `"default"`), que impulsa el Flujo.
        *   **Principio de Separación de Responsabilidades:** El diseño del Nodo debe encarnar estrictamente la separación de responsabilidades en `prep` (preparación y lectura de datos), `exec` (cómputo central y ejecución de lógica) y `post` (escritura de datos y actualización de estado / decisión de Acción), asegurando que cada fase tenga una única responsabilidad bien definida.
        *   **Diseño del Método `exec_fallback(prep_res, exc)` (si se define):** Si se define lógica de degradación elegante para el Nodo, describe cómo este método maneja la excepción `exc` después de que todos los reintentos de `exec` hayan fallado y proporciona un resultado alternativo `exec_res`, en lugar de abortar el flujo.
        *   **Consideraciones Especiales para Nodos Asíncronos/Paralelos:** Para nodos como `AsyncNode`, `AsyncParallelBatchNode`, el diseño de sus métodos `prep_async`, `exec_async`, `post_async` (y `exec_fallback_async`) también sigue los principios anteriores de separación de responsabilidades y flujo de datos. Además, desarrolla sus características de ejecución asíncrona, como manejo de E/S no bloqueantes, diseño de tareas concurrentes (por ejemplo, si las tareas son independientes, cómo se gestiona la concurrencia para evitar límites de tasa).
    *   **Contenido de la Estructura de Datos:** La sección `## Estructura de Datos` debe definir claramente la estructura del almacenamiento `shared` (por ejemplo, representado usando notación de diccionario Python), explicando el significado y propósito de los campos de datos clave. Si se usa `params` para escenarios específicos (como `BatchFlow`), esto también debe explicarse.
    *   **Uso Precisa de Terminología y Principios:** Todas las descripciones de diseño deben usar con precisión los conceptos abstractos centrales, la terminología y los principios de funcionamiento definidos en el "Patrón de Diseño Central" (por ejemplo, ciclo de vida del Nodo y responsabilidades de las tres fases, orquestación del grafo de Flujo y mecanismo impulsado por Acciones, diferentes pasajes de parámetros y ejecución en `BatchNode` vs. `BatchFlow`, impacto de Asíncrono/Paralelo en modelos de ejecución, roles distintos de `Shared Store` vs. `Params` en la comunicación).

6.  **Sin Diálogo Adicional:** Tu salida debe **contener única y exclusivamente** el contenido optimizado del documento Markdown completo.
​​
7. Ejemplo de Salida:​
```markdown
# ExplícameElPodcastDeYoutubeComoSiTuviera5
## Requerimientos del Proyecto
Este proyecto toma una URL de un podcast de YouTube, extrae la transcripción, identifica temas clave y pares de preguntas y respuestas, los simplifica para niños y genera un informe HTML con los resultados.

## Funciones de Utilidad

1. **Llamadas a LLM** (`utils/call_llm.py`)

2. **Procesamiento de YouTube** (`utils/youtube_processor.py`)
   - Obtener título del video, transcripción y miniatura

3. **Generador HTML** (`utils/html_generator.py`)
   - Crear informe formateado con temas, preguntas/respuestas y explicaciones simples

## Diseño del Flujo

El flujo de la aplicación consta de varios pasos clave organizados en un grafo dirigido:

1. **Procesamiento del Video**: Extraer transcripción y metadatos de la URL de YouTube
2. **Extracción de Temas**: Identificar los temas más interesantes (máx. 5)
3. **Generación de Preguntas**: Para cada tema, generar preguntas interesantes (3 por tema)
4. **Procesamiento de Temas**: Procesar en lote cada tema para:
   - Reformular el título del tema para mayor claridad
   - Reformular las preguntas
   - Generar respuestas ELI5 (ExplicameComoSiTuviera5)
5. **Generación HTML**: Crear la salida HTML final

### Diagrama de Flujo

```mermaid
flowchart TD
    videoProcess[Procesar URL YouTube] --> topicsQuestions[Extraer Temas y Preguntas]
    topicsQuestions --> contentBatch[Procesamiento de Contenido]
    contentBatch --> htmlGen[Generar HTML]
    
    subgraph contentBatch[Procesamiento de Contenido]
        topicProcess[Procesar Tema]
    end
```

## Estructura de Datos

La estructura de memoria compartida estará organizada como sigue:

```python
shared = {{
    "video_info": {{
        "url": str,            # URL de YouTube
        "title": str,          # Título del video
        "transcript": str,     # Transcripción completa
        "thumbnail_url": str,  # URL de la miniatura
        "video_id": str        # ID del video de YouTube
    }},
    "topics": [
        {{
            "title": str,              # Título original del tema
            "rephrased_title": str,    # Título del tema reformulado
            "questions": [
                {{
                    "original": str,      # Pregunta original
                    "rephrased": str,     # Pregunta reformulada
                    "answer": str         # Respuesta ELI5 (ExplicameComoSiTuviera5)
                }},
                # ... más preguntas
            ]
        }},
        # ... más temas
    ],
    "html_output": str  # Contenido HTML final
}}
```

## Diseños de Nodos

### 1. ProcesarURLYouTube
- **Propósito**: Procesar URL de YouTube para extraer información del video
- **Diseño**: Nodo Regular (sin lote/asíncrono)
- **Acceso a Datos**: 
  - Lectura: URL del almacenamiento compartido
  - Escritura: Información del video al almacenamiento compartido

### 2. ExtraerTemasYPreguntas
- **Propósito**: Extraer temas interesantes de la transcripción y generar preguntas para cada tema
- **Diseño**: Nodo Regular (sin lote/asíncrono)
- **Acceso a Datos**:
  - Lectura: Transcripción del almacenamiento compartido
  - Escritura: Temas con preguntas al almacenamiento compartido
- **Detalles de Implementación**:
  - Primero extrae hasta 5 temas interesantes de la transcripción
  - Para cada tema, genera inmediatamente 3 preguntas relevantes
  - Retorna una estructura combinada con temas y sus preguntas asociadas

### 3. ProcesarTema
- **Propósito**: Procesar cada tema en lote para reformulación y respuesta
- **Diseño**: BatchNode (procesa cada tema)
- **Acceso a Datos**:
  - Lectura: Temas y preguntas del almacenamiento compartido
  - Escritura: Contenido reformulado y respuestas al almacenamiento compartido

### 4. GenerarHTML
- **Propósito**: Crear la salida HTML final
- **Diseño**: Nodo Regular (sin lote/asíncrono)
- **Acceso a Datos**:
  - Lectura: Contenido procesado del almacenamiento compartido
  - Escritura: Salida HTML al almacenamiento compartido
```
---
**[Documento Markdown Anterior]:**
{parsed_documents}

**[Deficiencias e Ideas de Optimización]:**
{requirements}

**[Instrucciones Específicas del Usuario y Modificaciones para esta iteración]:**
{user_instructions}

**[Flujo de Requisitos Generales del Usuario]:**
{short_flow_steps}

**[Salida: Documento Markdown Optimizado]:**
"""

    def _get_design_optimization_fr(self) -> str:
        """French template for design optimization."""
        return """**Vous êtes un assistant IA professionnel compétent dans l'édition et l'optimisation de documents de conception de développement logiciel formatés en Markdown selon les besoins de l'utilisateur.** **Les documents que vous générez doivent strictement adhérer à un format spécifique de document de conception de projet basé sur l'architecture Nœud/Flux** (incluant des concepts abstraits centraux tels que `Node`, `Flow`, `BatchNode`, `BatchFlow`, `AsyncNode`, `AsyncFlow`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`, collectivement désignés comme le "Modèle de Conception Central").

**Votre tâche** consiste à recevoir :
1.  Un **Document Markdown Précédent** (peut être vide s'il s'agit d'une création initiale),
2.  **Déficiences et Consignes d'Optimisation** (générées à partir d'une analyse antérieure),
3.  **Demandes Spécifiques de l'Utilisateur et Instructions de Modification pour Cette Itération**,
4.  **Le Flux de Travail Complet des Besoins Globaux de l'Utilisateur**.

Vous devez analyser minutieusement toutes les entrées et produire un **document Markdown complet et optimisé** qui intègre toutes les informations. **La structure et les détails du contenu de ce document doivent strictement se conformer aux exigences du "Modèle de Conception Central" et se référer aux exemples de sortie fournis ainsi qu'aux explications détaillées de ce modèle.**

**Veuillez respecter les règles suivantes :**

1.  **Priorité aux Instructions Utilisateur :** Les **[Demandes Spécifiques de l'Utilisateur et Instructions de Modification pour Cette Itération]** ont la plus haute priorité. Vous devez vous assurer que ces instructions sont exécutées avec précision tout en les intégrant de manière appropriée dans la structure du document du "Modèle de Conception Central".
2.  **Référence aux Consignes d'Optimisation :** Lors de l'exécution des instructions utilisateur, référez-vous activement aux suggestions des **[Déficiences et Consignes d'Optimisation]**. Assurez-vous que ces suggestions soient appliquées en conformité avec les spécifications du "Modèle de Conception Central" et la structure du document.
3.  **Intégration et Mise à Jour :**
    *   Si le **[Document Markdown Précédent]** n'est pas vide, votre tâche consiste à le modifier et le compléter pour le rendre pleinement conforme au "Modèle de Conception Central".
    *   Si le **[Document Markdown Précédent]** est vide, votre tâche consiste à créer un nouveau document entièrement conforme au "Modèle de Conception Central" à partir de zéro, sur la base des instructions utilisateur et des consignes d'optimisation.
    *   Veillez à intégrer les suggestions actionnables des **[Demandes Spécifiques de l'Utilisateur et Instructions de Modification pour Cette Itération]** et des **[Déficiences et Consignes d'Optimisation]** dans les sections pertinentes du document, en respectant strictement les normes du "Modèle de Conception Central".
4.  **Assurer l'Exhaustivité :** La sortie doit être un document Markdown **complet** couvrant toutes les sections pertinentes requises par le "Modèle de Conception Central".
5.  **Adhérer Strictement au "Modèle de Conception Central" et Refléter sa Méthodologie de Conception :**
    *   **Structure du Document et En-têtes :** Le document Markdown en sortie doit strictement suivre la structure des sections et les conventions de nommage des en-têtes (par ex. `# [Titre du Projet]`, `## Exigences du Projet`, `## Fonctions Utilitaires` (si applicable), `## Conception du Flux`, `### Diagramme de Flux`, `## Structure des Données`, `## Conceptions des Nœuds`, `### N. NomDuNœud`, etc.) utilisées dans les exemples du "Modèle de Conception Central".
    *   **Contenu & Méthodologie de Conception du Flux :** La conception du flux doit décrire clairement comment il orchestre un ou plusieurs Nœuds pour réaliser des processus métier plus complexes. Le contenu doit inclure :
        *   **Connexions des Nœuds & Transitions Pilotées par Actions :** Utiliser une notation explicite (par ex. `node_A >> node_B` indique que `node_A` passe à `node_B` après que sa méthode `post` retourne l'Action `"default"` ; `node_A - "nom_action" >> node_B` indique que `node_A` passe à `node_B` après avoir retourné l'Action spécifique `"nom_action"`) pour montrer l'ordre d'exécution et la logique de branchement conditionnel basée sur les Actions. Expliquer la signification de chaque Action critique.
        *   **Description Complète de la Logique du Processus :** Décrire avec précision le nœud de départ (`start` nœud), toute logique de décision de branchement, les mécanismes de boucle (par ex. comment un nœud peut revenir à un nœud précédent basé sur une Action).
        *   **Conception de Flux Imbriqués (Sous-Flux) :** Si des Flux imbriqués sont utilisés (c'est-à-dire qu'un Flux agit comme un "super nœud" dans le graphe d'un autre Flux), expliquer comment le Flux enfant est invoqué et géré par le Flux parent et son comportement en tant que Nœud (par ex. le Flux enfant exécute ses propres méthodes `prep` et `post`, mais sa méthode `exec` n'est pas exécutée ; sa méthode `post` reçoit `exec_res` comme `None` ; les résultats sont typiquement stockés/passés en interne au sein du Flux enfant via `shared` et influencent finalement la décision du Flux parent).
        *   **Considérations Spéciales pour les Flux Async/Parallèles :** Pour `AsyncFlow` ou `AsyncParallelBatchFlow`, expliquer comment ils gèrent et planifient l'exécution de leurs Nœuds asynchrones/parallèles internes, et l'organisation globale et la stratégie de contrôle des flux de travail concurrents.
        *   **`### Diagramme de Flux` :** Doit utiliser la syntaxe Mermaid `flowchart TD` pour visualiser le processus de manière précise, claire et complète, incluant tous les Nœuds, les principaux chemins de transition entre eux et les étiquettes d'Actions clés.
    *   **Contenu & Méthodologie de Conception des Nœuds :** Chaque description de Nœud doit inclure son **Objectif**, sa **Conception** (spécifier le type par ex. `Node`, `BatchNode`, `AsyncNode`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`, etc. ; *les types de nœuds devraient de préférence être asynchrones* et inclure des paramètres de gestion des échecs comme `max_retries` (par ex. `max_retries=3`, default=1 signifie aucune nouvelle tentative) et `wait` (par ex. `wait=10` secondes, default=0)), **Accès aux Données** (détails sur la façon dont le Nœud interagit avec le stockage `shared` et `params`). Le contenu doit clairement refléter les **principes et la méthodologie de conception centraux** suivants :
        *   **Conception de la Méthode `prep(shared)` :** Décrire clairement comment cette phase lit et prétraite les données du stockage `shared` pour préparer les entrées des étapes suivantes, et indiquer explicitement ce qui est retourné (`prep_res`).
        *   **Conception de la Méthode `exec(prep_res)` :** Décrire clairement la logique de calcul principale et le traitement métier dans cette phase. **Souligner que cette phase ne doit PAS accéder directement au stockage `shared`** pour garantir la pureté du calcul. Si les nouvelles tentatives sont activées, l'implémentation devrait être idempotente. Expliquer comment elle utilise `prep_res` et ce qu'elle retourne (`exec_res`).
        *   **Conception de la Méthode `post(shared, prep_res, exec_res)` :** Décrire clairement comment cette phase post-traite `exec_res`, écrit les résultats finaux ou les mises à jour d'état dans le stockage `shared`, et décide & retourne la prochaine chaîne `Action` basée sur le résultat (si rien n'est retourné, la valeur par défaut est `"default"`), ce qui pilote le Flux.
        *   **Principe de Séparation des Préoccupations :** La conception du nœud doit strictement incarner la séparation des préoccupations en `prep` (préparation & lecture des données), `exec` (calcul principal & exécution de la logique), et `post` (écriture des données & mise à jour d'état / décision d'Action), garantissant que chaque phase a une responsabilité unique et bien définie.
        *   **Conception de la Méthode `exec_fallback(prep_res, exc)`** (si définie) : Si une logique de dégradation gracieuse est définie pour le Nœud, décrire comment cette méthode gère l'exception `exc` après que toutes les nouvelles tentatives de `exec` aient échoué et fournit un résultat `exec_res` alternatif, au lieu d'interrompre le flux.
        *   **Considérations Spéciales pour les Nœuds Async/Parallèles :** Pour les nœuds comme `AsyncNode`, `AsyncParallelBatchNode`, la conception de leurs méthodes `prep_async`, `exec_async`, `post_async` (et `exec_fallback_async`) suit également les principes ci-dessus de séparation des préoccupations et de flux de données. De plus, élaborer sur leurs caractéristiques d'exécution asynchrones, comme la gestion d'entrées/sorties non bloquantes, la conception de tâches concurrentes (par ex. si les tâches sont indépendantes, comment la concurrence est gérée pour éviter les limites de débit).
    *   **Contenu de la Structure des Données :** La section `## Structure des Données` doit clairement définir la structure du stockage `shared` (par ex. représentée en utilisant la notation de dictionnaire Python), expliquant la signification et l'objectif des champs de données clés. Si `params` est utilisé pour des scénarios spécifiques (comme `BatchFlow`), cela doit également être expliqué.
    *   **Utilisation Précise de la Terminologie et des Principes :** Toutes les descriptions de conception doivent utiliser avec précision les concepts abstraits centraux, la terminologie et les principes de fonctionnement définis dans le "Modèle de Conception Central" (par ex. cycle de vie du nœud & responsabilités à trois phases, orchestration du graphe de flux & mécanisme piloté par Action, différences de passage de paramètres et d'exécution dans `BatchNode` vs. `BatchFlow`, impact d'Async/Parallèle sur les modèles d'exécution, rôles distincts du `Stockage Partagé` vs. `Params` dans la communication).

6.  **Aucun Dialogue Supplémentaire :** Votre sortie doit **contenir uniquement et exclusivement** le contenu optimisé et complet du document Markdown.

7. Exemple de Sortie :
```markdown
# Explain Youtube Podcast To Me Like I'm 5 (Expliquer un podcast YouTube comme à un enfant de 5 ans)
## Exigences du Projet
Ce projet prend une URL de podcast YouTube, extrait la transcription, identifie les sujets clés et les paires Q&R, les simplifie pour les enfants et génère un rapport HTML avec les résultats.

## Fonctions Utilitaires

1. **Appels LLM** (`utils/call_llm.py`)

2. **Traitement YouTube** (`utils/youtube_processor.py`)
   - Obtenir le titre de la vidéo, la transcription et la miniature

3. **Générateur HTML** (`utils/html_generator.py`)
   - Créer un rapport formaté avec les sujets, Q&R et explications simplifiées

## Conception du Flux

Le flux de l'application consiste en plusieurs étapes clés organisées dans un graphe orienté :

1. **Traitement Vidéo**: Extraire la transcription et les métadonnées de l'URL YouTube
2. **Extraction des Sujets**: Identifier les sujets les plus intéressants (max 5)
3. **Génération de Questions**: Pour chaque sujet, générer des questions intéressantes (3 par sujet)
4. **Traitement des Sujets**: Traiter chaque sujet en lot pour :
   - Reformuler le titre du sujet pour plus de clarté
   - Reformuler les questions
   - Générer des réponses ELI5 (Explain Like I'm 5)
5. **Génération HTML**: Créer la sortie HTML finale

### Diagramme de Flux

```mermaid
flowchart TD
    videoProcess[Traiter URL YouTube] --> topicsQuestions[Extraire Sujets & Questions]
    topicsQuestions --> contentBatch[Traitement du Contenu]
    contentBatch --> htmlGen[Générer HTML]
    
    subgraph contentBatch[Traitement du Contenu]
        topicProcess[Traiter un Sujet]
    end
```

## Structure des Données

La structure de mémoire partagée sera organisée comme suit :

```python
shared = {{
    "video_info": {{
        "url": str,            # URL YouTube
        "title": str,          # Titre de la vidéo
        "transcript": str,     # Transcription complète
        "thumbnail_url": str,  # URL de la miniature
        "video_id": str        # ID de la vidéo YouTube
    }},
    "topics": [
        {{
            "title": str,              # Titre original du sujet
            "rephrased_title": str,    # Titre du sujet clarifié
            "questions": [
                {{
                    "original": str,      # Question originale
                    "rephrased": str,     # Question clarifiée
                    "answer": str         # Réponse ELI5
                }},
                # ... autres questions
            ]
        }},
        # ... autres sujets
    ],
    "html_output": str  # Contenu HTML final
}}
```

## Conceptions des Nœuds

### 1. ProcessYouTubeURL (TraiterURLYouTube)
- **Objectif**: Traiter l'URL YouTube pour extraire les informations vidéo
- **Conception**: Nœud Régulier (sans lot/asynchrone)
- **Accès aux Données**:
  - Lecture: URL du stockage partagé
  - Écriture: Informations vidéo dans le stockage partagé

### 2. ExtractTopicsAndQuestions (ExtraireSujetsEtQuestions)
- **Objectif**: Extraire les sujets intéressants de la transcription et générer des questions pour chaque sujet
- **Conception**: Nœud Régulier (sans lot/asynchrone)
- **Accès aux Données**:
  - Lecture: Transcription du stockage partagé
  - Écriture: Sujets avec questions dans le stockage partagé
- **Détails d'Implémentation**:
  - Extrait d'abord jusqu'à 5 sujets intéressants de la transcription
  - Pour chaque sujet, génère immédiatement 3 questions pertinentes
  - Retourne une structure combinée avec les sujets et leurs questions associées

### 3. ProcessTopic (TraiterSujet)
- **Objectif**: Traiter chaque sujet en lot pour le reformatage et les réponses
- **Conception**: BatchNode (traiter chaque sujet)
- **Accès aux Données**:
  - Lecture: Sujets et questions du stockage partagé
  - Écriture: Contenu reformulé et réponses dans le stockage partagé

### 4. GenerateHTML (GénérerHTML)
- **Objectif**: Créer la sortie HTML finale
- **Conception**: Nœud Régulier (sans lot/asynchrone)
- **Accès aux Données**:
  - Lecture: Contenu traité du stockage partagé
  - Écriture: Sortie HTML dans le stockage partagé
```
---
**[Document Markdown Précédent]:**
{parsed_documents}

**[Déficiences et Idées d'Optimisation]:**
{requirements}

**[Instructions Spécifiques de l'Utilisateur et Modifications pour cette itération]:**
{user_instructions}

**[Flux d'Exigences Générales de l'Utilisateur]:**
{short_flow_steps}

**[Sortie: Document Markdown Optimisé]:**
"""

    def _get_design_optimization_ja(self) -> str:
        """Japanese template for design optimization."""
        return """# プロフェッショナルなAIアシスタントの設計仕様書

## 設計仕様概要
本AIアシスタントは、ユーザー要件に基づいてMarkdown形式のソフトウェア開発設計ドキュメントの編集・最適化に特化したプロフェッショナルツールです。出力ドキュメントは、Node/Flowアーキテクチャに基づく厳密な設計書式（中核概念：`Node`, `Flow`, `BatchNode`, `BatchFlow`, `AsyncNode`, `AsyncFlow`, `AsyncParallelBatchNode`, `AsyncParallelBatchFlow`を包含する「中核設計パターン」）に準拠しなければなりません。

## 主要タスク
以下の入力を受け取り、**完全最適化済みMarkdownドキュメント**を生成します：
1.  **前回版Markdownドキュメント**（新規作成時は空）
2.  **不備点と最適化指針**（事前分析から生成）
3.  **ユーザーの個別リクエストと修正指示**
4.  **ユーザー要件全体の完全ワークフロー**

## 絶対遵守ルール

### 優先順位
1.  **ユーザー指示最優先**：当次[修正指示]を厳密に実行しつつ「中核設計パターン」に統合
2.  **最適化指針の反映**：[不備点指針]を設計パターン仕様に則って適用
3.  **文書統合方法**：
    *   既存ドキュメント：修正・追記で完全準拠化
    *   新規作成時：ユーザー指示から完全準拠ドキュメントを一から構築
    *   全変更を関連セクションにパターン規範厳守で統合
4.  **完全性保証**：出力は「中核設計パターン」必須項目を網羅した完成版

### 設計パターン厳守事項
#### 文書構造
*   見出し書式厳守（例: `# [プロジェクト名]`, `## 要件定義`, `## ユーティリティ関数`, `## フロー設計`, `### フロー図`, `## データ構造`, `## ノード設計`, `### N. ノード名`）

#### フロー設計
*   **ノード接続記述法**：`ノードA >> ノードB`（デフォルト遷移）, `ノードA - "アクション名" >> ノードB`（特定アクション遷移）
*   **全プロセス記述**：開始ノード(`start`), 分岐/ループ処理の明示
*   **ネストフロー設計**：子フローの`prep/post`実行動作と親フロー制御（`exec`未実行, `exec_res=None`受信）
*   **非同期/並列フロー**：`AsyncFlow`/`AsyncParallelBatchFlow`の内部ノード管理戦略を明記
*   **フロー図表記**：Mermaid `flowchart TD`構文で全ノード・遷移・アクションを可視化

#### ノード設計
*   **必須記述項目**：
    *   目的・種別(`Node`,`AsyncNode`等)
    *   障害対策パラメータ(`max_retries=3`, `wait=10`)
    *   データアクセス(`shared`/`params`使用法)
*   **3層責務分離原則**：
    ```typescript
    prep(shared) → prep_res  // 共有データ読取
    exec(prep_res) → exec_res // 純粋演算（共有データ厳禁）
    post(shared,exec_res) → Action // 書込・状態更新・遷移決定
    ```
*   **異常時処理**：`exec_fallback(prep_res, exc)`による復旧戦略の明記
*   **非同期ノード**：`prep_async/exec_async/post_async`の非同期特性記述（非ブロッキングI/O, 並列制御）

#### データ構造設計
*   `shared`構造のPython辞書形式定義（主要フィールド説明）
*   `params`使用箇所の動作説明

#### 用語厳格性
*   「中核設計パターン」の抽象概念・用語・原理を一貫使用（例: ノードライフサイクル、アクション駆動機構、`BatchFlow`と`BatchNode`のパラメータ差異）

### 出力ルール
*   生成する**完全最適化Markdownドキュメントのみ**を出力

---

## 出力例
```markdown
# 5歳児向けYouTubeポッドキャスト解説システム

## プロジェクト要件
YouTubeポッドキャストURLから字幕を抽出 → 重要トピック/Q&Aペアを特定 → 児童向けに簡略化 → HTMLレポート生成

## ユーティリティ関数
1. **LLM呼出** (`utils/call_llm.py`)
2. **YouTube処理** (`utils/youtube_processor.py`)
   - 動画タイトル/字幕/サムネイル取得
3. **HTML生成** (`utils/html_generator.py`)
   - トピック/Q&A/解説を含む整形レポート作成

## フロー設計
1. **動画処理**: YouTube URLからメタデータ抽出
2. **トピック抽出**: 重要トピック(max5)特定
3. **質問生成**: トピック毎に質問x3生成
4. **トピック処理**: 下記をバッチ処理
   - トピック言い換え
   - 質問再構築
   - ELI5回答生成
5. **HTML出力**: 最終レポート生成

### フロー図
```mermaid
flowchart TD
    videoProcess[YouTube処理] --> topicsQuestions[トピック/質問抽出]
    topicsQuestions --> contentBatch[コンテンツ加工]
    contentBatch --> htmlGen[HTML生成]
    
    subgraph contentBatch[コンテンツ加工]
        topicProcess[トピック処理]
    end
```

## データ構造
```python
shared = {{
    "video_info": {{
        "url": str,           # YouTube URL
        "title": str,         # 動画タイトル
        "transcript": str,    # 完全字幕
        "thumbnail_url": str, # サムネイルURL
        "video_id": str       # 動画ID
    }},
    "topics": [{{
        "title": str,           # 原トピック
        "rephrased_title": str, # 再構築トピック
        "questions": [{{ 
            "original": str,    # 原質問
            "rephrased": str,   # 再構築質問
            "answer": str       # ELI5回答
        }}]
    }}],
    "html_output": str  # 最終HTML
}}
```

## ノード設計
### 1. ProcessYouTubeURL
- **目的**: YouTube URLからのメタデータ抽出
- **設計**: 基本ノード（非バッチ/非同期）
- **データアクセス**:
  - 読取: URL（共有領域）
  - 書込: 動画情報（共有領域）

### 2. ExtractTopicsAndQuestions
- **目的**: 字幕からトピック抽出＆質問生成
- **設計**: 基本ノード
- **データアクセス**:
  - 読取: 字幕（共有領域）
  - 書込: トピック＆質問群（共有領域）
- **詳細**:
  - 最大5トピック抽出
  - トピック毎に質問x3即時生成
  - 統合構造で出力

### 3. ProcessTopic
- **目的**: トピック単位のバッチ処理
- **設計**: BatchNode
- **データアクセス**:
  - 読取: トピック/質問（共有領域）
  - 書込: 加工コンテンツ（共有領域）

### 4. GenerateHTML
- **目的**: 最終HTML生成
- **設計**: 基本ノード
- **データアクセス**:
  - 読取: 加工済コンテンツ（共有領域）
  - 書込: HTML出力（共有領域）
```
---
**[以前のMarkdown文書]:**
{parsed_documents}

**[不足点と最適化アイデア]:**
{requirements}

**[この反復に対するユーザーの具体的な要件と修正指示]:**
{user_instructions}

**[ユーザーの全体的な要件フロー]:**
{short_flow_steps}

**[出力: 最適化されたMarkdown文書]:**
"""


# Global prompt template manager instance
prompt_template_manager = PromptTemplateManager()


def get_prompt_template(prompt_type: PromptType, language: SupportedLanguage) -> str:
    """Convenience function to get a prompt template.

    Args:
        prompt_type: The type of prompt needed
        language: The target language

    Returns:
        The prompt template string
    """
    return prompt_template_manager.get_template(prompt_type, language)


def get_prompt_template_by_code(prompt_type: str, language_code: str) -> str:
    """Convenience function to get a prompt template by string codes.

    Args:
        prompt_type: The prompt type as string (e.g., 'generate_steps')
        language_code: The language code as string (e.g., 'en', 'zh')

    Returns:
        The prompt template string
    """
    try:
        prompt_enum = PromptType(prompt_type)
        language_enum = SupportedLanguage(language_code.lower())
        return prompt_template_manager.get_template(prompt_enum, language_enum)
    except ValueError as e:
        raise ValueError(
            f"Invalid prompt type '{prompt_type}' or language code '{language_code}': {e}"
        )
