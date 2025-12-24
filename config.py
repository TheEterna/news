# -*- coding: utf-8 -*-
"""
配置管理模块
从环境变量读取配置，支持 .env 文件
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据存储目录
DATA_DIR = BASE_DIR / "data" / "news"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Serper.dev API 配置（单引擎模式）
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "b5b706df415e0938a425cbd0426763b817ab4fe2")

# 以下配置已废弃，保留仅供参考
# TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
# SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY", "")
# SEARCH_ENGINE_MODE = os.getenv("SEARCH_ENGINE_MODE", "both")

# 自部署大模型配置 (OpenAI 兼容格式)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

# 新闻爬取配置
NEWS_MAX_RESULTS = 10  # 最多返回的新闻条数
NEWS_TIME_RANGE = "week"  # 时间范围：day, week, month, year

# PostgreSQL 数据库配置
DB_HOST = os.getenv("DB_HOST", "62.234.92.252")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "news_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "hfy")

# 新闻分类配置
VALID_CATEGORIES = ["product_release", "model_release", "feature_update"]
FILTER_CATEGORIES = ["interview", "analysis", "recruitment", "financial", "other"]
