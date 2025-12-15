# -*- coding: utf-8 -*-
"""
摘要生成服务
使用大模型对新闻进行摘要和总结
"""
import time
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME
from models.schemas import NewsItem
from utils.logger import logger


class Summarizer:
    """摘要生成器"""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，请在 .env 文件中设置")

        self._client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self._model = MODEL_NAME
        logger.info(f"Summarizer 初始化完成 | 模型: {MODEL_NAME} | 接口: {OPENAI_BASE_URL}")

    def _call_llm(self, messages: list, max_tokens: int = 500, temperature: float = 0.3, max_retries: int = 2) -> str:
        """
        调用大模型，带重试机制

        Args:
            messages: 消息列表
            max_tokens: 最大 token 数
            temperature: 温度参数
            max_retries: 最大重试次数

        Returns:
            模型返回的文本
        """
        for attempt in range(max_retries + 1):
            try:
                response = self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                content = response.choices[0].message.content
                if content:
                    return content.strip()

                # 返回为空，记录警告
                logger.warning(f"模型返回空内容 | 尝试: {attempt + 1}/{max_retries + 1}")

                if attempt < max_retries:
                    time.sleep(1)
                    continue

            except Exception as e:
                logger.error(f"调用模型失败 | 尝试: {attempt + 1}/{max_retries + 1} | 错误: {str(e)}")
                if attempt < max_retries:
                    time.sleep(2)
                    continue

        return ""

    def summarize_single(self, news: NewsItem) -> str:
        """
        对单条新闻生成摘要

        Args:
            news: 新闻条目

        Returns:
            摘要文本
        """
        if not news.content:
            logger.warning(f"新闻无内容，跳过摘要 | 标题: {news.title[:30]}...")
            return "无内容可摘要"

        logger.info(f"生成摘要中 | 标题: {news.title[:40]}...")

        # 截取内容，避免过长
        content = news.content[:3000]

        prompt = f"""请对以下新闻内容生成一段简洁的中文摘要（100-200字）。

标题：{news.title}

内容：
{content}

要求：
1. 直接输出摘要内容，不要添加任何前缀或说明
2. 摘要需要用中文撰写
3. 提取新闻的核心要点"""

        messages = [
            {"role": "system", "content": "你是一个专业的新闻摘要助手，擅长提取新闻要点并生成简洁准确的中文摘要。无论原文是什么语言，都请用中文输出摘要。"},
            {"role": "user", "content": prompt}
        ]

        summary = self._call_llm(messages, max_tokens=500, temperature=0.3)

        if not summary:
            # 如果仍然为空，使用标题作为备用摘要
            summary = f"（摘要生成失败）{news.title}"
            logger.warning(f"摘要生成失败，使用标题作为备用 | 标题: {news.title[:30]}...")

        logger.info(f"摘要生成完成 | 长度: {len(summary)} 字")
        return summary

    def summarize_all(self, news_list: list[NewsItem], company_name: str) -> str:
        """
        对所有新闻生成整体总结

        Args:
            news_list: 新闻列表
            company_name: 公司名称

        Returns:
            整体总结文档
        """
        if not news_list:
            return "暂无相关新闻"

        logger.info(f"开始生成整体总结 | 公司: {company_name} | 新闻数: {len(news_list)}")

        # 构建新闻摘要列表，过滤掉失败的摘要
        summaries = []
        for i, news in enumerate(news_list, 1):
            if news.summary and not news.summary.startswith("（摘要生成失败）"):
                summaries.append(f"{i}. 【{news.title}】\n   {news.summary}")
            else:
                summaries.append(f"{i}. 【{news.title}】")

        summaries_text = "\n\n".join(summaries)

        prompt = f"""以下是关于"{company_name}"的近期新闻摘要：

{summaries_text}

请基于以上新闻，生成一份关于"{company_name}"的综合新闻总结报告，包括：
1. 总体概述（公司近期动态的整体情况）
2. 重点事件（列出最重要的2-3个事件）
3. 趋势分析（如果有明显趋势的话）

请用清晰的结构输出，使用 Markdown 格式，用中文撰写。"""

        messages = [
            {"role": "system", "content": "你是一个专业的商业新闻分析师，擅长整合多条新闻并生成结构化的中文分析报告。"},
            {"role": "user", "content": prompt}
        ]

        summary = self._call_llm(messages, max_tokens=1500, temperature=0.5)

        if not summary:
            summary = "整体总结生成失败，请查看各条新闻的摘要。"

        logger.info(f"整体总结生成完成 | 长度: {len(summary)} 字")
        return summary

    def process_news_list(self, news_list: list[NewsItem], company_name: str) -> tuple[list[NewsItem], str]:
        """
        处理新闻列表：为每条新闻生成摘要，并生成整体总结

        Args:
            news_list: 新闻列表
            company_name: 公司名称

        Returns:
            (更新后的新闻列表, 整体总结)
        """
        logger.info(f"========== 开始处理新闻摘要 ==========")

        # 为每条新闻生成摘要
        total = len(news_list)
        success_count = 0

        for i, news in enumerate(news_list, 1):
            logger.info(f"[{i}/{total}] 处理新闻...")
            news.summary = self.summarize_single(news)
            if not news.summary.startswith("（摘要生成失败）"):
                success_count += 1

        logger.info(f"摘要生成统计 | 成功: {success_count}/{total}")

        logger.info(f"========== 开始生成整体总结 ==========")
        # 生成整体总结
        overall_summary = self.summarize_all(news_list, company_name)

        logger.info(f"========== 所有处理完成 ==========")
        return news_list, overall_summary


# 单例实例，延迟初始化
_summarizer_instance: Summarizer | None = None


def get_summarizer() -> Summarizer:
    """获取摘要生成器实例"""
    global _summarizer_instance
    if _summarizer_instance is None:
        _summarizer_instance = Summarizer()
    return _summarizer_instance
