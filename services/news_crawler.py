# -*- coding: utf-8 -*-
"""
新闻爬取服务
支持多搜索引擎的新闻爬取调度器
"""
from config import TAVILY_API_KEY, SERPAPI_API_KEY, SEARCH_ENGINE_MODE, NEWS_MAX_RESULTS
from models.schemas import NewsItem
from utils.logger import logger
from services.search_engine import SearchEngine


class NewsCrawler:
    """新闻爬取调度器（支持多引擎）"""

    def __init__(self, engines: list[SearchEngine] = None):
        """
        初始化爬取器

        Args:
            engines: 搜索引擎列表，为空则根据配置自动创建
        """
        self._engines = engines if engines is not None else self._create_default_engines()
        logger.info(f"NewsCrawler 初始化完成 | 引擎: {[e.name for e in self._engines]}")

    def _create_default_engines(self) -> list[SearchEngine]:
        """根据配置创建默认搜索引擎列表"""
        engines = []

        # Tavily 引擎（外国公司/英文搜索）
        if SEARCH_ENGINE_MODE in ("tavily", "both") and TAVILY_API_KEY:
            try:
                from services.search_engine.tavily_engine import TavilyEngine
                engines.append(TavilyEngine())
            except Exception as e:
                logger.warning(f"TavilyEngine 初始化失败: {e}")

        # 百度新闻引擎（中国公司/中文搜索）
        if SEARCH_ENGINE_MODE in ("baidu", "both") and SERPAPI_API_KEY:
            try:
                from services.search_engine.baidu_engine import BaiduNewsEngine
                engines.append(BaiduNewsEngine())
            except Exception as e:
                logger.warning(f"BaiduNewsEngine 初始化失败: {e}")

        if not engines:
            logger.warning("未配置任何搜索引擎，请检查 API Key 和 SEARCH_ENGINE_MODE 配置")

        return engines

    def search_by_keyword(self, keyword: str, max_results: int = 2) -> list[NewsItem]:
        """
        根据单个关键词搜索新闻（使用所有可用引擎）

        Args:
            keyword: 搜索关键词
            max_results: 每个引擎的最大结果数

        Returns:
            新闻列表（已去重）
        """
        logger.info(f"搜索关键词: {keyword} | 最大结果: {max_results} | 引擎数: {len(self._engines)}")

        all_news = []
        seen_urls = set()

        for engine in self._engines:
            try:
                results = engine.search(keyword, max_results)
                for news in results:
                    if news.url not in seen_urls:
                        seen_urls.add(news.url)
                        all_news.append(news)
            except Exception as e:
                logger.error(f"引擎 {engine.name} 搜索失败: {e}")

        logger.info(f"  -> 找到 {len(all_news)} 条不重复新闻")
        return all_news

    def fetch_news_by_keywords(self, keywords: list[str], news_per_keyword: int = 2) -> list[NewsItem]:
        """
        根据关键词列表搜索新闻，并去重

        Args:
            keywords: 关键词列表
            news_per_keyword: 每个关键词在每个引擎搜索的新闻数量

        Returns:
            去重后的新闻列表
        """
        logger.info(f"========== 开始多关键词搜索 ==========")
        logger.info(f"关键词数量: {len(keywords)} | 每个关键词搜索: {news_per_keyword} 条")
        logger.info(f"可用引擎: {[e.name for e in self._engines]}")

        all_news = []
        seen_urls = set()

        for i, keyword in enumerate(keywords, 1):
            logger.info(f"[{i}/{len(keywords)}] 搜索: {keyword}")

            for engine in self._engines:
                try:
                    news_list = engine.search(keyword, news_per_keyword)

                    # 去重：根据 URL 判断
                    for news in news_list:
                        if news.url not in seen_urls:
                            seen_urls.add(news.url)
                            all_news.append(news)
                            logger.info(f"    + [{engine.name}] {news.title[:50]}...")
                        else:
                            logger.debug(f"    - (重复) {news.title[:30]}...")

                except Exception as e:
                    logger.error(f"引擎 {engine.name} 搜索失败 | 关键词: {keyword} | 错误: {e}")

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
