# -*- coding: utf-8 -*-
"""
关键词生成服务
直接拼接公司名 + 固定后缀
"""
from config import DEFAULT_KEYWORD_COUNT
from utils.logger import logger


# 关键词后缀模板
KEYWORD_SUFFIXES = [
    "发布",
    "新产品",
    "新模型",
    "推出",
    "上线",
    "新功能",
    "更新",
    "AI",
    "人工智能",
    "新技术",
]


class KeywordGenerator:
    """关键词生成器"""

    def __init__(self):
        logger.info("KeywordGenerator 初始化完成")

    def generate_keywords(self, company_name: str, keyword_count: int = None) -> list[str]:
        """
        根据公司名称生成搜索关键词

        Args:
            company_name: 公司名称
            keyword_count: 关键词数量（1-10，默认使用配置值）

        Returns:
            关键词列表

        规则：
            - 1个: 公司名+发布
            - 2个: 公司名+发布, 公司名+新产品
            - 3个: 公司名+发布, 公司名+新产品, 公司名+新模型
            - 以此类推，最多10个
        """
        count = min(keyword_count or DEFAULT_KEYWORD_COUNT, 10)

        # 公司名 + 后缀
        keywords = []
        for suffix in KEYWORD_SUFFIXES:
            if len(keywords) >= count:
                break
            keywords.append(f"{company_name} {suffix}")

        logger.info(f"生成搜索关键词 | 公司: {company_name} | 数量: {len(keywords)}")
        for i, kw in enumerate(keywords, 1):
            logger.info(f"  [{i}] {kw}")

        return keywords


# 单例实例
_generator_instance: KeywordGenerator | None = None


def get_keyword_generator() -> KeywordGenerator:
    """获取关键词生成器实例"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = KeywordGenerator()
    return _generator_instance
