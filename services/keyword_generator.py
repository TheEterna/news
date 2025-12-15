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

    def generate_keywords(self, company_name: str, news_per_keyword: int = 2) -> list[str]:
        """
        根据公司名称生成多维度搜索关键词

        Args:
            company_name: 公司名称
            news_per_keyword: 每个关键词搜索的新闻数量

        Returns:
            关键词列表
        """
        logger.info(f"开始生成搜索关键词 | 公司: {company_name}")

        prompt = f"""你是一名专业的AI行业分析师。请为"{company_name}"生成全面的新闻搜索关键词列表。

## 搜索维度要求
请从以下多个维度生成搜索关键词：

1. **官方发布**：公司名 + 发布/推出/上线
2. **产品更新**：公司名 + 更新/升级/新版本/新功能
3. **技术动态**：公司名 + 技术/研发/突破/创新
4. **商业合作**：公司名 + 合作/签约/战略/投资
5. **行业影响**：公司名 + 市场/行业/竞争/份额
6. **英文搜索**：公司英文名 + news/release/launch/update
7. **媒体报道**：公司名 + 报道/新闻/动态

## 输出要求
- 生成 8-12 个不同角度的搜索关键词
- 每行一个关键词，不要编号
- 关键词要简洁有效，适合搜索引擎
- 中英文关键词都要包含
- 不要输出任何解释，只输出关键词列表

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
        """获取默认关键词列表"""
        return [
            f"{company_name} 新闻",
            f"{company_name} 发布",
            f"{company_name} 产品",
            f"{company_name} 动态",
            f"{company_name} news",
            f"{company_name} release",
            f"{company_name} update",
            f"{company_name} announcement",
        ]


# 单例实例
_generator_instance: KeywordGenerator | None = None


def get_keyword_generator() -> KeywordGenerator:
    """获取关键词生成器实例"""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = KeywordGenerator()
    return _generator_instance
