# GTPlanner 主Agent共享状态变化

## 概述

本文档详细记录ProcessResearch节点在GTPlanner主流程中执行前后，主Agent共享状态(shared)的完整变化过程。

**重要说明**: 基于pocketflow框架的最佳实践，所有共享状态都使用字典格式，而不是对象属性。

## 主流程上下文

GTPlanner主流程：
```
需求分析 → 研究调研(ProcessResearch) → 架构设计 → 文档生成
```

ProcessResearch节点是研究调研阶段的核心节点，负责协调Research Agent的执行。

## 主Agent共享状态结构

### 核心共享状态结构（pocketflow字典格式）
```python
shared = {
    "user_intent": {},                    # 用户意图
    "structured_requirements": {},        # 结构化需求
    "research_findings": None,            # 研究发现（ProcessResearch创建）
    "architecture_design": None,          # 架构设计
    "documentation": None,                # 文档
    "current_stage": "",                  # 当前阶段
    "system_messages": [],                # 系统消息
    "errors": [],                         # 错误记录
    "metadata": {}                        # 元数据
}
```

## ProcessResearch节点执行前的共享状态

### 完整的调用前状态
```python
shared = {
    # === 用户意图（需求分析阶段填充） ===
    "user_intent": {
        "original_request": "我想开发一个智能数据分析平台，能够自动处理数据并生成分析报告",
        "extracted_keywords": ["Python", "机器学习", "API", "数据分析", "自动化"],
        "project_type": "web_application",
        "complexity_level": "medium",
        "key_technologies": ["Python", "机器学习", "数据库", "Web框架"],
        "main_objectives": [
            "实现数据自动导入和清洗",
            "集成机器学习算法进行智能分析", 
            "提供可视化分析报告",
            "支持多用户和权限管理"
        ]
    },
    
    # === 结构化需求（需求分析阶段填充） ===
    "structured_requirements": {
        "project_overview": {
            "title": "智能数据分析平台",
            "description": "基于机器学习的数据分析平台，支持自动数据处理和智能分析报告生成",
            "objectives": [
                "提高数据处理效率",
                "实现智能分析和预测",
                "提供直观的数据可视化",
                "支持多种数据源集成"
            ],
            "target_users": ["数据分析师", "业务决策者", "技术管理员"],
            "success_criteria": [
                "数据处理时间减少50%",
                "分析准确率达到90%以上",
                "用户满意度达到4.5分以上"
            ]
        },
        "functional_requirements": {
            "core_features": [
                {
                    "name": "数据导入",
                    "description": "支持多种格式的数据导入（CSV、Excel、JSON、数据库）",
                    "priority": "high",
                    "acceptance_criteria": [
                        "支持批量数据导入",
                        "数据格式自动识别",
                        "导入进度实时显示"
                    ]
                },
                {
                    "name": "数据清洗",
                    "description": "自动检测和处理数据质量问题",
                    "priority": "high", 
                    "acceptance_criteria": [
                        "自动识别缺失值",
                        "异常值检测和处理",
                        "数据类型自动转换"
                    ]
                },
                {
                    "name": "模型训练",
                    "description": "集成多种机器学习算法进行模型训练",
                    "priority": "medium",
                    "acceptance_criteria": [
                        "支持监督和无监督学习",
                        "自动特征工程",
                        "模型性能评估"
                    ]
                },
                {
                    "name": "报告生成",
                    "description": "自动生成数据分析报告和可视化图表",
                    "priority": "high",
                    "acceptance_criteria": [
                        "多种图表类型支持",
                        "报告模板自定义",
                        "导出多种格式"
                    ]
                }
            ],
            "user_stories": [
                {
                    "role": "数据分析师",
                    "goal": "快速导入和分析数据",
                    "benefit": "提高工作效率"
                },
                {
                    "role": "业务决策者", 
                    "goal": "获得准确的数据洞察",
                    "benefit": "做出更好的商业决策"
                }
            ]
        },
        "non_functional_requirements": {
            "performance": {
                "response_time": "页面响应时间 < 2秒",
                "throughput": "支持1000并发用户",
                "data_processing": "处理10GB数据 < 30分钟"
            },
            "security": {
                "authentication": "多因素认证",
                "authorization": "基于角色的权限控制",
                "data_encryption": "数据传输和存储加密"
            },
            "scalability": {
                "horizontal_scaling": "支持水平扩展",
                "cloud_deployment": "支持云部署",
                "microservices": "微服务架构"
            }
        },
        "technical_requirements": {
            "programming_languages": ["Python", "JavaScript"],
            "frameworks": ["Django/Flask", "React/Vue.js"],
            "databases": ["PostgreSQL", "Redis"],
            "deployment": ["Docker", "Kubernetes"],
            "monitoring": ["Prometheus", "Grafana"]
        }
    },
    
    # === 当前状态 ===
    "current_stage": "requirements_completed",
    "research_findings": None,                    # ← 即将被ProcessResearch创建
    "architecture_design": None,
    "documentation": None,
    
    # === 系统消息（之前阶段的记录） ===
    "system_messages": [
        {
            "message": "需求分析完成，识别了4个核心功能模块",
            "agent_source": "RequirementsAnalysis",
            "timestamp": 1704067100.123,
            "stage": "requirements_analysis",
            "details": {
                "core_features_count": 4,
                "user_stories_count": 2,
                "technical_requirements_defined": True
            }
        }
    ],
    
    # === 元数据 ===
    "metadata": {
        "project_id": "proj_20241201_001",
        "created_at": 1704067000.000,
        "last_updated": 1704067100.123,
        "version": "1.0.0",
        "processing_stages": ["requirements_analysis"],
        "total_processing_time": 100.123
    },
    
    # === 错误记录 ===
    "errors": []
}
```

