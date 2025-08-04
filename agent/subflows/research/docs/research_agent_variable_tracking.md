# Research Agent 变量变化追踪

## 概述

本文档详细追踪 Research Agent 执行过程中共享变量的完整变化过程，包括每个节点调用前后的精确状态。

## 完整执行示例

### 初始状态

```python
# 子流程开始时的共享变量
subflow_shared = {
    "current_keyword": "Python编程",
    "analysis_requirements": "重点关注Python编程的基础概念和应用场景",
    "search_keywords": ["Python编程"],
    "max_search_results": 5,
    "first_search_result": {},
    "all_search_results": [],
    "url_content": "",
    "url_title": "",
    "url_metadata": {},
    "llm_analysis": {},
    "analyzed_keyword": "",
    "keyword_report": {}
}
```

## 节点执行详细追踪

### 🔍 NodeSearch 执行过程

#### Step 1: prep() 调用前
```python
shared_state = {
    "current_keyword": "Python编程",
    "search_keywords": ["Python编程"],  # ← prep()会读取这个
    "max_search_results": 5,
    # 其他字段为空...
}
```

#### Step 2: prep() 执行
```python
# prep()方法内部处理
search_keywords = shared.get("search_keywords", [])  # ["Python编程"]
max_results = shared.get("max_search_results", 10)   # 5

# prep()返回结果
prep_result = {
    "search_keywords": ["Python编程"],
    "search_type": "web",
    "max_results": 5,
    "language": "zh-CN",
    "original_keywords": ["Python编程"],
    "keyword_count": 1
}
```

#### Step 3: exec() 执行
```python
# exec()调用Jina搜索API
# 返回结果
exec_result = {
    "search_results": [
        {
            "title": "Python 教程— Python 3.13.5 文档",
            "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
            "snippet": "Python 是一门易于学习、功能强大的编程语言...",
            "search_keyword": "Python编程",
            "rank": 1,
            "source_type": "docs",
            "relevance_score": 0.8
        },
        # ... 9个更多结果
    ],
    "total_found": 10,
    "search_time": 1250,
    "keywords_processed": 1
}
```

#### Step 4: post() 调用前
```python
# 共享变量状态（未变）
shared_state = {
    "current_keyword": "Python编程",
    "search_keywords": ["Python编程"],
    "max_search_results": 5,
    "first_search_result": {},        # ← 即将被填充
    "all_search_results": [],         # ← 即将被填充
    # 其他字段仍为空...
}
```

#### Step 5: post() 执行后
```python
# post()更新共享变量
shared_state = {
    "current_keyword": "Python编程",
    "search_keywords": ["Python编程"],
    "max_search_results": 5,
    "first_search_result": {          # ✅ 新增
        "title": "Python 教程— Python 3.13.5 文档",
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
        "snippet": "Python 是一门易于学习、功能强大的编程语言...",
        "search_keyword": "Python编程",
        "rank": 1,
        "source_type": "docs",
        "relevance_score": 0.8
    },
    "all_search_results": [           # ✅ 新增
        {...}, {...}, {...}  # 10个搜索结果
    ],
    "url_content": "",
    "url_title": "",
    "url_metadata": {},
    "llm_analysis": {},
    "analyzed_keyword": "",
    "keyword_report": {}
}

# post()返回值
return "success"  # 触发流程进入下一个节点
```

### 📄 NodeURL 执行过程

#### Step 1: prep() 调用前
```python
shared_state = {
    # ... 前面的数据保持不变 ...
    "first_search_result": {
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html"  # ← prep()会读取这个
    },
    "url_content": "",                # ← 即将被填充
    "url_title": "",                  # ← 即将被填充
    "url_metadata": {}                # ← 即将被填充
}
```

#### Step 2: prep() 执行
```python
# prep()方法内部处理
first_search_result = shared.get("first_search_result", {})
url = first_search_result.get("url", "")  # 获取URL

# prep()返回结果
prep_result = {
    "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
    "extraction_type": "full",
    "target_selectors": [],
    "max_content_length": 10000,
    "parsed_url": ParseResult(...)
}
```

#### Step 3: exec() 执行
```python
# exec()调用Jina Web API
# 返回结果
exec_result = {
    "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
    "title": "Python 教程— Python 3.13.5 文档",
    "content": "Python 教程 — Python 3.13.5 文档\n\n...",  # 10000+字符
    "metadata": {
        "author": "",
        "publish_date": "",
        "tags": [],
        "description": "Python官方教程文档"
    },
    "extracted_sections": [...],
    "processing_status": "success",
    "processing_time": 2100,
    "content_length": 10003
}
```

