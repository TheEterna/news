# -*- coding: utf-8 -*-
"""
公司新闻爬取与摘要生成系统
FastAPI 应用入口
"""
import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

from config import DATA_DIR
from models.schemas import NewsRequest, NewsResponse, ErrorResponse
from services.keyword_generator import get_keyword_generator
from services.news_crawler import get_news_crawler
from services.summarizer import get_summarizer
from services.renderer import get_renderer
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


@app.get("/", summary="健康检查")
async def health_check():
    """API 健康检查"""
    return {"status": "ok", "message": "公司新闻爬取与摘要系统运行中"}


if __name__ == "__main__":
    import uvicorn
    logger.info("启动服务 | 端口: 8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
