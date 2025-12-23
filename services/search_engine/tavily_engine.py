# -*- coding: utf-8 -*-
"""
Tavily 搜索引擎实现
用于搜索英文/国际新闻
"""
from tavily import TavilyClient

from config import TAVILY_API_KEY, NEWS_TIME_RANGE
from models.schemas import NewsItem
from utils.logger import logger
from . import SearchEngine


class TavilyEngine(SearchEngine):
    """Tavily 搜索引擎（适用于外国公司/英文搜索）"""

    def __init__(self):
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY 未配置，请在 .env 文件中设置")
        self._client = TavilyClient(api_key=TAVILY_API_KEY)
        logger.info("TavilyEngine 初始化完成")

    @property
    def name(self) -> str:
        return "tavily"

    def search(self, keyword: str, max_results: int = 5) -> list[NewsItem]:
        """
        使用 Tavily API 搜索新闻

        Args:
            keyword: 搜索关键词
            max_results: 最大返回数量

        Returns:
            新闻列表
        """
        logger.info(f"[Tavily] 搜索关键词: {keyword} | 最大结果: {max_results}")

        try:
            response = self._client.search(
                query=keyword,
                topic="news",
                time_range=NEWS_TIME_RANGE,
                max_results=max_results,
                include_raw_content=True,
            )

            news_list = []
            results = response.get("results", [])

            for item in results:
                news = NewsItem(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                    published_date=item.get("published_date", ""),
                    content=item.get("raw_content") or item.get("content", ""),
                    summary="",
                    source_engine="Tavily"
                )
                news_list.append(news)

            logger.info(f"[Tavily] 找到 {len(news_list)} 条新闻")
            return news_list

        except Exception as e:
            logger.error(f"[Tavily] 搜索失败 | 关键词: {keyword} | 错误: {str(e)}")
            return []


# 单例实例，延迟初始化
_tavily_engine_instance: TavilyEngine | None = None


def get_tavily_engine() -> TavilyEngine:
    """获取 Tavily 引擎单例实例"""
    global _tavily_engine_instance
    if _tavily_engine_instance is None:
        _tavily_engine_instance = TavilyEngine()
    return _tavily_engine_instance
