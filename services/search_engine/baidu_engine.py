# -*- coding: utf-8 -*-
"""
百度新闻搜索引擎实现
使用 SerpApi 的 Baidu News API
适用于中国公司/中文新闻搜索
"""
from serpapi import GoogleSearch

from config import SERPAPI_API_KEY
from models.schemas import NewsItem
from utils.logger import logger
from . import SearchEngine


class BaiduNewsEngine(SearchEngine):
    """百度新闻搜索引擎（适用于中国公司/中文搜索）"""

    def __init__(self):
        if not SERPAPI_API_KEY:
            raise ValueError("SERPAPI_API_KEY 未配置，请在 .env 文件中设置")
        self._api_key = SERPAPI_API_KEY
        logger.info("BaiduNewsEngine 初始化完成")

    @property
    def name(self) -> str:
        return "baidu_news"

    def search(self, keyword: str, max_results: int = 5) -> list[NewsItem]:
        """
        使用 SerpApi 百度新闻 API 搜索

        Args:
            keyword: 搜索关键词
            max_results: 最大返回数量（最大50）

        Returns:
            新闻列表
        """
        logger.info(f"[百度新闻] 搜索关键词: {keyword} | 最大结果: {max_results}")

        try:
            params = {
                "engine": "baidu_news",
                "q": keyword,
                "rtt": 4,           # 按时间排序
                "rn": min(max_results, 50),  # 最大50条
                "api_key": self._api_key
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            news_list = []
            organic_results = results.get("organic_results", [])

            for item in organic_results:
                news = NewsItem(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    published_date=item.get("date", ""),
                    content=item.get("snippet", ""),  # 使用 snippet 作为内容
                    summary="",
                    source_engine="百度新闻"
                )
                news_list.append(news)

            logger.info(f"[百度新闻] 找到 {len(news_list)} 条新闻")
            return news_list

        except Exception as e:
            logger.error(f"[百度新闻] 搜索失败 | 关键词: {keyword} | 错误: {str(e)}")
            return []


# 单例实例，延迟初始化
_baidu_engine_instance: BaiduNewsEngine | None = None


def get_baidu_engine() -> BaiduNewsEngine:
    """获取百度新闻引擎单例实例"""
    global _baidu_engine_instance
    if _baidu_engine_instance is None:
        _baidu_engine_instance = BaiduNewsEngine()
    return _baidu_engine_instance
