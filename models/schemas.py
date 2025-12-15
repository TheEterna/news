# -*- coding: utf-8 -*-
"""
数据模型定义
使用 Pydantic 定义请求和响应的数据结构
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class NewsRequest(BaseModel):
    """新闻查询请求"""
    company_name: str = Field(..., description="公司名称", min_length=1)


class NewsItem(BaseModel):
    """单条新闻"""
    title: str = Field(..., description="新闻标题")
    url: str = Field(..., description="新闻链接")
    published_date: Optional[str] = Field(None, description="发布日期")
    content: str = Field("", description="新闻内容")
    summary: str = Field("", description="AI生成的摘要")


class NewsResponse(BaseModel):
    """新闻查询响应"""
    company_name: str = Field(..., description="公司名称")
    fetch_time: datetime = Field(default_factory=datetime.now, description="查询时间")
    news_count: int = Field(0, description="新闻数量")
    news_list: list[NewsItem] = Field(default_factory=list, description="新闻列表")
    overall_summary: str = Field("", description="整体总结")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细信息")