#### Step 4: post() 执行后
```python
shared_state = {
    # ... 前面的数据保持不变 ...
    "url_content": "Python 教程 — Python 3.13.5 文档\n\n...",  # ✅ 新增
    "url_title": "Python 教程— Python 3.13.5 文档",              # ✅ 新增
    "url_metadata": {                                            # ✅ 新增
        "author": "",
        "publish_date": "",
        "tags": [],
        "description": "Python官方教程文档"
    },
    "llm_analysis": {},
    "analyzed_keyword": "",
    "keyword_report": {}
}

# post()返回值
return "success"  # 触发流程进入下一个节点
```

### 🤖 LLMAnalysisNode 执行过程

#### Step 1: prep() 调用前
```python
shared_state = {
    # ... 前面的数据保持不变 ...
    "url_content": "Python 教程 — Python 3.13.5 文档\n\n...",  # ← prep()会读取
    "current_keyword": "Python编程",                             # ← prep()会读取
    "analysis_requirements": "重点关注Python编程的基础概念...",    # ← prep()会读取
    "llm_analysis": {},               # ← 即将被填充
    "analyzed_keyword": ""            # ← 即将被填充
}
```

#### Step 2: prep() 执行
```python
# prep()方法内部处理
url_content = shared.get("url_content", "")
current_keyword = shared.get("current_keyword", "")
analysis_requirements = shared.get("analysis_requirements", "")

# prep()返回结果
prep_result = {
    "url_content": "Python 教程 — Python 3.13.5 文档\n\n...",
    "current_keyword": "Python编程",
    "analysis_requirements": "重点关注Python编程的基础概念和应用场景"
}
```

#### Step 3: exec() 执行
```python
# exec()调用LLM API进行分析
# 构建的prompt:
prompt = """
请分析以下网页内容，重点关注与关键词"Python编程"相关的信息。

分析需求：
重点关注Python编程的基础概念和应用场景

网页内容：
Python 教程 — Python 3.13.5 文档...

请以JSON格式返回分析结果：
{
    "key_insights": ["关键洞察1", "关键洞察2"],
    ...
}
"""

# exec()返回结果
exec_result = {
    "analysis": {
        "key_insights": [
            "Python被设计为易于学习且功能强大的编程语言，适合有编程基础的学习者",
            "Python适用于脚本编写和快速应用开发，支持面向对象编程"
        ],
        "relevant_information": "Python是一种解释型、高级编程语言，具有简洁的语法...",
        "technical_details": [
            "Python支持多种编程范式，包括面向对象、函数式和过程式编程",
            "Python拥有丰富的标准库和第三方包生态系统"
        ],
        "recommendations": [
            "建议从基础语法开始学习，逐步掌握高级特性",
            "多做实践项目，结合理论学习"
        ],
        "relevance_score": 0.9,
        "summary": "Python教程内容全面介绍了Python编程语言的基础概念和应用"
    },
    "keyword": "Python编程"
}
```

#### Step 4: post() 执行后
```python
shared_state = {
    # ... 前面的数据保持不变 ...
    "llm_analysis": {                 # ✅ 新增
        "key_insights": [
            "Python被设计为易于学习且功能强大的编程语言，适合有编程基础的学习者",
            "Python适用于脚本编写和快速应用开发，支持面向对象编程"
        ],
        "relevant_information": "Python是一种解释型、高级编程语言，具有简洁的语法...",
        "technical_details": [
            "Python支持多种编程范式，包括面向对象、函数式和过程式编程",
            "Python拥有丰富的标准库和第三方包生态系统"
        ],
        "recommendations": [
            "建议从基础语法开始学习，逐步掌握高级特性",
            "多做实践项目，结合理论学习"
        ],
        "relevance_score": 0.9,
        "summary": "Python教程内容全面介绍了Python编程语言的基础概念和应用"
    },
    "analyzed_keyword": "Python编程",  # ✅ 新增
    "keyword_report": {}
}

# post()返回值
return "success"  # 触发流程进入下一个节点
```

### 📊 ResultAssemblyNode 执行过程

#### Step 1: prep() 调用前
```python
shared_state = {
    # 所有前面步骤的数据都已准备好
    "current_keyword": "Python编程",
    "first_search_result": {...},
    "url_content": "Python 教程 — Python 3.13.5 文档\n\n...",
    "llm_analysis": {...},
    "keyword_report": {}              # ← 即将被填充（最终产物）
}
```

#### Step 2: prep() 执行
```python
# prep()收集所有相关数据
prep_result = {
    "keyword": "Python编程",
    "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
    "title": "Python 教程— Python 3.13.5 文档",
    "content": "Python 教程 — Python 3.13.5 文档\n\n...",
    "analysis": {
        "key_insights": [...],
        "relevant_information": "...",
        "technical_details": [...],
        "recommendations": [...],
        "relevance_score": 0.9,
        "summary": "..."
    }
}
```