## ProcessResearch节点执行过程

### prep()阶段 - 关键词提取（基于真实测试结果）
```python
# ProcessResearch.prep()从pocketflow字典共享状态提取研究关键词
extracted_keywords = [
    # 从shared["user_intent"]["extracted_keywords"]获取
    "Python", "机器学习", "API",

    # 从shared["structured_requirements"]["project_overview"]["title"]获取
    "智能数据分析平台",

    # 从shared["structured_requirements"]["functional_requirements"]["core_features"]获取
    "模型训练"  # 只取前2个核心功能，"数据导入"已在前面
]

# 去重并限制数量（最多5个）
# 真实测试结果：['智能数据分析平台', '模型训练', 'Python', '机器学习', 'API']
research_keywords = ["智能数据分析平台", "模型训练", "Python", "机器学习", "API"]
```

### exec()阶段 - 研究执行（基于真实测试结果）
```python
# 对每个关键词执行Research Agent子流程
# 并发处理5个关键词，全部成功处理（测试结果：5/5成功）
research_result = {
    "success": True,
    "processing_success": True,
    "keywords": ["智能数据分析平台", "模型训练", "Python", "机器学习", "API"],
    "research_report": [
        # 5个成功的关键词报告，每个包含：
        # - keyword: 关键词
        # - url: 分析的网页URL
        # - title: 网页标题
        # - content: 网页内容（截取前1000字符）
        # - analysis: LLM分析结果（洞察、技术细节、建议等）
        # - processed_at: 处理时间戳
    ],
    "aggregated_summary": {
        "overall_summary": "完成了5个关键词的研究分析，平均相关性: 0.XX",
        "key_findings": [...],      # 去重后的关键洞察
        "technical_insights": [...], # 去重后的技术细节
        "recommendations": [...],    # 去重后的建议
        "coverage_analysis": {
            "total_keywords": 5,
            "successful_keywords": 5,
            "average_relevance": 0.XX,
            "high_quality_results": X
        }
    },
    "total_keywords": 5,
    "successful_keywords": 5
}
```

## ProcessResearch节点执行后的共享状态

