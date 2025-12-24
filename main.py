# -*- coding: utf-8 -*-
"""
公司新闻爬取与摘要生成系统
FastAPI 应用入口
"""
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, Form
from fastapi.responses import JSONResponse, HTMLResponse

from config import DATA_DIR
from models.schemas import NewsRequest, NewsResponse, NewsItem, ErrorResponse, Phase1Request, Phase1Response
from services.keyword_generator import get_keyword_generator
from services.news_crawler import get_news_crawler
from services.summarizer import get_summarizer
from services.renderer import get_renderer
from services.news_classifier import get_news_classifier
from database.repository import get_repository
from utils.logger import logger

app = FastAPI(
    title="公司新闻爬取与摘要系统",
    description="输入公司名称，自动爬取近期新闻并生成AI摘要",
    version="1.0.0"
)


def save_to_json(response: NewsResponse) -> Path:
    """将结果保存到 JSON 文件"""
    timestamp = response.fetch_time.strftime("%Y%m%d_%H%M%S")
    filename = f"{response.company_name}_{timestamp}.json"
    filepath = DATA_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(response.model_dump(mode="json"), f, ensure_ascii=False, indent=2)

    logger.info(f"JSON 已保存 | 文件: {filepath}")
    return filepath


@app.post(
    "/api/news/fetch",
    response_class=HTMLResponse,
    summary="获取公司新闻并生成报告",
    description="输入公司名称，使用 SOP 生成多维度关键词，逐个搜索新闻，为每条新闻生成AI摘要"
)
async def fetch_news(request: NewsRequest):
    """
    获取公司新闻并生成报告

    - **company_name**: 公司名称（必填）

    处理流程：
    1. 使用大模型生成多维度搜索关键词
    2. 逐个关键词搜索新闻（每个关键词 2 条）
    3. 新闻去重
    4. 逐条为每条新闻生成 AI 摘要
    5. 生成整体总结
    6. 保存 JSON + 详情页 + 列表页
    7. 返回列表页面
    """
    logger.info(f"================== 新请求 ==================")
    logger.info(f"收到请求 | 公司名称: {request.company_name}")

    try:
        # 步骤 1: 生成搜索关键词
        logger.info("步骤 1/6: 生成搜索关键词...")
        keyword_generator = get_keyword_generator()
        keywords = keyword_generator.generate_keywords(request.company_name)

        # 步骤 2: 多关键词搜索新闻
        logger.info("步骤 2/6: 多关键词搜索新闻...")
        crawler = get_news_crawler()
        news_list = crawler.fetch_news_by_keywords(keywords, news_per_keyword=2)

        if not news_list:
            logger.warning(f"未找到相关新闻 | 公司: {request.company_name}")
            return HTMLResponse(content=f"""
                <!DOCTYPE html>
                <html><head><meta charset="UTF-8"><title>未找到新闻</title></head>
                <body style="font-family: sans-serif; padding: 40px; text-align: center; background: #f8f9fc;">
                <h1 style="color: #8b5cf6;">未找到相关新闻</h1>
                <p>公司: {request.company_name}</p>
                <p>搜索了 {len(keywords)} 个关键词，但未找到相关新闻。</p>
                </body></html>
            """)

        # 步骤 3: 逐条生成摘要
        logger.info("步骤 3/6: 逐条生成摘要...")
        summarizer = get_summarizer()
        news_list, overall_summary = summarizer.process_news_list(news_list, request.company_name)

        # 步骤 4: 构建响应对象
        logger.info("步骤 4/6: 构建响应...")
        response = NewsResponse(
            company_name=request.company_name,
            fetch_time=datetime.now(),
            news_count=len(news_list),
            news_list=news_list,
            overall_summary=overall_summary
        )

        # 步骤 5: 保存所有文件
        logger.info("步骤 5/6: 保存文件...")
        json_path = save_to_json(response)

        renderer = get_renderer()
        detail_path, list_path = renderer.render_and_save(response)

        # 步骤 6: 返回列表页面
        logger.info("步骤 6/6: 返回列表页面...")
        html = renderer.render_list(response)

        logger.info(f"========== 请求处理完成 ==========")
        logger.info(f"公司: {request.company_name}")
        logger.info(f"搜索关键词: {len(keywords)} 个")
        logger.info(f"新闻数量: {response.news_count} 条")
        logger.info(f"已保存文件:")
        logger.info(f"  - {json_path.name}")
        logger.info(f"  - {detail_path.name}")
        logger.info(f"  - {list_path.name}")
        logger.info(f"====================================")

        return HTMLResponse(content=html)

    except ValueError as e:
        logger.error(f"配置错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")


