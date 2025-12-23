# -*- coding: utf-8 -*-
"""
新闻分类服务
使用 AI 判断新闻类型并给出相关性评分
"""
import json
from openai import OpenAI

from config import OPENAI_API_KEY, OPENAI_BASE_URL, MODEL_NAME
from utils.logger import logger


class NewsClassifier:
    """新闻分类器"""

    # 分类标准
    CATEGORIES = {
        "product_release": "产品发布 - 公司发布新产品",
        "model_release": "新模型发布 - AI 模型、算法等发布",
        "feature_update": "新功能更新 - 现有产品/服务的功能更新",
        "interview": "访谈/人物故事 - CEO 访谈、人物专访等",
        "analysis": "行业分析/评论 - 市场分析、行业评论文章",
        "recruitment": "招聘/活动公告 - 招聘信息、会议活动",
        "financial": "财报/股价新闻 - 财务报表、股票价格相关",
        "other": "其他 - 不属于以上类别"
    }

    # 符合要求的分类
    VALID_CATEGORIES = ["product_release", "model_release", "feature_update"]

    # 分类中文映射
    CATEGORY_CN = {
        "product_release": "产品发布",
        "model_release": "新模型",
        "feature_update": "功能更新",
        "interview": "访谈",
        "analysis": "行业分析",
        "recruitment": "招聘/活动",
        "financial": "财报/股价",
        "other": "其他"
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

    def classify(self, title: str, content: str) -> dict:
        """
        对单条新闻进行分类

        Args:
            title: 新闻标题
            content: 新闻内容

        Returns:
            {
                "category": "product_release",
                "relevance": 0.85,
                "reason": "这是关于新产品发布的新闻..."
            }
        """
        # 截取内容避免过长
        content_truncated = content[:2000] if content else ""

        categories_desc = "\n".join([
            f"- {k}: {v}" for k, v in self.CATEGORIES.items()
        ])

        prompt = f"""请分析以下新闻，判断其类型。

## 新闻标题
{title}

## 新闻内容
{content_truncated}

## 分类标准
{categories_desc}

## 输出要求
请以 JSON 格式输出，包含以下字段：
- category: 分类结果（必须是上述分类之一的英文key）
- relevance: 相关性评分（0-1之间的小数，1表示非常符合该分类）
- reason: 判断理由（简短说明为什么属于该分类，30字以内，中文）

只输出 JSON，不要输出其他内容。"""

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": "你是一个专业的新闻分类助手。请严格按照 JSON 格式输出，不要添加任何额外文字。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"LLM 原始返回 | 长度: {len(result_text)} | 内容: {repr(result_text[:100])}...")

            if not result_text:
                logger.warning("LLM 返回内容为空")
                return {
                    "category": "other",
                    "relevance": 0.5,
                    "reason": "LLM返回为空"
                }

            # 尝试使用正则提取 JSON
            import re
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)

            try:
                result = json.loads(result_text)
            except json.JSONDecodeError:
                # 如果标准解析失败，尝试修复常见错误（如单引号）
                logger.warning(f"JSON 解析初次失败，尝试清洗 | 内容: {result_text[:100]}...")
                try:
                    # 尝试处理 Python 风格的字典字符串
                    import ast
                    result = ast.literal_eval(result_text)
                    if not isinstance(result, dict):
                        raise ValueError("解析结果不是字典")
                except Exception as e:
                    logger.warning(f"清洗失败: {str(e)}")
                    # 最后的尝试：修复单引号
                    result = json.loads(result_text.replace("'", '"'))

            # 验证分类是否有效
            if result.get("category") not in self.CATEGORIES:
                result["category"] = "other"

            # 验证相关性评分
            relevance = result.get("relevance", 0.5)
            if not isinstance(relevance, (int, float)) or relevance < 0 or relevance > 1:
                relevance = 0.5
            result["relevance"] = float(relevance)

            # 确保 reason 存在
            if not result.get("reason"):
                result["reason"] = self.CATEGORY_CN.get(result["category"], "未知分类")

            logger.info(f"分类完成 | 类别: {result['category']} | 相关性: {result['relevance']:.2f}")
            return result

        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败，使用默认分类 | 错误: {str(e)} | 原始内容: {result_text}")
            return {
                "category": "other",
                "relevance": 0.5,
                "reason": "分类解析失败"
            }
        except Exception as e:
            logger.error(f"分类失败 | 错误: {str(e)}")
            return {
                "category": "other",
                "relevance": 0.5,
                "reason": f"分类出错: {str(e)[:20]}"
            }

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