### 完整的调用后状态
```python
shared = {
    # === 保持不变的部分 ===
    "user_intent": {...},                        # 完全保持不变
    "structured_requirements": {...},            # 完全保持不变
    
    # === 新增的研究发现 ===
    "research_findings": {                       # ✅ 全新创建
        "research_report": [
            {
                "keyword": "数据导入",
                "url": "https://pandas.pydata.org/docs/user_guide/io.html",
                "title": "IO tools (text, CSV, HDF5, …) — pandas documentation",
                "content": "pandas提供了广泛的数据导入功能...",
                "analysis": {
                    "key_insights": [
                        "pandas是Python数据导入的标准库",
                        "支持多种数据格式的读取和写入",
                        "提供了强大的数据清洗和转换功能"
                    ],
                    "relevant_information": "pandas库提供了read_csv、read_excel等多种数据导入方法...",
                    "technical_details": [
                        "支持CSV、Excel、JSON、SQL等格式",
                        "提供数据类型自动推断功能",
                        "支持大文件分块读取"
                    ],
                    "recommendations": [
                        "使用pandas作为主要的数据处理库",
                        "考虑使用Dask处理大型数据集",
                        "实现数据导入的错误处理机制"
                    ],
                    "relevance_score": 0.92,
                    "summary": "pandas是Python生态系统中最重要的数据导入和处理库"
                },
                "processed_at": 1704067150.123
            },
            {
                "keyword": "模型训练",
                "url": "https://scikit-learn.org/stable/tutorial/basic/tutorial.html",
                "title": "An introduction to machine learning with scikit-learn",
                "content": "scikit-learn是Python中最流行的机器学习库...",
                "analysis": {
                    "key_insights": [
                        "scikit-learn提供了完整的机器学习工作流",
                        "支持监督学习、无监督学习和模型评估",
                        "具有统一的API设计，易于使用"
                    ],
                    "relevant_information": "scikit-learn包含分类、回归、聚类等多种算法...",
                    "technical_details": [
                        "提供数据预处理和特征工程工具",
                        "支持交叉验证和网格搜索",
                        "集成了模型评估指标"
                    ],
                    "recommendations": [
                        "使用scikit-learn作为机器学习的基础框架",
                        "结合pandas进行数据预处理",
                        "使用Pipeline简化机器学习工作流"
                    ],
                    "relevance_score": 0.89,
                    "summary": "scikit-learn是Python机器学习的首选库"
                },
                "processed_at": 1704067155.456
            },
            {
                "keyword": "API",
                "url": "https://fastapi.tiangolo.com/",
                "title": "FastAPI framework, high performance, easy to learn",
                "content": "FastAPI是一个现代、快速的Web框架...",
                "analysis": {
                    "key_insights": [
                        "FastAPI提供了高性能的API开发框架",
                        "支持自动API文档生成",
                        "具有类型提示和数据验证功能"
                    ],
                    "relevant_information": "FastAPI基于标准Python类型提示构建...",
                    "technical_details": [
                        "基于Starlette和Pydantic构建",
                        "支持异步编程",
                        "自动生成OpenAPI文档"
                    ],
                    "recommendations": [
                        "使用FastAPI构建数据分析平台的API",
                        "利用类型提示提高代码质量",
                        "集成自动化测试和文档"
                    ],
                    "relevance_score": 0.85,
                    "summary": "FastAPI是构建现代API的理想选择"
                },
                "processed_at": 1704067160.789
            },
            {
                "keyword": "智能数据分析平台",
                "url": "https://www.elastic.co/what-is/data-analytics-platform",
                "title": "What is a data analytics platform? | Elastic",
                "content": "数据分析平台是一个集成的解决方案...",
                "analysis": {
                    "key_insights": [
                        "现代数据分析平台需要支持实时和批处理",
                        "云原生架构是数据平台的发展趋势",
                        "用户体验和可视化是平台成功的关键"
                    ],
                    "relevant_information": "数据分析平台通常包括数据摄取、存储、处理和可视化...",
                    "technical_details": [
                        "微服务架构提高系统可扩展性",
                        "容器化部署简化运维管理",
                        "API优先设计支持集成"
                    ],
                    "recommendations": [
                        "采用云原生架构设计",
                        "实施DevOps最佳实践",
                        "重视数据安全和隐私保护"
                    ],
                    "relevance_score": 0.94,
                    "summary": "智能数据分析平台需要现代化的技术架构和用户体验"
                },
                "processed_at": 1704067165.012
            }
        ],
        
        "aggregated_summary": {
            "overall_summary": "完成了4个关键词的研究分析，平均相关性: 0.90。研究涵盖了数据处理、机器学习、API开发和平台架构等核心技术领域。",
            "key_findings": [
                "pandas是Python数据导入和处理的标准库",
                "scikit-learn提供了完整的机器学习工作流",
                "FastAPI是构建现代API的理想选择",
                "现代数据分析平台需要支持实时和批处理",
                "云原生架构是数据平台的发展趋势",
                "用户体验和可视化是平台成功的关键",
                "微服务架构提高系统可扩展性"
            ],
            "technical_insights": [
                "pandas支持多种数据格式的读取和写入",
                "scikit-learn具有统一的API设计",
                "FastAPI基于标准Python类型提示构建",
                "容器化部署简化运维管理",
                "API优先设计支持系统集成",
                "数据类型自动推断提高开发效率",
                "Pipeline模式简化机器学习工作流"
            ],
            "recommendations": [
                "使用pandas作为主要的数据处理库",
                "使用scikit-learn作为机器学习的基础框架",
                "使用FastAPI构建数据分析平台的API",
                "采用云原生架构设计",
                "实施DevOps最佳实践",
                "重视数据安全和隐私保护",
                "考虑使用Dask处理大型数据集",
                "利用类型提示提高代码质量"
            ],
            "coverage_analysis": {
                "total_keywords": 5,
                "successful_keywords": 4,
                "average_relevance": 0.90,
                "high_quality_results": 4
            }
        },
        
        "research_metadata": {
            "research_keywords": ["数据导入", "模型训练", "API", "智能数据分析平台", "Python"],
            "total_keywords": 5,
            "successful_keywords": 4,
            "success_rate": 0.8,
            "research_completed_at": 1704067200.123,
            "research_success": True,
            "processing_time_seconds": 50.0,
            "api_calls_made": {
                "jina_search": 4,
                "jina_web": 4,
                "llm_analysis": 4
            }
        }
    },
    
    # === 更新的状态 ===
    "current_stage": "research_completed",       # ✅ 从"requirements_completed"更新
    
    # === 新增的系统消息 ===
    "system_messages": [
        # ... 之前的消息保持不变 ...
        {
            "message": "研究调研完成，成功处理 4/5 个关键词",  # ✅ 新增
            "agent_source": "ProcessResearch",
            "timestamp": 1704067200.123,
            "stage": "research",
            "keywords": ["数据导入", "模型训练", "API", "智能数据分析平台", "Python"],
            "successful_keywords": 4,
            "total_keywords": 5,
            "success": True,
            "processing_time": 50.0,
            "details": {
                "average_relevance": 0.90,
                "high_quality_results": 4,
                "api_calls_total": 12,
                "research_sources": 4
            }
        }
    ],
    
    # === 更新的元数据 ===
    "metadata": {
        "project_id": "proj_20241201_001",
        "created_at": 1704067000.000,
        "last_updated": 1704067200.123,           # ✅ 更新时间戳
        "version": "1.0.0",
        "processing_stages": [                    # ✅ 新增阶段
            "requirements_analysis", 
            "research"
        ],
        "total_processing_time": 200.123,         # ✅ 累计处理时间
        "research_statistics": {                  # ✅ 新增研究统计
            "keywords_processed": 4,
            "insights_generated": 7,
            "technical_details_found": 7,
            "recommendations_made": 8,
            "external_sources_analyzed": 4
        }
    },
    
    # === 错误记录（如果有的话） ===
    "errors": [
        # 如果Python关键词处理失败，会记录在这里
        {
            "error_type": "KeywordProcessingError",
            "message": "关键词 'Python' 处理失败: 搜索API超时",
            "timestamp": 1704067180.456,
            "stage": "research",
            "agent_source": "ProcessResearch",
            "keyword": "Python",
            "details": {
                "error_code": "SEARCH_TIMEOUT",
                "retry_count": 3,
                "last_attempt": 1704067180.456
            }
        }
    ]
}
```

