# -*- coding: utf-8 -*-
"""
表格解析服务
支持解析 Excel (.xlsx, .xls) 和 CSV 文件，提取第一列数据
"""
import csv
import io
from typing import BinaryIO

from utils.logger import logger


class SpreadsheetParser:
    """表格解析器"""

    # 支持的文件类型
    SUPPORTED_EXTENSIONS = {'.xlsx', '.xls', '.csv'}

    def parse(self, file: BinaryIO, filename: str) -> list[str]:
        """
        解析上传的表格文件，提取第一列数据（跳过标题行）

        Args:
            file: 文件对象
            filename: 文件名（用于判断文件类型）

        Returns:
            第一列的数据列表（去除空值和重复）
        """
        ext = self._get_extension(filename)

        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {ext}，支持: {', '.join(self.SUPPORTED_EXTENSIONS)}")

        if ext == '.csv':
            return self._parse_csv(file)
        else:
            return self._parse_excel(file)

    def _get_extension(self, filename: str) -> str:
        """获取文件扩展名（小写）"""
        if '.' not in filename:
            return ''
        return '.' + filename.rsplit('.', 1)[-1].lower()

    def _parse_csv(self, file: BinaryIO) -> list[str]:
        """解析 CSV 文件"""
        logger.info("解析 CSV 文件...")

        # 读取文件内容
        content = file.read()

        # 尝试多种编码
        text = None
        for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
            try:
                text = content.decode(encoding)
                logger.info(f"CSV 编码: {encoding}")
                break
            except UnicodeDecodeError:
                continue

        if text is None:
            raise ValueError("无法解析 CSV 文件编码，请使用 UTF-8 或 GBK 编码")

        # 解析 CSV
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)

        return self._extract_first_column(rows)

    def _parse_excel(self, file: BinaryIO) -> list[str]:
        """解析 Excel 文件"""
        logger.info("解析 Excel 文件...")

        try:
            import openpyxl
        except ImportError:
            raise ValueError("需要安装 openpyxl 库来解析 Excel 文件: pip install openpyxl")

        # 从字节流加载工作簿
        workbook = openpyxl.load_workbook(file, read_only=True, data_only=True)
        sheet = workbook.active

        # 读取所有行
        rows = []
        for row in sheet.iter_rows(values_only=True):
            rows.append(list(row))

        workbook.close()
        return self._extract_first_column(rows)

    def _extract_first_column(self, rows: list[list]) -> list[str]:
        """
        从行数据中提取第一列

        Args:
            rows: 所有行数据

        Returns:
            第一列的数据列表（跳过标题行，去空去重，保持顺序）
        """
        if not rows:
            return []

        # 跳过第一行（标题行），提取第一列
        result = []
        seen = set()

        for i, row in enumerate(rows):
            if i == 0:
                # 记录标题行，用于日志
                header = row[0] if row else "无标题"
                logger.info(f"表格标题行第一列: {header}")
                continue

            if not row:
                continue

            value = row[0]
            if value is None:
                continue

            # 转为字符串并清理
            value_str = str(value).strip()
            if not value_str:
                continue

            # 去重但保持顺序
            if value_str not in seen:
                seen.add(value_str)
                result.append(value_str)

        logger.info(f"解析完成 | 提取公司数: {len(result)}")
        return result


# 单例
_parser_instance: SpreadsheetParser | None = None


def get_spreadsheet_parser() -> SpreadsheetParser:
    """获取表格解析器实例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = SpreadsheetParser()
    return _parser_instance
