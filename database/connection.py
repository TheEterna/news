# -*- coding: utf-8 -*-
"""
PostgreSQL 数据库连接管理
使用单例模式确保全局唯一连接
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from utils.logger import logger


class DatabaseManager:
    """数据库管理器（单例）"""

    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._connection is None:
            self._init_database()

    def _init_database(self):
        """初始化数据库连接和表结构"""
        try:
            self._connection = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            self._connection.autocommit = False

            self._create_tables()
            logger.info(f"PostgreSQL 数据库连接成功 | {DB_HOST}:{DB_PORT}/{DB_NAME}")
        except Exception as e:
            logger.error(f"PostgreSQL 连接失败: {str(e)}")
            raise

    def _create_tables(self):
        """创建数据库表"""
        cursor = self._connection.cursor()

        # 搜索任务表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_tasks (
                id              SERIAL PRIMARY KEY,
                company_name    TEXT NOT NULL,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status          TEXT DEFAULT 'collecting',
                keywords_used   TEXT,
                total_fetched   INTEGER DEFAULT 0,
                total_approved  INTEGER DEFAULT 0,
                overall_summary TEXT
            )
        """)

        # 新闻条目表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_items (
                id              SERIAL PRIMARY KEY,
                task_id         INTEGER NOT NULL REFERENCES search_tasks(id),
                title           TEXT NOT NULL,
                url             TEXT NOT NULL,
                published_date  TEXT,
                content         TEXT,
                ai_category     TEXT,
                ai_relevance    REAL,
                ai_reason       TEXT,
                status          TEXT DEFAULT 'pending_review',
                summary         TEXT,
                fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at     TIMESTAMP
            )
        """)

        # 创建索引（如果不存在）
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_task_id ON news_items(task_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_status ON news_items(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_news_url ON news_items(url)
        """)

        self._connection.commit()

    @contextmanager
    def get_cursor(self):
        """获取游标的上下文管理器，使用 RealDictCursor 返回字典"""
        cursor = self._connection.cursor(cursor_factory=RealDictCursor)
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()

    @property
    def connection(self):
        return self._connection

    def close(self):
        """关闭数据库连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("数据库连接已关闭")


# 单例获取函数
_db_instance: DatabaseManager | None = None


def get_database() -> DatabaseManager:
    """获取数据库管理器实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
