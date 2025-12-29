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
    source_engine: str = Field("", description="来源搜索引擎")


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


# ========== 两阶段系统新增模型 ==========

class Phase1Request(BaseModel):
    """阶段一请求：新闻搜集"""
    company_name: str = Field(..., description="公司名称", min_length=1)
    keyword_count: Optional[int] = Field(None, description="关键词数量（可选）", ge=1, le=10)
    news_per_keyword: Optional[int] = Field(None, description="每个关键词搜索的新闻数（可选）", ge=1, le=10)


class Phase1Response(BaseModel):
    """阶段一响应"""
    task_id: int = Field(..., description="任务ID")
    company_name: str = Field(..., description="公司名称")
    total_fetched: int = Field(0, description="总抓取数量")
    pending_review_count: int = Field(0, description="待审核数量")
    filtered_count: int = Field(0, description="已过滤数量")
    message: str = Field("", description="提示信息")


class Phase2ReviewRequest(BaseModel):
    """阶段二请求：审核提交"""
    task_id: int = Field(..., description="任务ID")
    approved_news_ids: list[int] = Field(default_factory=list, description="确认通过的新闻ID列表")


class Phase2Response(BaseModel):
    """阶段二响应"""
    task_id: int = Field(..., description="任务ID")
    company_name: str = Field(..., description="公司名称")
    approved_count: int = Field(0, description="通过数量")
    overall_summary: str = Field("", description="整体总结")
    message: str = Field("", description="提示信息")


class TaskInfo(BaseModel):
    """搜索任务信息"""
    id: int
    company_name: str
    created_at: str
    status: str
    total_fetched: int
    total_approved: int


# ========== 批量任务相关模型 ==========

class BatchTaskResult(BaseModel):
    """单个批量任务的结果"""
    company_name: str = Field(..., description="公司名称")
    task_id: Optional[int] = Field(None, description="任务ID（成功时）")
    success: bool = Field(..., description="是否成功")
    message: str = Field("", description="结果信息")


class BatchUploadResponse(BaseModel):
    """批量上传响应"""
    batch_id: int = Field(..., description="批次ID")
    batch_name: str = Field("", description="批次名称")
    total_companies: int = Field(0, description="解析到的公司总数")
    success_count: int = Field(0, description="成功创建任务数")
    failed_count: int = Field(0, description="失败数")
    results: list[BatchTaskResult] = Field(default_factory=list, description="详细结果列表")


class BatchInfo(BaseModel):
    """批次信息"""
    id: int
    name: str
    filename: Optional[str] = None
    total_companies: int = 0
    success_count: int = 0
    failed_count: int = 0
    created_at: str
    status: str
    tasks: list[TaskInfo] = Field(default_factory=list, description="批次下的任务列表")