@app.get("/", response_class=HTMLResponse, summary="首页")
async def home():
    """系统首页 - 可视化操作界面"""
    renderer = get_renderer()
    template = renderer._env.get_template("index.html")
    return HTMLResponse(content=template.render())


@app.get("/api/health", summary="健康检查")
async def health_check():
    """API 健康检查"""
    return {"status": "ok", "message": "公司新闻爬取与摘要系统运行中"}




# ========== 两阶段系统 API (v2) ==========

@app.post(
    "/api/v2/news/collect",
    response_model=Phase1Response,
    summary="阶段一：新闻搜集与AI初筛",
    tags=["v2-两阶段系统"]
)
async def phase1_collect_news(request: Phase1Request):
    """
    阶段一：搜集新闻并进行AI初筛

    流程：
    1. 生成搜索关键词
    2. 搜索新闻
    3. AI 分类判断
    4. 存入数据库
    5. 返回统计信息
    """
    logger.info(f"======== 阶段一开始 | 公司: {request.company_name} ========")

    repo = get_repository()

    # 1. 生成关键词
    logger.info("步骤 1/4: 生成搜索关键词...")
    keyword_generator = get_keyword_generator()
    keywords = keyword_generator.generate_keywords(request.company_name)

    # 2. 创建任务
    logger.info("步骤 2/4: 创建搜索任务...")
    task_id = repo.create_task(request.company_name, keywords)

    # 3. 搜索新闻
    logger.info("步骤 3/4: 搜索新闻...")
    crawler = get_news_crawler()
    news_list = crawler.fetch_news_by_keywords(keywords, news_per_keyword=2)

    if not news_list:
        repo.update_task_status(task_id, status="completed", total_fetched=0)
        return Phase1Response(
            task_id=task_id,
            company_name=request.company_name,
            total_fetched=0,
            pending_review_count=0,
            filtered_count=0,
            message="未找到相关新闻"
        )

    # 4. AI 批量分类
    logger.info("步骤 4/4: AI 批量分类...")
    classifier = get_news_classifier()

    # 构建批量分类输入
    news_for_classify = [
        {"id": i + 1, "title": news.title, "content": news.content}
        for i, news in enumerate(news_list)
    ]

    # 一次调用完成所有分类和去重
    classify_results = classifier.classify_batch(news_for_classify)

    # 处理分类结果并存储
    pending_count = 0
    filtered_count = 0
    duplicate_count = 0
    added_count = 0

    for i, news in enumerate(news_list):
        result = classify_results[i]
        category = result["category"]

        # 判断状态
        if category == "duplicate":
            status = "filtered"
            duplicate_count += 1
        elif classifier.is_valid_category(category):
            status = "pending_review"
            pending_count += 1
        else:
            status = "filtered"
            filtered_count += 1

        # 构建存储数据
        news_data = {
            "title": news.title,
            "url": news.url,
            "published_date": news.published_date,
            "content": news.content,
            "ai_category": category,
            "ai_relevance": 0.9 if status == "pending_review" else 0.3,
            "ai_reason": result["reason"],
            "status": status
        }

        # 存入数据库
        news_id = repo.add_news_item(task_id, news_data)
        if news_id:
            added_count += 1

        logger.info(f"  [{i+1}/{len(news_list)}] {category}: {news.title[:40]}...")

    # 5. 更新任务状态
    repo.update_task_status(
        task_id,
        status="reviewing",
        total_fetched=added_count
    )

    logger.info(f"======== 阶段一完成 | 任务ID: {task_id} ========")
    logger.info(f"  总计: {added_count} | 待审核: {pending_count} | 重复: {duplicate_count} | 过滤: {filtered_count}")

    return Phase1Response(
        task_id=task_id,
        company_name=request.company_name,
        total_fetched=added_count,
        pending_review_count=pending_count,
        filtered_count=filtered_count + duplicate_count,
        message=f"搜集完成，{pending_count} 条待审核，{duplicate_count} 条重复，{filtered_count} 条过滤"
    )


