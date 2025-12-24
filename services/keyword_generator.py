# -*- coding: utf-8 -*-
"""
关键词生成服务
根据 SOP 使用大模型生成搜索关键词列表
"""
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME
from utils.logger import logger


class KeywordGenerator:
    """关键词生成器"""

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置，请在 .env 文件中设置")

        self._client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self._model = MODEL_NAME
        logger.info(f"KeywordGenerator 初始化完成 | 模型: {MODEL_NAME}")

    def generate_keywords(self, company_name: str) -> list[str]:
        """
        根据公司名称生成多维度搜索关键词

        Args:
            company_name: 公司名称

        Returns:
            关键词列表（4-5个）
        """
        logger.info(f"开始生成搜索关键词 | 公司: {company_name}")

        prompt = f"""你是一名专业的AI行业分析师。请为"{company_name}"生成精准的新闻搜索关键词。

## 搜索目标
我们只关注【新产品/新模型】的发布新闻：
- ✅ 新产品发布（全新的产品个体）
- ✅ 新模型发布（如 gemini-2.5-flash、Claude 3.5 等新模型）
- ❌ 不要：功能更新、版本升级、性能优化类

## 输出要求
- 只生成 2-3 个最有效的搜索关键词
- 每行一个关键词，不要编号
- 关键词要简洁精准
- 中英文各一个即可
- 不要输出任何解释

公司名称：{company_name}

请直接输出关键词列表："""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是一个专业的搜索关键词生成助手，擅长生成全面、精准的搜索关键词。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            content = response.choices[0].message.content
            if not content:
                logger.warning("关键词生成返回空内容，使用默认关键词")
                return self._get_default_keywords(company_name)

            # 解析关键词列表
            keywords = []
            for line in content.strip().split('\n'):
                line = line.strip()
                # 去除编号和特殊字符
                line = line.lstrip('0123456789.-、·•*) ')
                if line and len(line) > 2:
                    keywords.append(line)

            if not keywords:
                logger.warning("解析关键词失败，使用默认关键词")
                return self._get_default_keywords(company_name)

            logger.info(f"关键词生成完成 | 数量: {len(keywords)}")
            for i, kw in enumerate(keywords, 1):
                logger.info(f"  [{i}] {kw}")

            return keywords

        except Exception as e:
            logger.error(f"关键词生成失败: {str(e)}，使用默认关键词")
            return self._get_default_keywords(company_name)

    def _get_default_keywords(self, company_name: str) -> list[str]:
        """获取默认关键词列表（2-3个）"""
        return [
            f"{company_name} 发布",
            f"{company_name} release",
        ]


# 单例实例
_generator_instance: KeywordGenerator | None = None


def get_keyword_generator() -> KeywordGenerator:
    """获取关键词生成器实例"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = KeywordGenerator()
    return _generator_instance
