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

# Tavily API 配置
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# 自部署大模型配置 (OpenAI 兼容格式)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:8000/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-3.5-turbo")

# 新闻爬取配置
NEWS_MAX_RESULTS = 10  # 最多返回的新闻条数
NEWS_TIME_RANGE = "week"  # 时间范围：day, week, month, year
