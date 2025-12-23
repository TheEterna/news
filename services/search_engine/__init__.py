# -*- coding: utf-8 -*-
"""
搜索引擎抽象层
定义搜索引擎的统一接口，支持多引擎扩展
"""
from abc import ABC, abstractmethod

from models.schemas import NewsItem


class SearchEngine(ABC):
    """搜索引擎抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称标识"""
        pass

    @abstractmethod
    def search(self, keyword: str, max_results: int = 5) -> list[NewsItem]:
        """
        搜索新闻

        Args:
            keyword: 搜索关键词
            max_results: 最大返回数量

        Returns:
            新闻列表
        """
        pass