@app.get(
    "/api/v2/tasks/{task_id}/review",
    response_class=HTMLResponse,
    summary="获取审核页面",
    tags=["v2-两阶段系统"]
)
async def get_review_page(task_id: int):
    """返回人工审核页面"""
    repo = get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 获取待审核新闻（AI 判断符合要求的）
    news_list = repo.get_pending_review_news(task_id)
    # 获取被过滤的新闻
    filtered_list = repo.get_filtered_news(task_id)

    renderer = get_renderer()
    html = renderer.render_review_list(task, news_list, filtered_list)

    return HTMLResponse(content=html)


@app.post(
    "/api/v2/news/review",
    response_class=HTMLResponse,
    summary="阶段二：提交审核结果并生成报告",
    tags=["v2-两阶段系统"]
)
async def phase2_submit_review(
    task_id: int = Form(...),
    approved_ids: str = Form("")
):
    """
    阶段二：处理人工审核结果

    流程：
    1. 更新新闻状态
    2. 为通过的新闻生成摘要
    3. 生成整体总结
    4. 返回最终报告
    """
    logger.info(f"======== 阶段二开始 | 任务ID: {task_id} ========")

    repo = get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 解析通过的新闻 ID
    approved_news_ids = []
    if approved_ids:
        approved_news_ids = [int(x.strip()) for x in approved_ids.split(",") if x.strip()]

    logger.info(f"用户选择了 {len(approved_news_ids)} 条新闻")

    # 获取所有待审核新闻
    all_pending = repo.get_pending_review_news(task_id)
    all_pending_ids = [n["id"] for n in all_pending]

    # 计算被拒绝的新闻
    rejected_ids = [id for id in all_pending_ids if id not in approved_news_ids]

    # 更新状态
    repo.batch_update_news_status(approved_news_ids, "approved")
    repo.batch_update_news_status(rejected_ids, "rejected")

    # 如果没有选择任何新闻
    if not approved_news_ids:
        repo.update_task_status(task_id, status="completed", total_approved=0)
        renderer = get_renderer()
        html = renderer.render_final_report(task, [], "没有选择任何新闻进行总结。")
        return HTMLResponse(content=html)

    # 为通过的新闻生成摘要
    logger.info("生成新闻摘要...")
    summarizer = get_summarizer()
    approved_news = repo.get_news_by_ids(approved_news_ids)

    for i, news_dict in enumerate(approved_news, 1):
        logger.info(f"  [{i}/{len(approved_news)}] 摘要: {news_dict['title'][:40]}...")

        # 转换为 NewsItem 以便调用 summarizer
        news_item = NewsItem(
            title=news_dict["title"],
            url=news_dict["url"],
            published_date=news_dict["published_date"],
            content=news_dict["content"],
            summary=""
        )
        summary = summarizer.summarize_single(news_item)

        # 更新数据库
        repo.update_news_summary(news_dict["id"], summary)
        news_dict["summary"] = summary

    # 生成整体总结
    logger.info("生成整体总结...")
    news_items_for_summary = [
        NewsItem(
            title=n["title"],
            url=n["url"],
            published_date=n["published_date"],
            content=n["content"],
            summary=n["summary"]
        ) for n in approved_news
    ]
    overall_summary = summarizer.summarize_all(news_items_for_summary, task["company_name"])

    # 更新任务状态
    repo.update_task_status(
        task_id,
        status="completed",
        total_approved=len(approved_news_ids),
        overall_summary=overall_summary
    )

    # 渲染最终报告
    renderer = get_renderer()
    html = renderer.render_final_report(task, approved_news, overall_summary)

    logger.info(f"======== 阶段二完成 | 任务ID: {task_id} ========")
    logger.info(f"  通过: {len(approved_news_ids)} | 拒绝: {len(rejected_ids)}")

    return HTMLResponse(content=html)


@app.get(
    "/api/v2/tasks",
    summary="获取所有任务列表",
    tags=["v2-两阶段系统"]
)
async def get_all_tasks():
    """获取所有搜索任务"""
    repo = get_repository()
    tasks = repo.get_all_tasks()
    return {"tasks": tasks}


@app.get(
    "/api/v2/tasks/{task_id}",
    summary="获取任务详情",
    tags=["v2-两阶段系统"]
)
async def get_task_detail(task_id: int):
    """获取任务详情及其新闻列表"""
    repo = get_repository()
    task = repo.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    news_list = repo.get_news_by_task(task_id)

    return {
        "task": task,
        "news_list": news_list
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("启动服务 | 端口: 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
