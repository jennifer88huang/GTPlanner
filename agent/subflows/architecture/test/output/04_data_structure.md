# 数据结构设计结果

## 整体描述
RAG问答处理流水线的共享数据存储，用于在各节点间传递和共享关键数据，支持从用户问题输入到最终答案生成的完整处理流程，包含输入数据、中间处理结果、对话上下文和系统状态信息

## Shared字段定义

### raw_user_input
- **数据类型**: str
- **描述**: 用户原始输入的自然语言问题
- **用途**: 记录用户未经处理的原始查询
- **读取节点**: InputValidationNode
- **写入节点**: FlowInitiator
- **是否必需**: 是
- **示例值**: `什么是人工智能的发展历程？`

### raw_conversation_history
- **数据类型**: list
- **描述**: 原始对话历史记录，包含多轮问答内容
- **用途**: 提供上下文参考，支持多轮对话理解
- **读取节点**: InputValidationNode, ConversationMemoryNode
- **写入节点**: FlowInitiator
- **是否必需**: 是
- **示例值**: `[{'role': 'user', 'content': '什么是机器学习？'}, {'role': 'assistant', 'content': '机器学习是人工智能的一个分支...'}]`

### validated_question
- **数据类型**: str
- **描述**: 经过验证和预处理的问题文本
- **用途**: 确保后续节点使用格式正确的问题文本
- **读取节点**: QuestionUnderstandingNode, ConversationMemoryNode
- **写入节点**: InputValidationNode
- **是否必需**: 是
- **示例值**: `人工智能的发展历程是什么？`

### structured_conversation_context
- **数据类型**: dict
- **描述**: 结构化的对话上下文信息，包含格式化的历史记录和元数据
- **用途**: 为问题理解和回答生成提供结构化上下文支持
- **读取节点**: QuestionUnderstandingNode, AnswerGenerationNode
- **写入节点**: InputValidationNode
- **是否必需**: 是
- **示例值**: `{'history': [{'role': 'user', 'content': '什么是机器学习？'}, {'role': 'assistant', 'content': '机器学习是人工智能的一个分支...'}], 'turn_count': 1, 'last_updated': '2023-11-15T10:30:00Z'}`

### question_intent
- **数据类型**: str
- **描述**: 用户问题的意图分类标签
- **用途**: 指导后续检索和回答生成策略
- **读取节点**: ConversationMemoryNode, DocumentRetrievalNode
- **写入节点**: QuestionUnderstandingNode
- **是否必需**: 是
- **示例值**: `definition`

### extracted_entities
- **数据类型**: list
- **描述**: 从问题中提取的关键实体列表
- **用途**: 辅助文档检索和上下文理解
- **读取节点**: ConversationMemoryNode, DocumentRetrievalNode
- **写入节点**: QuestionUnderstandingNode
- **是否必需**: 是
- **示例值**: `[{'entity': '人工智能', 'type': 'concept', 'confidence': 0.95}]`

### optimized_query_vector
- **数据类型**: list
- **描述**: 优化后的问题查询向量，用于文档检索
- **用途**: 提高文档检索的准确性和相关性
- **读取节点**: DocumentRetrievalNode
- **写入节点**: QuestionUnderstandingNode
- **是否必需**: 是
- **示例值**: `[0.123, 0.456, -0.789]`

### updated_conversation_history
- **数据类型**: list
- **描述**: 更新后的完整对话历史记录
- **用途**: 维护多轮对话状态，支持上下文连贯的对话
- **读取节点**: AnswerGenerationNode, AnswerRefinementNode
- **写入节点**: ConversationMemoryNode
- **是否必需**: 是
- **示例值**: `[{'role': 'user', 'content': '什么是机器学习？'}, {'role': 'assistant', 'content': '机器学习是人工智能的一个分支...'}, {'role': 'user', 'content': '它的发展历程是什么？'}]`

