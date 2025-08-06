"""
用户意图分析数据模型

定义用户意图相关的数据结构。
"""

from typing import List
from dataclasses import dataclass, field


@dataclass
class UserIntent:
    """用户意图分析"""
    primary_goal: str = ""
    intent_category: str = ""  # "planning" | "analysis" | "design" | "research"
    confidence_level: float = 0.0
    extracted_keywords: List[str] = field(default_factory=list)
    domain_context: str = ""
    complexity_level: str = "medium"  # "simple" | "medium" | "complex"
    last_updated: str = ""

    def add_keyword(self, keyword: str):
        """添加关键词"""
        if keyword and keyword not in self.extracted_keywords:
            self.extracted_keywords.append(keyword)

    def update_confidence(self, confidence: float):
        """更新置信度"""
        self.confidence_level = max(0.0, min(1.0, confidence))

    def is_high_confidence(self) -> bool:
        """判断是否为高置信度"""
        return self.confidence_level >= 0.7

    def is_complex_task(self) -> bool:
        """判断是否为复杂任务"""
        return self.complexity_level == "complex"
