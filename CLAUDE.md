# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个 **AI 新闻爬取与摘要系统**，用于自动化搜集科技公司新闻并生成 AI 摘要。主要用于帮助工作人员撰写 AI 及相关科研、论文、产品资讯。

**两阶段产出目标：**
1. **新闻搜集阶段**：搜索并罗列符合"产品/新品/新模型"标准的新闻（非访谈类）
2. **AI 总结阶段**：人工校验后，对符合要求的新闻进行 AI 摘要

## 常用命令

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
# 服务运行在 http://localhost:8000

# API 调用示例
curl -X POST http://localhost:8000/api/news/fetch \
  -H "Content-Type: application/json" \
  -d '{"company_name": "百度"}'
```

## 环境配置

在项目根目录创建 `.env` 文件：
```
TAVILY_API_KEY=your_tavily_key
OPENAI_API_KEY=your_openai_key
OPENAI_BASE_URL=http://localhost:8000/v1  # 自部署模型地址
MODEL_NAME=gpt-3.5-turbo

# PostgreSQL 数据库配置
DB_HOST=localhost
DB_PORT=5432
DB_NAME=news_db
DB_USER=postgres
DB_PASSWORD=your_password
```

## 架构说明

```
news/
├── main.py              # FastAPI 入口，定义 /api/news/fetch 端点
├── config.py            # 环境变量和配置常量
├── models/
│   └── schemas.py       # Pydantic 数据模型 (NewsRequest, NewsItem, NewsResponse)
├── services/            # 核心业务服务（均采用单例模式）
│   ├── keyword_generator.py  # 使用 LLM 生成多维度搜索关键词
│   ├── news_crawler.py       # 使用 Tavily API 爬取新闻
│   ├── summarizer.py         # 使用 LLM 生成摘要和总结
│   └── renderer.py           # Jinja2 模板渲染 HTML 报告
├── templates/           # HTML 模板
│   ├── report.html      # 新闻详情报告模板
│   └── news_list.html   # 新闻列表表格模板
├── utils/
│   └── logger.py        # 日志配置
└── data/news/           # 输出文件存储目录 (JSON + HTML)
```

## 处理流程

`/api/news/fetch` 端点的 6 步处理流程：
1. **KeywordGenerator** → LLM 生成 8-12 个多维度搜索关键词
2. **NewsCrawler** → 每个关键词搜索 2 条新闻，URL 去重
3. **Summarizer.summarize_single** → 逐条生成中文摘要
4. 构建 NewsResponse 响应对象
5. **Renderer** → 保存 JSON + 详情页 HTML + 列表页 HTML
6. 返回列表页 HTML

## 关键技术点

- **服务单例模式**：各服务通过 `get_*()` 函数获取单例实例，延迟初始化
- **Tavily API**：用于新闻搜索（`topic="news"`），支持 `include_raw_content`
- **OpenAI 兼容接口**：支持自部署模型，通过 `OPENAI_BASE_URL` 配置
- **LLM 调用带重试**：`Summarizer._call_llm()` 实现了重试机制

## 输出文件

每次查询生成三个文件到 `data/news/`：
- `{公司名}_{时间戳}.json` - 原始数据
- `{公司名}_{时间戳}_详情.html` - 详细报告
- `{公司名}_{时间戳}_列表.html` - 表格列表

---

## 两阶段系统 (v2 API)

新增的两阶段处理系统，支持人工审核介入。

### 新增架构

```
news/
├── database/                    # PostgreSQL 数据库模块
│   ├── connection.py            # 数据库连接管理（单例，psycopg2）
│   └── repository.py            # 数据访问层（CRUD）
├── services/
│   └── news_classifier.py       # AI 新闻分类服务
├── templates/
│   ├── review_list.html         # 审核列表页面（支持勾选）
│   └── final_report.html        # 最终报告页面
```

### v2 API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v2/news/collect` | POST | 阶段一：搜集新闻 + AI 初筛 |
| `/api/v2/tasks/{task_id}/review` | GET | 获取审核页面 (HTML) |
| `/api/v2/news/review` | POST | 阶段二：提交审核 + 生成报告 |
| `/api/v2/tasks` | GET | 任务列表 |
| `/api/v2/tasks/{task_id}` | GET | 任务详情 |

### 两阶段流程

**阶段一：POST /api/v2/news/collect**
```bash
curl -X POST http://localhost:8000/api/v2/news/collect \
  -H "Content-Type: application/json" \
  -d '{"company_name": "百度"}'
```
返回 `task_id`，用于后续审核。

**查看审核页面：GET /api/v2/tasks/{task_id}/review**
浏览器访问 `http://localhost:8000/api/v2/tasks/1/review`

**阶段二：提交审核**
在审核页面勾选符合要求的新闻，点击提交，系统自动生成 AI 摘要和最终报告。

### AI 分类标准

符合要求（待审核）：
- `product_release` - 产品发布
- `model_release` - 新模型发布
- `feature_update` - 新功能更新

自动过滤：
- `interview` - 访谈/人物故事
- `analysis` - 行业分析/评论
- `recruitment` - 招聘/活动公告
- `financial` - 财报/股价新闻
- `other` - 其他

### 数据库表

- `search_tasks` - 搜索任务（company_name, status, keywords_used...）
- `news_items` - 新闻条目（task_id, title, url, ai_category, status, summary...）