### context_summary
- **数据类型**: str
- **描述**: 对话上下文的摘要信息
- **用途**: 为文档检索和回答生成提供简洁的上下文参考
- **读取节点**: DocumentRetrievalNode, AnswerGenerationNode
- **写入节点**: ConversationMemoryNode
- **是否必需**: 是
- **示例值**: `用户之前询问了机器学习的定义，现在想了解其发展历程`

### retrieved_documents
- **数据类型**: list
- **描述**: 从知识库检索到的相关文档片段列表
- **用途**: 为回答生成提供事实依据和参考资料
- **读取节点**: AnswerGenerationNode
- **写入节点**: DocumentRetrievalNode
- **是否必需**: 是
- **示例值**: `[{'id': 'doc123', 'content': '机器学习的发展始于20世纪50年代...', 'score': 0.92, 'source': 'AI发展史.pdf'}]`

### retrieval_confidence
- **数据类型**: float
- **描述**: 文档检索结果的整体置信度评分
- **用途**: 指导回答生成策略，区分高/低置信度情况
- **读取节点**: AnswerGenerationNode
- **写入节点**: DocumentRetrievalNode
- **是否必需**: 是
- **示例值**: `0.87`

### initial_answer
- **数据类型**: str
- **描述**: 初步生成的自然语言回答
- **用途**: 作为最终回答的基础版本
- **读取节点**: ConversationMemoryNode, AnswerRefinementNode
- **写入节点**: AnswerGenerationNode
- **是否必需**: 是
- **示例值**: `机器学习的发展历程可以分为以下几个阶段：1. 起步阶段(1950s-1970s)...`

### citation_sources
- **数据类型**: list
- **描述**: 回答引用的来源信息列表
- **用途**: 提供回答的事实依据，支持可追溯性
- **读取节点**: AnswerRefinementNode
- **写入节点**: AnswerGenerationNode
- **是否必需**: 是
- **示例值**: `[{'doc_id': 'doc123', 'quote': '机器学习的发展始于20世纪50年代', 'page': 15}]`

### final_answer
- **数据类型**: str
- **描述**: 经过优化和格式化的最终回答
- **用途**: 作为系统输出返回给用户
- **读取节点**: FlowTerminator
- **写入节点**: AnswerRefinementNode
- **是否必需**: 是
- **示例值**: `机器学习的发展历程可以分为以下几个关键阶段：

1. 起步阶段(1950s-1970s)...[1]

[1] AI发展史.pdf, 第15页`

### answer_confidence
- **数据类型**: float
- **描述**: 最终回答的置信度评分
- **用途**: 指示回答的可靠性程度
- **读取节点**: FlowTerminator
- **写入节点**: AnswerRefinementNode
- **是否必需**: 是
- **示例值**: `0.89`

### error_info
- **数据类型**: dict
- **描述**: 错误信息，包含错误类型和描述
- **用途**: 记录和传递处理过程中发生的错误信息
- **读取节点**: FlowTerminator
- **写入节点**: InputValidationNode, QuestionUnderstandingNode, DocumentRetrievalNode, AnswerGenerationNode
- **是否必需**: 否
- **示例值**: `{'error_type': 'validation_error', 'message': '输入问题为空', 'code': 'EMPTY_INPUT'}`

### node_execution_status
- **数据类型**: dict
- **描述**: 各节点的执行状态信息
- **用途**: 跟踪流程执行进度和节点状态
- **读取节点**: 所有节点
- **写入节点**: 所有节点
- **是否必需**: 是
- **示例值**: `{'InputValidationNode': 'completed', 'QuestionUnderstandingNode': 'completed', 'DocumentRetrievalNode': 'in_progress'}`

## 数据流模式

### 输入验证与预处理流程
- **描述**: 处理原始用户输入，转换为结构化上下文和验证后的问题
- **涉及字段**: raw_user_input, raw_conversation_history, validated_question, structured_conversation_context
- **流转顺序**: raw_user_input → InputValidationNode → validated_question → raw_conversation_history → InputValidationNode → structured_conversation_context

