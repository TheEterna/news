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

    # ========== 批次组相关 ==========

    def create_batch(self, name: str, filename: str, total_companies: int,
                     keyword_count: int = 3, news_per_keyword: int = 2) -> int:
        """创建批次组，返回批次ID"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO batch_groups (name, filename, total_companies, status, keyword_count, news_per_keyword)
                VALUES (%s, %s, %s, 'processing', %s, %s)
                RETURNING id
            """, (name, filename, total_companies, keyword_count, news_per_keyword))
            batch_id = cursor.fetchone()['id']
            logger.info(f"创建批次 | ID: {batch_id} | 名称: {name} | 公司数: {total_companies} | 关键词: {keyword_count} | 每词新闻: {news_per_keyword}")
            return batch_id

    def update_batch_status(self, batch_id: int, status: str, success_count: int = 0, failed_count: int = 0):
        """更新批次状态"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE batch_groups
                SET status = %s, success_count = %s, failed_count = %s
                WHERE id = %s
            """, (status, success_count, failed_count, batch_id))

    def get_batch(self, batch_id: int) -> Optional[dict]:
        """获取批次详情"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("SELECT * FROM batch_groups WHERE id = %s", (batch_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_batches(self) -> list[dict]:
        """获取所有批次列表"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM batch_groups
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_tasks_by_batch(self, batch_id: int) -> list[dict]:
        """获取批次下的所有任务"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM search_tasks
                WHERE batch_id = %s
                ORDER BY created_at DESC
            """, (batch_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_batches_with_tasks(self) -> list[dict]:
        """获取所有批次及其任务列表（用于前端折叠显示）"""
        batches = self.get_all_batches()
        for batch in batches:
            batch['tasks'] = self.get_tasks_by_batch(batch['id'])
        return batches

    # ========== 搜索任务相关 ==========

    def create_task(self, company_name: str, keywords: list[str], batch_id: Optional[int] = None) -> int:
        """创建搜索任务，返回任务ID"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO search_tasks (company_name, keywords_used, status, batch_id)
                VALUES (%s, %s, 'collecting', %s)
                RETURNING id
            """, (company_name, json.dumps(keywords, ensure_ascii=False), batch_id))
            task_id = cursor.fetchone()['id']
            batch_info = f" | 批次: {batch_id}" if batch_id else ""
            logger.info(f"创建搜索任务 | ID: {task_id} | 公司: {company_name}{batch_info}")
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

    def save_task_report(self, task_id: int, report_html: str, overall_summary: str):
        """保存任务报告"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                UPDATE search_tasks
                SET report_html = %s, overall_summary = %s
                WHERE id = %s
            """, (report_html, overall_summary, task_id))
            logger.info(f"报告已保存 | 任务ID: {task_id} | HTML长度: {len(report_html)}")

    def get_task_report(self, task_id: int) -> Optional[str]:
        """获取任务报告 HTML"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("SELECT report_html FROM search_tasks WHERE id = %s", (task_id,))
            row = cursor.fetchone()
            return row['report_html'] if row else None

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

    def get_standalone_tasks(self) -> list[dict]:
        """获取独立任务（不属于任何批次的任务）"""
        db = get_database()
        with db.get_cursor() as cursor:
            cursor.execute("""
                SELECT * FROM search_tasks
                WHERE batch_id IS NULL
                ORDER BY created_at DESC
            """)
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

    # ========== 新闻浏览功能 ==========

    def browse_news(self,
                    page: int = 1,
                    page_size: int = 20,
                    company: str = None,
                    batch_id: int = None,
                    status_list: list = None,
                    category_list: list = None,
                    date_from: str = None,
                    date_to: str = None,
                    keyword: str = None) -> tuple[list[dict], int]:
        """
        多条件查询新闻列表（带分页）

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            company: 公司名称筛选
            batch_id: 批次ID筛选
            status_list: 状态列表筛选
            category_list: AI分类列表筛选
            date_from: 开始日期 (YYYY-MM-DD)
            date_to: 结束日期 (YYYY-MM-DD)
            keyword: 标题关键词搜索

        Returns:
            (新闻列表, 总数)
        """
        db = get_database()

        # 构建基础查询
        base_select = """
            SELECT
                n.id,
                n.title,
                n.url,
                n.published_date,
                n.ai_category,
                n.ai_relevance,
                n.ai_reason,
                n.status,
                n.summary,
                n.fetched_at,
                n.task_id,
                t.company_name,
                t.batch_id,
                b.name as batch_name
            FROM news_items n
            INNER JOIN search_tasks t ON n.task_id = t.id
            LEFT JOIN batch_groups b ON t.batch_id = b.id
        """

        # 构建 WHERE 子句
        conditions = []
        params = []

        if company:
            conditions.append("t.company_name = %s")
            params.append(company)

        if batch_id:
            conditions.append("t.batch_id = %s")
            params.append(batch_id)

        if status_list:
            conditions.append("n.status = ANY(%s)")
            params.append(status_list)

        if category_list:
            conditions.append("n.ai_category = ANY(%s)")
            params.append(category_list)

        if date_from:
            conditions.append("n.fetched_at >= %s")
            params.append(date_from)

        if date_to:
            conditions.append("n.fetched_at <= %s")
            params.append(date_to + " 23:59:59")

        if keyword:
            conditions.append("n.title ILIKE %s")
            params.append(f"%{keyword}%")

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        with db.get_cursor() as cursor:
            # 计算总数
            count_query = f"""
                SELECT COUNT(*) as total
                FROM news_items n
                INNER JOIN search_tasks t ON n.task_id = t.id
                LEFT JOIN batch_groups b ON t.batch_id = b.id
                {where_clause}
            """
            cursor.execute(count_query, params)
            total = cursor.fetchone()['total']

            # 分页查询
            offset = (page - 1) * page_size
            data_query = f"""
                {base_select}
                {where_clause}
                ORDER BY n.fetched_at DESC, n.id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_query, params + [page_size, offset])
            items = [dict(row) for row in cursor.fetchall()]

        return items, total

    def get_filter_options(self) -> dict:
        """
        获取筛选选项（公司列表、批次列表）

        Returns:
            {
                "companies": ["公司A", "公司B", ...],
                "batches": [{"id": 1, "name": "批次名"}, ...]
            }
        """
        db = get_database()
        with db.get_cursor() as cursor:
            # 获取所有公司名
            cursor.execute("""
                SELECT DISTINCT company_name
                FROM search_tasks
                ORDER BY company_name
            """)
            companies = [row['company_name'] for row in cursor.fetchall()]

            # 获取所有批次
            cursor.execute("""
                SELECT id, name
                FROM batch_groups
                ORDER BY created_at DESC
            """)
            batches = [{"id": row['id'], "name": row['name']} for row in cursor.fetchall()]

        return {
            "companies": companies,
            "batches": batches
        }


# 单例获取函数
_repository_instance: NewsRepository | None = None


def get_repository() -> NewsRepository:
    """获取数据仓库实例"""
    global _repository_instance
    if _repository_instance is None:
        _repository_instance = NewsRepository()
    return _repository_instance