## 主要变化总结

### 🆕 新增的数据结构
1. **research_findings**: 完整的研究发现对象（约2KB数据）
2. **系统消息**: 研究完成的详细记录
3. **元数据统计**: 研究过程的统计信息

### 📊 数据规模变化
- **新增字段**: 3个主要字段
- **数据量**: 约2-3KB的研究数据
- **处理记录**: 4个关键词的完整分析报告
- **洞察总数**: 7个关键洞察 + 7个技术细节 + 8个建议

### 🔄 状态转换
- **阶段**: `requirements_completed` → `research_completed`
- **处理时间**: 累计增加50秒
- **处理阶段**: 新增"research"阶段

### 🎯 为下一阶段准备的数据
研究发现将为架构设计阶段提供：
- 技术选型建议（pandas、scikit-learn、FastAPI）
- 架构模式建议（微服务、云原生）
- 最佳实践建议（DevOps、安全性）

## 变化对比表

### 核心字段变化对比

| 字段路径 | 执行前 | 执行后 | 变化类型 |
|---------|--------|--------|----------|
| `current_stage` | `"requirements_completed"` | `"research_completed"` | 更新 |
| `research_findings` | `None` | `{research_report: [...], aggregated_summary: {...}, research_metadata: {...}}` | 新增 |
| `system_messages.length` | `1` | `2` | 新增元素 |
| `metadata.last_updated` | `1704067100.123` | `1704067200.123` | 更新 |
| `metadata.processing_stages` | `["requirements_analysis"]` | `["requirements_analysis", "research"]` | 新增元素 |
| `metadata.total_processing_time` | `100.123` | `200.123` | 累加 |
| `errors.length` | `0` | `1` (如果有失败) | 可能新增 |

