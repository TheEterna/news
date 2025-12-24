# -*- coding: utf-8 -*-
"""
Serper.dev 新闻搜索引擎实现
使用 Serper Google News API
支持时间范围过滤和国际搜索
"""
import requests

from config import SERPER_API_KEY, NEWS_TIME_RANGE
from models.schemas import NewsItem
from utils.logger import logger
from . import SearchEngine


class SerperNewsEngine(SearchEngine):
    """Serper.dev 新闻搜索引擎"""

    API_URL = "https://google.serper.dev/news"

    # 时间范围映射 (Serper tbs 参数)
    TIME_RANGE_MAP = {
        "day": "qdr:d",      # 过去24小时
        "week": "qdr:w",     # 过去一周
        "month": "qdr:m",    # 过去一月
        "year": "qdr:y",     # 过去一年
    }

    def __init__(self):
        if not SERPER_API_KEY:
            raise ValueError("SERPER_API_KEY 未配置，请在 .env 文件中设置")
        self._api_key = SERPER_API_KEY
        logger.info("SerperNewsEngine 初始化完成")

    @property
    def name(self) -> str:
        return "serper_news"

    def search(
        self,
        keyword: str,
        max_results: int = 5,
        time_range: str = None,
        region: str = None,
        language: str = None
    ) -> list[NewsItem]:
        """
        使用 Serper Google News API 搜索新闻

        Args:
            keyword: 搜索关键词
            max_results: 最大返回数量（最大100）
            time_range: 时间范围 (day/week/month/year)，默认使用配置
            region: 地区代码 (cn/us/uk等)，默认自动检测
            language: 语言代码 (zh-cn/en等)，默认自动检测

        Returns:
            新闻列表
        """
        # 自动检测：关键词包含中文则使用中国区，否则使用国际
        is_chinese = any('\u4e00' <= c <= '\u9fff' for c in keyword)

        if region is None:
            region = "cn" if is_chinese else "us"
        if language is None:
            language = "zh-cn" if is_chinese else "en"
        if time_range is None:
            time_range = NEWS_TIME_RANGE

        logger.info(f"[Serper] 搜索: {keyword} | 数量: {max_results} | 时间: {time_range} | 地区: {region}")

        try:
            headers = {
                "X-API-KEY": self._api_key,
                "Content-Type": "application/json"
            }

            payload = {
                "q": keyword,
                "num": min(max_results, 100),
                "gl": region,
                "hl": language,
            }

            # 添加时间范围过滤
            if time_range and time_range in self.TIME_RANGE_MAP:
                payload["tbs"] = self.TIME_RANGE_MAP[time_range]

            response = requests.post(
                self.API_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            news_list = []

            # 解析新闻结果
            news_results = data.get("news", [])

            for item in news_results:
                news = NewsItem(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    published_date=item.get("date", ""),
                    content=item.get("snippet", ""),
                    summary="",
                    source_engine="Serper"
                )
                news_list.append(news)

            logger.info(f"[Serper] 找到 {len(news_list)} 条新闻")
            return news_list

        except requests.RequestException as e:
            logger.error(f"[Serper] 网络请求失败 | 关键词: {keyword} | 错误: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"[Serper] 搜索失败 | 关键词: {keyword} | 错误: {str(e)}")
            return []


# 单例实例，延迟初始化
_serper_engine_instance: SerperNewsEngine | None = None


def get_serper_engine() -> SerperNewsEngine:
    """获取 Serper 新闻引擎单例实例"""
    global _serper_engine_instance
    if _serper_engine_instance is None:
        _serper_engine_instance = SerperNewsEngine()
    return _serper_engine_instance
