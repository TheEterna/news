# -*- coding: utf-8 -*-
"""
数据库模块
提供 SQLite 数据存储支持
"""
from database.connection import get_database
from database.repository import get_repository

__all__ = ["get_database", "get_repository"]