#### Step 3: exec() 执行
```python
# exec()组装最终报告
exec_result = {
    "keyword_report": {
        "keyword": "Python编程",
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
        "title": "Python 教程— Python 3.13.5 文档",
        "content": "Python 教程 — Python 3.13.5 文档...",  # 截取前1000字符
        "analysis": {
            "key_insights": [
                "Python被设计为易于学习且功能强大的编程语言，适合有编程基础的学习者",
                "Python适用于脚本编写和快速应用开发，支持面向对象编程"
            ],
            "relevant_information": "Python是一种解释型、高级编程语言...",
            "technical_details": [
                "Python支持多种编程范式，包括面向对象、函数式和过程式编程",
                "Python拥有丰富的标准库和第三方包生态系统"
            ],
            "recommendations": [
                "建议从基础语法开始学习，逐步掌握高级特性",
                "多做实践项目，结合理论学习"
            ],
            "relevance_score": 0.9,
            "summary": "Python教程内容全面介绍了Python编程语言的基础概念和应用"
        },
        "processed_at": 1704067200.123
    }
}
```

#### Step 4: post() 执行后（最终状态）
```python
shared_state = {
    "current_keyword": "Python编程",
    "analysis_requirements": "重点关注Python编程的基础概念和应用场景",
    "search_keywords": ["Python编程"],
    "max_search_results": 5,
    "first_search_result": {
        "title": "Python 教程— Python 3.13.5 文档",
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
        "snippet": "Python 是一门易于学习、功能强大的编程语言...",
        "search_keyword": "Python编程",
        "rank": 1,
        "source_type": "docs",
        "relevance_score": 0.8
    },
    "all_search_results": [...],  # 10个搜索结果
    "url_content": "Python 教程 — Python 3.13.5 文档\n\n...",
    "url_title": "Python 教程— Python 3.13.5 文档",
    "url_metadata": {
        "author": "",
        "publish_date": "",
        "tags": [],
        "description": "Python官方教程文档"
    },
    "llm_analysis": {
        "key_insights": [...],
        "relevant_information": "...",
        "technical_details": [...],
        "recommendations": [...],
        "relevance_score": 0.9,
        "summary": "..."
    },
    "analyzed_keyword": "Python编程",
    "keyword_report": {               # ✅ 最终产物
        "keyword": "Python编程",
        "url": "https://docs.python.org/zh-cn/3.13/tutorial/index.html",
        "title": "Python 教程— Python 3.13.5 文档",
        "content": "Python 教程 — Python 3.13.5 文档...",
        "analysis": {...},
        "processed_at": 1704067200.123
    }
}

# post()返回值
return "success"  # 流程结束
```

## 变化总结

### 数据累积过程
1. **初始**: 12个字段，全部为空或默认值
2. **搜索后**: +2个字段有数据 (`first_search_result`, `all_search_results`)
3. **URL解析后**: +3个字段有数据 (`url_content`, `url_title`, `url_metadata`)
4. **LLM分析后**: +2个字段有数据 (`llm_analysis`, `analyzed_keyword`)
5. **结果组装后**: +1个字段有数据 (`keyword_report`) - **最终目标**

### 关键观察
- **渐进式构建**: 每个节点只添加自己的数据，不修改前面的数据
- **数据依赖**: 后续节点依赖前面节点的输出
- **错误隔离**: 任何节点失败都会中断流程，但不影响其他关键词
- **最终产物**: `keyword_report` 是整个子流程的最终输出

## 主流程共享状态变化

### ProcessResearch 节点执行过程

#### 主流程调用前的共享状态
```python
# 主流程的shared对象（来自GTPlanner）
shared = {
    "user_intent": {
        "extracted_keywords": ["Python", "机器学习", "API"]
    },
    "structured_requirements": {
        "project_overview": {
            "title": "智能数据分析平台",
            "description": "基于机器学习的数据分析平台",
            "objectives": ["提高数据处理效率", "实现智能分析"]
        },
        "functional_requirements": {
            "core_features": [
                {"name": "数据导入"},
                {"name": "模型训练"}
            ]
        }
    },
    "research_findings": None,        # ← 即将被创建
    "current_stage": "requirements_completed"
}
```

#### ProcessResearch.prep() 执行
```python
# 从主流程共享状态提取研究关键词
prep_result = {
    "research_keywords": ["数据导入", "模型训练", "API", "智能数据分析平台", "Python"],
    "requirements": {
        "project_title": "智能数据分析平台",
        "project_description": "基于机器学习的数据分析平台",
        "objectives": ["提高数据处理效率", "实现智能分析"]
    },
    "total_keywords": 5
}
```

