"""
研究调研数据模型

定义研究调研相关的数据结构。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class ResearchSource:
    """研究信息源"""
    source_id: str
    title: str
    url: str
    content_summary: str
    relevance_score: float
    credibility_score: float
    extracted_insights: List[str] = field(default_factory=list)
    key_data_points: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if not self.source_id:
            self.source_id = str(uuid.uuid4())[:12]

    def add_insight(self, insight: str):
        """添加洞察"""
        if insight and insight not in self.extracted_insights:
            self.extracted_insights.append(insight)

    def add_data_point(self, data_point: str):
        """添加关键数据点"""
        if data_point and data_point not in self.key_data_points:
            self.key_data_points.append(data_point)

    def is_high_relevance(self) -> bool:
        """判断是否为高相关性"""
        return self.relevance_score >= 0.7

    def is_credible(self) -> bool:
        """判断是否可信"""
        return self.credibility_score >= 0.6


@dataclass
class ResearchTopic:
    """研究主题"""
    topic: str
    sources: List[ResearchSource] = field(default_factory=list)
    topic_synthesis: str = ""
    recommendations: List[str] = field(default_factory=list)

    def add_source(self, source: ResearchSource):
        """添加信息源"""
        if source not in self.sources:
            self.sources.append(source)

    def add_recommendation(self, recommendation: str):
        """添加建议"""
        if recommendation and recommendation not in self.recommendations:
            self.recommendations.append(recommendation)

    def get_high_relevance_sources(self) -> List[ResearchSource]:
        """获取高相关性信息源"""
        return [s for s in self.sources if s.is_high_relevance()]

    def get_credible_sources(self) -> List[ResearchSource]:
        """获取可信信息源"""
        return [s for s in self.sources if s.is_credible()]

    def get_average_relevance(self) -> float:
        """获取平均相关性"""
        if not self.sources:
            return 0.0
        return sum(s.relevance_score for s in self.sources) / len(self.sources)

    def get_average_credibility(self) -> float:
        """获取平均可信度"""
        if not self.sources:
            return 0.0
        return sum(s.credibility_score for s in self.sources) / len(self.sources)


@dataclass
class ResearchFindings:
    """研究发现结果"""
    research_summary: Dict[str, Any] = field(default_factory=dict)
    findings_by_topic: List[ResearchTopic] = field(default_factory=list)
    cross_topic_insights: List[str] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    research_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_topic(self, topic_name: str) -> ResearchTopic:
        """添加研究主题"""
        topic = ResearchTopic(topic=topic_name)
        self.findings_by_topic.append(topic)
        return topic

    def get_topic(self, topic_name: str) -> ResearchTopic:
        """获取指定主题"""
        for topic in self.findings_by_topic:
            if topic.topic == topic_name:
                return topic
        # 如果不存在则创建
        return self.add_topic(topic_name)

    def add_cross_topic_insight(self, insight: str):
        """添加跨主题洞察"""
        if insight and insight not in self.cross_topic_insights:
            self.cross_topic_insights.append(insight)

    def add_knowledge_gap(self, gap: str):
        """添加知识缺口"""
        if gap and gap not in self.knowledge_gaps:
            self.knowledge_gaps.append(gap)

    def get_total_sources_count(self) -> int:
        """获取总信息源数量"""
        return sum(len(topic.sources) for topic in self.findings_by_topic)

    def get_high_quality_sources(self) -> List[ResearchSource]:
        """获取高质量信息源"""
        high_quality = []
        for topic in self.findings_by_topic:
            high_quality.extend([
                s for s in topic.sources 
                if s.is_high_relevance() and s.is_credible()
            ])
        return high_quality

    def update_summary(self, **kwargs):
        """更新研究摘要"""
        self.research_summary.update(kwargs)

    def is_comprehensive(self) -> bool:
        """判断研究是否全面"""
        return (
            len(self.findings_by_topic) >= 2 and
            self.get_total_sources_count() >= 5 and
            len(self.cross_topic_insights) > 0
        )
