# -*- coding: utf-8 -*-
"""
数据访问层
封装所有数据库 CRUD 操作（PostgreSQL）
"""
import json
from datetime import datetime
from typing import Optional

from database.connection import get_database
from utils.logger import logger


class NewsRepository:
    """新闻数据仓库"""

    # ========== 搜索任务相关 ==========

    def create_task(self, company_name: str, keywords: list[str]) -> int:
        """创建搜索任务，返回任务ID"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO search_tasks (company_name, keywords_used, status)
                VALUES (%s, %s, 'collecting')
                RETURNING id
            """, (company_name, json.dumps(keywords, ensure_ascii=False)))
            task_id = cursor.fetchone()['id']
            logger.info(f"创建搜索任务 | ID: {task_id} | 公司: {company_name}")
            return task_id

    def update_task_status(self, task_id: int, status: str, **kwargs):
        """更新任务状态"""
        db = get_database()
        with db.get_cursor() as cursor:
            updates = ["status = %s"]
            values = [status]

            for key, value in kwargs.items():
                updates.append(f"{key} = %s")
                values.append(value)

            values.append(task_id)
            cursor.execute(f"""
                UPDATE search_tasks
                SET {', '.join(updates)}
                WHERE id = %s
            """, values)

    def get_task(self, task_id: int) -> Optional[dict]:
        """获取任务详情"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM search_tasks WHERE id = %s", (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_tasks(self) -> list[dict]:
        """获取所有任务"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM search_tasks ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # ========== 新闻条目相关 ==========

    def add_news_item(self, task_id: int, news_data: dict) -> Optional[int]:
        """
        添加新闻条目
        返回新闻ID
        """
        db = get_database()
        with db.get_cursor() as cursor:
            # 检查 URL 是否已存在（同一任务内去重）
            cursor.execute("""
                SELECT id FROM news_items WHERE task_id = %s AND url = %s
            """, (task_id, news_data.get('url', '')))
            existing = cursor.fetchone()
            if existing:
                logger.info(f"新闻已存在，跳过 | URL: {news_data.get('url', '')[:50]}...")
                return None

            cursor.execute("""
                INSERT INTO news_items
                (task_id, title, url, published_date, content,
                 ai_category, ai_relevance, ai_reason, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                task_id,
                news_data.get('title', ''),
                news_data.get('url', ''),
                news_data.get('published_date', ''),
                news_data.get('content', ''),
                news_data.get('ai_category', ''),
                news_data.get('ai_relevance', 0.0),
                news_data.get('ai_reason', ''),
                news_data.get('status', 'pending_review')
            ))
            return cursor.fetchone()['id']

    def get_news_by_task(self, task_id: int, status: Optional[str] = None) -> list[dict]:
        """获取任务下的新闻列表"""
        db = get_database()
        with db.get_cursor() as cursor:
            if status:
                cursor.execute("""
                    SELECT * FROM news_items
                    WHERE task_id = %s AND status = %s
                    ORDER BY ai_relevance DESC, fetched_at DESC
                """, (task_id, status))
            else:
                cursor.execute("""
                    SELECT * FROM news_items
                    WHERE task_id = %s
                    ORDER BY ai_relevance DESC, fetched_at DESC
                """, (task_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_pending_review_news(self, task_id: int) -> list[dict]:
        """获取待审核的新闻（AI 判断为符合要求的）"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM news_items
                WHERE task_id = %s
                  AND status = 'pending_review'
                ORDER BY ai_relevance DESC, fetched_at DESC
            """, (task_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_filtered_news(self, task_id: int) -> list[dict]:
        """获取被过滤的新闻"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM news_items
                WHERE task_id = %s
                  AND status = 'filtered'
                ORDER BY fetched_at DESC
            """, (task_id,))
            return [dict(row) for row in cursor.fetchall()]

    def batch_update_news_status(self, news_ids: list[int], status: str):
        """批量更新新闻状态"""
        if not news_ids:
            return
        db = get_database()
        with db.get_cursor() as cursor:
            # PostgreSQL 使用 ANY 数组语法更高效
            cursor.execute("""
                UPDATE news_items
                SET status = %s, reviewed_at = %s
                WHERE id = ANY(%s)
            """, (status, datetime.now(), news_ids))
            logger.info(f"批量更新状态 | 数量: {len(news_ids)} | 状态: {status}")

    def update_news_summary(self, news_id: int, summary: str):
        """更新新闻摘要"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE news_items SET summary = %s WHERE id = %s
            """, (summary, news_id))

    def get_news_by_ids(self, news_ids: list[int]) -> list[dict]:
        """根据 ID 列表获取新闻"""
        if not news_ids:
            return []
        db = get_database()
        with db.get_cursor() as cursor:
            # PostgreSQL 使用 ANY 数组语法
            cursor.execute("""
                SELECT * FROM news_items
                WHERE id = ANY(%s)
                ORDER BY ai_relevance DESC
            """, (news_ids,))
            return [dict(row) for row in cursor.fetchall()]


# 单例获取函数
_repository_instance: NewsRepository | None = None


def get_repository() -> NewsRepository:
    """获取数据仓库实例"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = NewsRepository()
    return _repository_instance
