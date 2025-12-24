# -*- coding: utf-8 -*-
"""
新闻分类服务
使用 AI 批量判断新闻类型，一次调用完成所有审核和去重
"""
import json
import re
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME
from utils.logger import logger


class NewsClassifier:
    """新闻分类器（批量模式）"""

    # 符合要求的分类
    VALID_CATEGORIES = ["new_product", "new_model"]

    # 分类中文映射
    CATEGORY_CN = {
        "new_product": "新产品",
        "new_model": "新模型",
        "update": "更新",
        "irrelevant": "无关"
    }

    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY 未配置")

        self._client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_BASE_URL
        )
        self._model = MODEL_NAME
        logger.info(f"NewsClassifier 初始化完成 | 模型: {MODEL_NAME}")

    def classify_batch(self, news_list: list[dict]) -> list[dict]:
        """
        批量分类新闻（一次 LLM 调用）

        Args:
            news_list: 新闻列表，每条包含 {id, title, content}

        Returns:
            分类结果列表，每条包含 {id, category, reason, is_duplicate_of}
        """
        if not news_list:
            return []

        logger.info(f"开始批量分类 | 新闻数量: {len(news_list)}")

        # 构建新闻列表文本
        news_text = ""
        for i, news in enumerate(news_list):
            content_short = (news.get("content") or "")[:500]
            news_text += f"""
【新闻 {i + 1}】
标题: {news.get("title", "")}
内容: {content_short}
---"""

        prompt = f"""请批量审核以下新闻，判断每条是否符合收录标准。

## 收录标准

我们只收录【新产品/新模型】的发布新闻：

✅ **new_product** - 新产品发布
   - 公司发布的新产品（全新的产品个体）
   - 例如：某公司发布新款手机、新软件产品

✅ **new_model** - 新模型发布
   - AI 模型的新版本发布（是一个新的模型个体）
   - 例如：gemini-2.5-flash、Claude 3.5、GPT-4o 都算新模型
   - 关键：是一个【新的模型】，有独立的名称/版本号

❌ **update** - 功能更新（不收录）
   - 现有产品/模型的功能更新、性能优化
   - 例如：某产品新增了XX功能、优化了XX性能
   - 关键：不是新个体，是对已有产品的【更新/升级】

❌ **irrelevant** - 无关内容（不收录）
   - 访谈、评测、分析、招聘、财报等

## 核心区分逻辑
- **新** = 一个全新的独立个体（新产品名、新模型名）
- **更新** = 对已有个体的修改增强（新功能、新特性）

## 去重要求
如果多条新闻报道的是【同一个产品/模型的发布】，只保留第一条，后续标记为重复。

## 待审核新闻
{news_text}

## 输出要求
请输出 JSON 数组，每条新闻一个对象：
```json
[
  {{"id": 1, "category": "new_model", "reason": "发布新模型gemini-2.5"}},
  {{"id": 2, "category": "irrelevant", "reason": "行业分析文章"}},
  {{"id": 3, "category": "duplicate", "reason": "与新闻1重复", "duplicate_of": 1}}
]
```

只输出 JSON 数组，不要其他内容。"""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是专业的新闻审核助手，擅长判断新闻类型并识别重复内容。请严格输出 JSON 格式。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"LLM 批量分类返回 | 长度: {len(result_text)}")

            # 解析 JSON 数组
            results = self._parse_batch_result(result_text, len(news_list))

            # 统计结果
            valid_count = sum(1 for r in results if r.get("category") in self.VALID_CATEGORIES)
            duplicate_count = sum(1 for r in results if r.get("category") == "duplicate")
            filtered_count = len(results) - valid_count - duplicate_count

            logger.info(f"批量分类完成 | 通过: {valid_count} | 重复: {duplicate_count} | 过滤: {filtered_count}")

            return results

        except Exception as e:
            logger.error(f"批量分类失败: {str(e)}")
            # 返回默认结果（全部标记为其他）
            return [
                {"id": i + 1, "category": "irrelevant", "reason": f"分类出错: {str(e)[:20]}"}
                for i in range(len(news_list))
            ]

    def _parse_batch_result(self, result_text: str, expected_count: int) -> list[dict]:
        """解析批量分类结果"""
        # 尝试提取 JSON 数组
        json_match = re.search(r'\[.*\]', result_text, re.DOTALL)
        if json_match:
            result_text = json_match.group(0)

        try:
            results = json.loads(result_text)
            if not isinstance(results, list):
                raise ValueError("结果不是数组")
        except json.JSONDecodeError:
            logger.warning(f"JSON 解析失败，尝试修复...")
            # 尝试修复常见问题
            result_text = result_text.replace("'", '"')
            results = json.loads(result_text)

        # 验证和补全结果
        validated = []
        for i in range(expected_count):
            # 查找对应 ID 的结果
            found = None
            for r in results:
                if r.get("id") == i + 1:
                    found = r
                    break

            if found:
                # 验证 category
                category = found.get("category", "irrelevant")
                if category not in ["new_product", "new_model", "update", "irrelevant", "duplicate"]:
                    category = "irrelevant"

                validated.append({
                    "id": i + 1,
                    "category": category,
                    "reason": found.get("reason", ""),
                    "duplicate_of": found.get("duplicate_of")
                })
            else:
                # 缺失的结果，默认标记为无关
                validated.append({
                    "id": i + 1,
                    "category": "irrelevant",
                    "reason": "未返回分类结果"
                })

        return validated

    def classify(self, title: str, content: str) -> dict:
        """
        单条分类（兼容旧接口）

        Args:
            title: 新闻标题
            content: 新闻内容

        Returns:
            {"category": "new_model", "relevance": 0.9, "reason": "..."}
        """
        results = self.classify_batch([{"id": 1, "title": title, "content": content}])
        if results:
            r = results[0]
            return {
                "category": r["category"],
                "relevance": 0.9 if r["category"] in self.VALID_CATEGORIES else 0.3,
                "reason": r["reason"]
            }
        return {"category": "irrelevant", "relevance": 0.5, "reason": "分类失败"}

    def is_valid_category(self, category: str) -> bool:
        """判断分类是否符合要求"""
        return category in self.VALID_CATEGORIES

    def get_category_cn(self, category: str) -> str:
        """获取分类的中文名称"""
        return self.CATEGORY_CN.get(category, "其他")


# 单例实例
_classifier_instance: NewsClassifier | None = None


def get_news_classifier() -> NewsClassifier:
    """获取新闻分类器实例"""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = NewsClassifier()
    return _classifier_instance
