# -*- coding: utf-8 -*-
"""
HTML 报告渲染服务
使用 Jinja2 模板引擎渲染新闻报告
"""
import re
from pathlib import Path

import markdown
from jinja2 import Environment, FileSystemLoader

from config import BASE_DIR, DATA_DIR
from models.schemas import NewsResponse
from utils.logger import logger

# 模板目录
TEMPLATES_DIR = BASE_DIR / "templates"


def truncate(text: str, length: int = 50) -> str:
    """截断文本"""
    if len(text) <= length:
        return text
    return text[:length] + "..."


def clean_url(url: str) -> str:
    """清理 URL，提取域名"""
    match = re.match(r'https?://([^/]+)', url)
    return match.group(1) if match else url


class ReportRenderer:
    """报告渲染器"""

    def __init__(self):
        self._env = Environment(
            loader=FileSystemLoader(TEMPLATES_DIR),
            autoescape=True
        )
        # 添加自定义过滤器
        self._env.filters['truncate'] = truncate
        self._md = markdown.Markdown(extensions=['tables', 'fenced_code'])
        logger.info(f"ReportRenderer 初始化完成 | 模板目录: {TEMPLATES_DIR}")

    def _markdown_to_html(self, text: str) -> str:
        """将 Markdown 转换为 HTML"""
        self._md.reset()
        return self._md.convert(text)

    def _render_template(self, template_name: str, response: NewsResponse, time_range: str) -> str:
        """渲染指定模板"""
        template = self._env.get_template(template_name)

        # 将整体总结的 Markdown 转换为 HTML
        overall_summary_html = self._markdown_to_html(response.overall_summary)

        return template.render(
            company_name=response.company_name,
            fetch_time=response.fetch_time.strftime("%Y-%m-%d %H:%M:%S"),
            news_count=response.news_count,
            news_list=response.news_list,
            overall_summary=overall_summary_html,
            time_range=time_range
        )

    def render(self, response: NewsResponse, time_range: str = "近一周") -> str:
        """
        渲染新闻详情报告为 HTML

        Args:
            response: 新闻响应对象
            time_range: 时间范围描述

        Returns:
            渲染后的 HTML 字符串
        """
        logger.info(f"开始渲染详情报告 | 公司: {response.company_name}")
        html = self._render_template("report.html", response, time_range)
        logger.info(f"详情报告渲染完成 | 长度: {len(html)} 字符")
        return html

    def render_list(self, response: NewsResponse, time_range: str = "近一周") -> str:
        """
        渲染新闻列表表格页面

        Args:
            response: 新闻响应对象
            time_range: 时间范围描述

        Returns:
            渲染后的 HTML 字符串
        """
        logger.info(f"开始渲染列表页面 | 公司: {response.company_name}")
        html = self._render_template("news_list.html", response, time_range)
        logger.info(f"列表页面渲染完成 | 长度: {len(html)} 字符")
        return html

    def render_and_save(self, response: NewsResponse, time_range: str = "近一周") -> tuple[Path, Path]:
        """
        渲染并保存 HTML 报告（详情页 + 列表页）

        Args:
            response: 新闻响应对象
            time_range: 时间范围描述

        Returns:
            (详情页路径, 列表页路径)
        """
        timestamp = response.fetch_time.strftime("%Y%m%d_%H%M%S")

        # 保存详情页
        detail_html = self.render(response, time_range)
        detail_filename = f"{response.company_name}_{timestamp}_详情.html"
        detail_filepath = DATA_DIR / detail_filename
        with open(detail_filepath, "w", encoding="utf-8") as f:
            f.write(detail_html)
        logger.info(f"详情页已保存 | 文件: {detail_filepath}")

        # 保存列表页
        list_html = self.render_list(response, time_range)
        list_filename = f"{response.company_name}_{timestamp}_列表.html"
        list_filepath = DATA_DIR / list_filename
        with open(list_filepath, "w", encoding="utf-8") as f:
            f.write(list_html)
        logger.info(f"列表页已保存 | 文件: {list_filepath}")

        return detail_filepath, list_filepath


# 单例实例，延迟初始化
_renderer_instance: ReportRenderer | None = None


def get_renderer() -> ReportRenderer:
    """获取报告渲染器实例"""
    global _renderer_instance
    if _renderer_instance is None:
        _renderer_instance = ReportRenderer()
    return _renderer_instance
