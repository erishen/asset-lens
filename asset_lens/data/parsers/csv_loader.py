"""
CSV Loader - CSV 文件加载器
"""

import csv
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
from datetime import date

from ..models import InvestmentProduct
from .product_parser import ProductParser


class CSVLoader:
    """CSV 文件加载器"""

    @classmethod
    def parse_csv_file(
        cls,
        file_path: Path,
        reference_date: date | None = None,
    ) -> list[InvestmentProduct]:
        """解析单个 CSV 文件"""
        products: list[InvestmentProduct] = []

        if not file_path.exists():
            return products

        try:
            with open(file_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    product = ProductParser.parse_row(row, reference_date)
                    if product:
                        products.append(product)
        except (OSError, ValueError, KeyError) as e:
            logger.error(f"解析文件 {file_path} 失败: {e}")

        return products

    @classmethod
    def load_data(cls, data_path: Path | None = None) -> list[InvestmentProduct]:
        """加载投资数据"""
        from ...config import config

        if data_path is None:
            data_path = config.sample_data_path

        if data_path.is_file():
            return cls.parse_csv_file(data_path)
        elif data_path.is_dir():
            return cls.load_data_from_dir(data_path)

        return []

    @classmethod
    def load_data_from_dir(cls, data_dir: Path) -> list[InvestmentProduct]:
        """从目录加载所有数据文件"""
        all_products = []

        csv_files = list(data_dir.glob("*.csv"))

        for csv_file in csv_files:
            products = cls.parse_csv_file(csv_file)
            all_products.extend(products)

        return all_products


csv_loader = CSVLoader()
