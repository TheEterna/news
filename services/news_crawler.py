# -*- coding: utf-8 -*-
"""
新闻爬取服务
使用 Tavily API 爬取指定公司的新闻资讯
"""
from tavily import TavilyClient

from config import TAVILY_API_KEY, NEWS_MAX_RESULTS, NEWS_TIME_RANGE
from models.schemas import NewsItem
from utils.logger import logger


class NewsCrawler:
    """新闻爬取器"""

    def __init__(self):
        if not TAVILY_API_KEY:
            raise ValueError("TAVILY_API_KEY 未配置，请在 .env 文件中设置")
        self._client = TavilyClient(api_key=TAVILY_API_KEY)
        logger.info("NewsCrawler 初始化完成")

    def search_by_keyword(self, keyword: str, max_results: int = 2) -> list[NewsItem]:
        """
        根据单个关键词搜索新闻

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数

        Returns:
            新闻列表
        """
        logger.info(f"搜索关键词: {keyword} | 最大结果: {max_results}")

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
                    summary=""
                )
                news_list.append(news)

            logger.info(f"  -> 找到 {len(news_list)} 条新闻")
            return news_list

        except Exception as e:
            logger.error(f"搜索失败 | 关键词: {keyword} | 错误: {str(e)}")
            return []

    def fetch_news_by_keywords(self, keywords: list[str], news_per_keyword: int = 2) -> list[NewsItem]:
        """
        根据关键词列表搜索新闻，并去重

        Args:
            keywords: 关键词列表
            news_per_keyword: 每个关键词搜索的新闻数量

        Returns:
            去重后的新闻列表
        """
        logger.info(f"========== 开始多关键词搜索 ==========")
        logger.info(f"关键词数量: {len(keywords)} | 每个关键词搜索: {news_per_keyword} 条")

        all_news = []
        seen_urls = set()

        for i, keyword in enumerate(keywords, 1):
            logger.info(f"[{i}/{len(keywords)}] 搜索: {keyword}")
            news_list = self.search_by_keyword(keyword, news_per_keyword)

            # 去重：根据 URL 判断
            for news in news_list:
                if news.url not in seen_urls:
                    seen_urls.add(news.url)
                    all_news.append(news)
                    logger.info(f"    + {news.title[:50]}...")
                else:
                    logger.info(f"    - (重复) {news.title[:30]}...")

        logger.info(f"========== 搜索完成 ==========")
        logger.info(f"总计: {len(all_news)} 条不重复新闻")

        return all_news

    def fetch_news(self, company_name: str) -> list[NewsItem]:
        """
        爬取指定公司的新闻（简单模式，单关键词）

        Args:
            company_name: 公司名称

        Returns:
            新闻列表
        """
        query = f"{company_name} 新闻"
        logger.info(f"简单搜索模式 | 查询: {query}")

        return self.search_by_keyword(query, NEWS_MAX_RESULTS)


# 单例实例，延迟初始化
_crawler_instance: NewsCrawler | None = None


def get_news_crawler() -> NewsCrawler:
    """获取新闻爬取器实例"""
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = NewsCrawler()
    return _crawler_instance