### 问题理解与上下文管理流程
- **描述**: 解析问题意图，提取关键实体，更新对话上下文
- **涉及字段**: validated_question, structured_conversation_context, question_intent, extracted_entities, optimized_query_vector, updated_conversation_history, context_summary
- **流转顺序**: validated_question+structured_conversation_context → QuestionUnderstandingNode → question_intent+extracted_entities+optimized_query_vector → ConversationMemoryNode → updated_conversation_history+context_summary

### 文档检索与回答生成流程
- **描述**: 基于优化查询检索相关文档，生成初步回答
- **涉及字段**: optimized_query_vector, extracted_entities, context_summary, retrieved_documents, retrieval_confidence, initial_answer, citation_sources
- **流转顺序**: optimized_query_vector+extracted_entities+context_summary → DocumentRetrievalNode → retrieved_documents+retrieval_confidence → AnswerGenerationNode → initial_answer+citation_sources

### 回答优化与最终输出流程
- **描述**: 优化初步回答，生成格式化最终结果
- **涉及字段**: initial_answer, citation_sources, updated_conversation_history, final_answer, answer_confidence
- **流转顺序**: initial_answer+citation_sources+updated_conversation_history → AnswerRefinementNode → final_answer+answer_confidence

### 错误处理流程
- **描述**: 捕获和传递处理过程中的错误信息
- **涉及字段**: error_info, node_execution_status
- **流转顺序**: 错误发生节点 → error_info+node_execution_status → FlowTerminator

## Shared存储示例结构