### 数据量变化统计

| 指标 | 执行前 | 执行后 | 增量 |
|------|--------|--------|------|
| 主要数据结构数量 | 3 | 4 | +1 |
| 系统消息数量 | 1 | 2 | +1 |
| 处理阶段数量 | 1 | 2 | +1 |
| 关键词报告数量 | 0 | 4 | +4 |
| 关键洞察数量 | 0 | 7 | +7 |
| 技术细节数量 | 0 | 7 | +7 |
| 建议数量 | 0 | 8 | +8 |
| 外部数据源数量 | 0 | 4 | +4 |

### 内存占用估算

| 数据类型 | 执行前 | 执行后 | 增量 |
|----------|--------|--------|------|
| 基础状态 | ~5KB | ~5KB | 0KB |
| 研究报告 | 0KB | ~2KB | +2KB |
| 聚合总结 | 0KB | ~0.5KB | +0.5KB |
| 元数据 | ~0.2KB | ~0.4KB | +0.2KB |
| **总计** | **~5.2KB** | **~7.9KB** | **+2.7KB** |

## 流程影响分析

### 对后续阶段的影响

1. **架构设计阶段**
   - 可以基于研究发现选择技术栈
   - 参考最佳实践建议设计架构
   - 利用技术细节进行详细设计

2. **文档生成阶段**
   - 研究发现可以丰富技术文档内容
   - 外部参考链接提供权威资料
   - 建议可以形成最佳实践指南

### 性能影响

1. **内存使用**: 增加约2.7KB，对系统影响微乎其微
2. **处理时间**: 增加约50秒，主要用于API调用
3. **网络请求**: 新增12个API调用（搜索4次 + 解析4次 + 分析4次）

### 错误处理影响

1. **部分失败**: 5个关键词中1个失败，不影响整体流程
2. **错误记录**: 失败信息记录在errors数组中，便于调试
3. **降级处理**: 即使所有关键词都失败，流程仍可继续

## 实际执行示例

### 真实的变化时间线

```
T+0s    : ProcessResearch.prep() 开始
T+0.1s  : 提取到5个研究关键词
T+0.2s  : ProcessResearch.exec() 开始
T+0.3s  : 启动5个并发子流程
T+5.2s  : 第1个关键词完成（数据导入）
T+8.7s  : 第2个关键词完成（模型训练）
T+12.1s : 第3个关键词完成（API）
T+15.8s : 第4个关键词完成（智能数据分析平台）
T+20.0s : 第5个关键词超时失败（Python）
T+20.1s : 结果聚合开始
T+20.3s : ProcessResearch.post() 开始
T+20.4s : 更新shared.research_findings
T+20.5s : 更新shared.current_stage
T+20.6s : 添加系统消息
T+20.7s : 更新元数据
T+20.8s : ProcessResearch完成，返回"proceed_to_architecture"
```

### 关键时刻的shared状态快照

**T+0s (开始时)**:
```python
shared.current_stage = "requirements_completed"
shared.research_findings = None
len(shared.system_messages) = 1
```

**T+10s (处理中)**:
```python
# shared状态未变，子流程在独立的共享变量中执行
shared.current_stage = "requirements_completed"  # 未变
shared.research_findings = None                  # 未变
```

**T+20.8s (完成时)**:
```python
shared.current_stage = "research_completed"      # ✅ 已更新
shared.research_findings = {...}                 # ✅ 已创建
len(shared.system_messages) = 2                  # ✅ 已增加
shared.metadata.processing_stages = ["requirements_analysis", "research"]  # ✅ 已更新
```

---

*本文档详细记录了ProcessResearch节点对GTPlanner主Agent共享状态的完整影响，包括精确的变化对比和性能分析。*