#### ProcessResearch.exec() 执行
```python
# 对每个关键词执行子流程，收集结果
exec_result = {
    "keywords": ["数据导入", "模型训练", "API", "智能数据分析平台", "Python"],
    "result": {
        "success": True,
        "research_report": [
            {
                "keyword": "数据导入",
                "url": "https://example.com/data-import",
                "analysis": {...}
            },
            {
                "keyword": "模型训练",
                "url": "https://example.com/model-training",
                "analysis": {...}
            },
            # ... 更多关键词报告
        ],
        "aggregated_summary": {
            "overall_summary": "完成了5个关键词的研究分析，平均相关性: 0.85",
            "key_findings": [...],
            "technical_insights": [...],
            "recommendations": [...],
            "coverage_analysis": {
                "total_keywords": 5,
                "successful_keywords": 4,
                "average_relevance": 0.85
            }
        },
        "total_keywords": 5,
        "successful_keywords": 4
    },
    "processing_success": True,
    "research_report": [...],
    "aggregated_summary": {...},
    "successful_keywords": 4,
    "total_keywords": 5
}
```

#### ProcessResearch.post() 执行后的主流程共享状态
```python
shared = {
    "user_intent": {
        "extracted_keywords": ["Python", "机器学习", "API"]
    },
    "structured_requirements": {...},  # 保持不变
    "research_findings": {            # ✅ 新创建的研究发现
        "research_report": [
            {
                "keyword": "数据导入",
                "url": "https://example.com/data-import",
                "title": "数据导入最佳实践",
                "content": "数据导入是数据分析的第一步...",
                "analysis": {
                    "key_insights": ["数据质量是关键", "支持多种格式"],
                    "technical_details": ["ETL流程", "数据验证"],
                    "recommendations": ["建立数据标准", "自动化处理"],
                    "relevance_score": 0.9
                }
            },
            {
                "keyword": "模型训练",
                "url": "https://example.com/model-training",
                "title": "机器学习模型训练指南",
                "content": "模型训练是机器学习的核心...",
                "analysis": {
                    "key_insights": ["数据预处理重要", "超参数调优"],
                    "technical_details": ["交叉验证", "正则化"],
                    "recommendations": ["使用GPU加速", "监控训练过程"],
                    "relevance_score": 0.85
                }
            }
            // ... 更多关键词报告
        ],
        "aggregated_summary": {
            "overall_summary": "完成了5个关键词的研究分析，平均相关性: 0.85",
            "key_findings": [
                "数据质量是数据分析成功的关键因素",
                "机器学习模型需要大量高质量数据进行训练",
                "API设计应该考虑可扩展性和安全性",
                "智能数据分析平台需要集成多种算法"
            ],
            "technical_insights": [
                "ETL流程是数据处理的标准方法",
                "深度学习模型需要GPU加速",
                "RESTful API是主流的接口设计方式",
                "微服务架构适合大型数据平台"
            ],
            "recommendations": [
                "建立完善的数据治理体系",
                "采用云原生技术栈",
                "实施DevOps最佳实践",
                "重视数据安全和隐私保护"
            ],
            "coverage_analysis": {
                "total_keywords": 5,
                "successful_keywords": 4,
                "average_relevance": 0.85,
                "high_quality_results": 3
            }
        },
        "research_metadata": {        # ✅ 新增研究元数据
            "research_keywords": ["数据导入", "模型训练", "API", "智能数据分析平台", "Python"],
            "total_keywords": 5,
            "successful_keywords": 4,
            "success_rate": 0.8,
            "research_completed_at": 1704067200.123,
            "research_success": True
        }
    },
    "current_stage": "research_completed",  # ✅ 阶段更新
    "system_messages": [              # ✅ 新增系统消息
        {
            "message": "研究调研完成，成功处理 4/5 个关键词",
            "agent_source": "ProcessResearch",
            "timestamp": 1704067200.123,
            "keywords": ["数据导入", "模型训练", "API", "智能数据分析平台", "Python"],
            "successful_keywords": 4,
            "total_keywords": 5,
            "success": True
        }
    ]
}
```

### 主流程状态变化总结

#### 新增的主要数据结构
1. **research_findings**: 完整的研究发现对象
   - `research_report`: 每个关键词的详细报告数组
   - `aggregated_summary`: 聚合后的总结和洞察
   - `research_metadata`: 研究过程的元数据

2. **阶段更新**: `current_stage` 从 "requirements_completed" 更新为 "research_completed"

3. **系统消息**: 添加研究完成的系统消息记录

#### 数据规模
- **输入**: 5个关键词
- **处理**: 每个关键词执行完整的4步子流程
- **输出**: 4个成功的关键词报告 + 1个聚合总结
- **数据量**: 约40+个洞察，30+个技术细节，25+个建议

---

*本文档提供了 Research Agent 执行过程中变量变化的完整追踪记录，包括子流程和主流程的详细状态变化。*