```json
{
  "raw_user_input": "什么是人工智能的发展历程？",
  "raw_conversation_history": [
    {
      "role": "user",
      "content": "什么是人工智能？"
    },
    {
      "role": "assistant",
      "content": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。"
    }
  ],
  "validated_question": "什么是人工智能的发展历程？",
  "structured_conversation_context": {
    "history": [
      {
        "role": "user",
        "content": "什么是人工智能？"
      },
      {
        "role": "assistant",
        "content": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。"
      }
    ],
    "turn_count": 1,
    "last_updated": "2023-11-15T14:30:22Z",
    "session_id": "conv_123456"
  },
  "question_intent": "development_history",
  "extracted_entities": [
    {
      "entity": "人工智能",
      "type": "concept",
      "confidence": 0.98
    },
    {
      "entity": "发展历程",
      "type": "event_sequence",
      "confidence": 0.92
    }
  ],
  "optimized_query_vector": [
    0.023,
    0.145,
    -0.089,
    0.231,
    0.567,
    -0.342,
    0.189
  ],
  "updated_conversation_history": [
    {
      "role": "user",
      "content": "什么是人工智能？"
    },
    {
      "role": "assistant",
      "content": "人工智能是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。"
    },
    {
      "role": "user",
      "content": "什么是人工智能的发展历程？"
    }
  ],
  "context_summary": "用户之前询问了人工智能的定义，现在想了解其发展历程",
  "retrieved_documents": [
    {
      "id": "doc_ai_history_001",
      "content": "人工智能的发展历程可追溯至20世纪40-50年代。1950年，艾伦·图灵发表了《计算机器与智能》，提出了著名的图灵测试。1956年达特茅斯会议上，约翰·麦卡锡首次提出了\"人工智能\"这一术语，标志着人工智能作为一门学科正式诞生。",
      "score": 0.94,
      "source": "人工智能发展史概述.pdf",
      "page": 5,
      "timestamp": "2023-09-15"
    },
    {
      "id": "doc_ai_history_002",
      "content": "20世纪60-70年代，人工智能经历了早期发展和第一次低谷。这一时期开发了如SHRDLU等早期系统，但由于技术限制和过高期望，导致了70年代的\"人工智能冬天\"。80年代专家系统的兴起带来了短暂复苏，但90年代再次进入低谷。",
      "score": 0.88,
      "source": "人工智能发展史概述.pdf",
      "page": 6,
      "timestamp": "2023-09-15"
    },
    {
      "id": "doc_ai_history_003",
      "content": "21世纪以来，随着大数据、计算能力的提升和深度学习算法的突破，人工智能进入了快速发展期。2012年AlexNet在ImageNet竞赛中的成功标志着深度学习时代的到来，2016年AlphaGo击败李世石则让人工智能受到广泛关注。近年来，大型语言模型如GPT系列的发展进一步推动了人工智能的应用普及。",
      "score": 0.91,
      "source": "现代人工智能发展报告.pdf",
      "page": 12,
      "timestamp": "2023-06-20"
    }
  ],
  "retrieval_confidence": 0.92,
  "initial_answer": "人工智能的发展历程可追溯至20世纪40-50年代，经历了多个发展阶段：1. 诞生期(1940s-1950s)：1950年艾伦·图灵提出图灵测试，1956年达特茅斯会议首次提出\"人工智能\"术语；2. 早期发展与起伏期(1960s-1990s)：经历了早期发展、70年代第一次\"人工智能冬天\"、80年代专家系统带来的复苏和90年代第二次低谷；3. 快速发展期(21世纪至今)：随着大数据、计算能力提升和深度学习突破，人工智能进入快速发展阶段，2012年AlexNet标志深度学习时代到来，2016年AlphaGo事件引发广泛关注，近年来大型语言模型如GPT系列进一步推动了应用普及。",
  "citation_sources": [
    {
      "doc_id": "doc_ai_history_001",
      "quote": "1950年，艾伦·图灵发表了《计算机器与智能》，提出了著名的图灵测试。1956年达特茅斯会议上，约翰·麦卡锡首次提出了'人工智能'这一术语",
      "page": 5
    },
    {
      "doc_id": "doc_ai_history_002",
      "quote": "20世纪60-70年代，人工智能经历了早期发展和第一次低谷...导致了70年代的'人工智能冬天'。80年代专家系统的兴起带来了短暂复苏，但90年代再次进入低谷",
      "page": 6
    },
    {
      "doc_id": "doc_ai_history_003",
      "quote": "2012年AlexNet在ImageNet竞赛中的成功标志着深度学习时代的到来，2016年AlphaGo击败李世石则让人工智能受到广泛关注",
      "page": 12
    }
  ],
  "final_answer": "人工智能的发展历程可追溯至20世纪40-50年代，至今经历了多个关键发展阶段：\n\n### 1. 诞生期（1940s-1950s）\n1950年，艾伦·图灵发表了《计算机器与智能》，提出了著名的图灵测试，为人工智能奠定了理论基础[1]。1956年达特茅斯会议上，约翰·麦卡锡首次提出了\"人工智能\"这一术语，标志着人工智能作为一门独立学科正式诞生[1]。\n\n### 2. 早期发展与起伏期（1960s-1990s）\n20世纪60-70年代，人工智能经历了早期发展和第一次低谷。这一时期开发了如SHRDLU等早期系统，但由于技术限制和过高期望，导致了70年代的\"人工智能冬天\"[2]。80年代专家系统的兴起带来了短暂复苏，但90年代再次进入低谷[2]。\n\n### 3. 快速发展期（21世纪至今）\n随着大数据、计算能力的提升和深度学习算法的突破，人工智能进入了快速发展期。2012年AlexNet在ImageNet竞赛中的成功标志着深度学习时代的到来，2016年AlphaGo击败李世石则让人工智能受到广泛关注[3]。近年来，大型语言模型如GPT系列的发展进一步推动了人工智能的应用普及[3]。\n\n**参考来源**：\n[1] 人工智能发展史概述.pdf，第5页\n[2] 人工智能发展史概述.pdf，第6页\n[3] 现代人工智能发展报告.pdf，第12页",
  "answer_confidence": 0.91,
  "error_info": null,
  "node_execution_status": {
    "InputValidationNode": "completed",
    "QuestionUnderstandingNode": "completed",
    "ConversationMemoryNode": "completed",
    "DocumentRetrievalNode": "completed",
    "AnswerGenerationNode": "completed",
    "AnswerRefinementNode": "completed"
  }
}
```

---
*生成时间: 2025-08-06 09:56:28*
