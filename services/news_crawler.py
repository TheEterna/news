# -*- coding: utf-8 -*-
"""
新闻爬取服务
使用 Serper.dev 单引擎模式
"""
import re
from difflib import SequenceMatcher

from config import SERPER_API_KEY, NEWS_MAX_RESULTS
from models.schemas import NewsItem
from utils.logger import logger
from services.search_engine import SearchEngine


class NewsCrawler:
    """新闻爬取调度器（单引擎模式）"""

    # 标题相似度阈值（超过此值视为重复）
    TITLE_SIMILARITY_THRESHOLD = 0.7

    def __init__(self, engine: SearchEngine = None):
        """
        初始化爬取器

        Args:
            engine: 搜索引擎实例，为空则使用默认 Serper 引擎
        """
        self._engine = engine if engine is not None else self._create_default_engine()
        logger.info(f"NewsCrawler 初始化完成 | 引擎: {self._engine.name}")

    def _create_default_engine(self) -> SearchEngine:
        """创建默认搜索引擎（Serper）"""
        if not SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY 未配置，请在 config.py 或 .env 文件中设置")

        try:
            from services.search_engine.serper_engine import SerperNewsEngine
            return SerperNewsEngine()
        except Exception as e:
            logger.error(f"SerperNewsEngine 初始化失败: {e}")
            raise

    def _normalize_title(self, title: str) -> str:
        """
        标准化标题用于比较
        移除标点符号、空格，转小写
        """
        # 移除标点和特殊字符
        normalized = re.sub(r'[^\w\u4e00-\u9fff]', '', title.lower())
        return normalized

    def _is_similar_title(self, title: str, existing_titles: list[str]) -> bool:
        """
        检查标题是否与已有标题相似

        Args:
            title: 待检查的标题
            existing_titles: 已收录的标题列表

        Returns:
            True 如果存在相似标题
        """
        normalized_new = self._normalize_title(title)

        for existing in existing_titles:
            normalized_existing = self._normalize_title(existing)

            # 计算相似度
            similarity = SequenceMatcher(None, normalized_new, normalized_existing).ratio()

            if similarity >= self.TITLE_SIMILARITY_THRESHOLD:
                logger.debug(f"标题相似度 {similarity:.2f}: '{title[:30]}...' vs '{existing[:30]}...'")
                return True

        return False

    def search_by_keyword(self, keyword: str, max_results: int = 2) -> list[NewsItem]:
        """
        根据单个关键词搜索新闻

        Args:
            keyword: 搜索关键词
            max_results: 最大结果数

        Returns:
            新闻列表（已去重）
        """
        logger.info(f"搜索关键词: {keyword} | 最大结果: {max_results}")

        try:
            results = self._engine.search(keyword, max_results)
            logger.info(f"  -> 找到 {len(results)} 条新闻")
            return results
        except Exception as e:
            logger.error(f"引擎 {self._engine.name} 搜索失败: {e}")
            return []

    def fetch_news_by_keywords(self, keywords: list[str], news_per_keyword: int = 2) -> list[NewsItem]:
        """
        根据关键词列表搜索新闻，并去重（URL + 标题相似度）

        Args:
            keywords: 关键词列表
            news_per_keyword: 每个关键词搜索的新闻数量

        Returns:
            去重后的新闻列表
        """
        logger.info(f"========== 开始多关键词搜索 ==========")
        logger.info(f"关键词数量: {len(keywords)} | 每个关键词搜索: {news_per_keyword} 条")
        logger.info(f"使用引擎: {self._engine.name}")

        all_news = []
        seen_urls = set()
        seen_titles = []  # 用于标题相似度检测

        for i, keyword in enumerate(keywords, 1):
            logger.info(f"[{i}/{len(keywords)}] 搜索: {keyword}")

            try:
                news_list = self._engine.search(keyword, news_per_keyword)

                # 去重：URL + 标题相似度，并限制每个关键词的新闻数量
                added_count = 0
                for news in news_list:
                    if added_count >= news_per_keyword:
                        break  # 已达到该关键词的数量限制

                    # 检查 URL 重复
                    if news.url in seen_urls:
                        logger.debug(f"    - (URL重复) {news.title[:30]}...")
                        continue

                    # 检查标题相似度
                    if self._is_similar_title(news.title, seen_titles):
                        logger.info(f"    - (标题相似) {news.title[:40]}...")
                        continue

                    # 通过去重检查，添加到结果
                    seen_urls.add(news.url)
                    seen_titles.append(news.title)
                    all_news.append(news)
                    added_count += 1
                    logger.info(f"    + {news.title[:50]}...")

            except Exception as e:
                logger.error(f"搜索失败 | 关键词: {keyword} | 错误: {e}")

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
