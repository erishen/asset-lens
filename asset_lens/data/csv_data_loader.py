import csv
import logging
import re
from datetime import date, datetime
from pathlib import Path

from ..core.exceptions import DataLoadError, DataParseError
from ..data.models import InvestmentProduct

logger = logging.getLogger(__name__)


class CSVDataLoaderMixin:
    @classmethod
    def parse_csv_file(cls, csv_path: Path, reference_date: date | None = None) -> list[InvestmentProduct]:
        if not csv_path.exists():
            raise FileNotFoundError(f"CSV 文件不存在: {csv_path}")

        if reference_date is None:
            reference_date = datetime.now().date()

        products = []

        data_dir = csv_path.parent
        usd_rate, hkd_rate = cls.get_exchange_rates(data_dir)

        try:
            with open(csv_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                for _row_num, row in enumerate(reader, start=2):
                    product = cls.parse_row(row, reference_date)
                    if product:
                        from decimal import Decimal

                        if product.usd_rate is None:
                            product.usd_rate = Decimal(str(usd_rate))
                        if product.hkd_rate is None:
                            product.hkd_rate = Decimal(str(hkd_rate))
                        products.append(product)

        except (OSError, csv.Error, DataParseError) as e:
            raise DataLoadError(f"读取 CSV 文件失败: {e}", file_path=str(csv_path)) from e

        return products

    @classmethod
    def load_data(cls, data_path: Path | None = None) -> list[InvestmentProduct]:
        from ..config import config

        if data_path is not None:
            if data_path.is_dir():
                patterns = [
                    "投资产品-表格 1.csv",
                    "投资产品.csv",
                    "*工作表 1*.csv",
                    "*工作表*1*.csv",
                    "*Sheet1*.csv",
                    "*.csv",
                ]

                csv_files = []
                for pattern in patterns:
                    csv_files = list(data_path.glob(pattern))
                    if csv_files:
                        break

                if not csv_files:
                    raise FileNotFoundError(f"数据目录中没有找到 CSV 文件: {data_path}")

                csv_path = csv_files[0]
                logger.info(f"使用数据文件: {csv_path.name}")
            else:
                csv_path = data_path

            return cls.parse_csv_file(csv_path)

        data_path = config.data_path

        if config.is_real_mode:
            data_dirs_to_search = [
                config.project_root / ".." / "ts-demo" / "data",
                config.project_root / "data" / "real",
            ]

            for data_dir in data_dirs_to_search:
                if not data_dir.exists():
                    continue
                dirs = [
                    d
                    for d in data_dir.iterdir()
                    if d.is_dir() and (d.name.startswith("money_csv_") or d.name.startswith("money_"))
                ]

                if dirs:
                    def extract_date(d: Path) -> int:
                        match = re.search(r"(\d{8})", d.name)
                        return int(match.group(1)) if match else 0

                    dirs.sort(key=extract_date, reverse=True)

                    today_suffix = int(datetime.now().strftime("%Y%m%d"))
                    target_dir = None

                    for d in dirs:
                        dir_date = extract_date(d)
                        if dir_date <= today_suffix:
                            target_dir = d
                            break

                    if target_dir is None:
                        target_dir = dirs[0]

                    logger.info(f"使用数据目录: {target_dir.name}")

                    usd_rate, hkd_rate = cls.get_exchange_rates(target_dir)
                    csv_files = list(target_dir.glob("投资产品-表格 1.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("投资产品.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("*工作表 1*.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("*工作表*1*.csv"))
                    if not csv_files:
                        csv_files = list(target_dir.glob("*.csv"))

                    if csv_files:
                        csv_path = csv_files[0]
                        try:
                            products = cls.parse_csv_file(csv_path)
                            dir_date_str = target_dir.name.split("_")[-1]
                            reference_date = datetime.strptime(dir_date_str, "%Y%m%d")
                            products = cls._calculate_irr_for_products(products, reference_date, usd_rate, hkd_rate)
                            logger.info(
                                f"成功加载 {len(products)} 个投资产品, 美元汇率: {usd_rate}, 港元汇率: {hkd_rate}"
                            )
                            return products
                        except (OSError, DataLoadError, DataParseError) as e:
                            logger.error(f"加载数据失败: {e}", exc_info=True)
                            raise

                    logger.warning(f"未找到 CSV 文件: {target_dir}")
                    return []

        if data_path.is_dir():
            patterns = [
                "投资产品-表格 1.csv",
                "投资产品.csv",
                "*工作表 1*.csv",
                "*工作表*1*.csv",
                "*Sheet1*.csv",
                "*.csv",
            ]

            csv_files = []
            for pattern in patterns:
                csv_files = list(data_path.glob(pattern))
                if csv_files:
                    break

            if not csv_files:
                raise FileNotFoundError(f"数据目录中没有找到 CSV 文件: {data_path}")

            csv_path = csv_files[0]
            logger.info(f"使用数据文件: {csv_path.name}")
        else:
            csv_path = data_path

        products = cls.parse_csv_file(csv_path)

        reference_date = datetime.now()
        products = cls._calculate_irr_for_products(
            products, reference_date, float(config.default_usd_rate), float(config.default_hkd_rate)
        )

        return products

    @classmethod
    def load_data_from_dir(cls, data_dir: Path, reference_date: datetime | None = None) -> list[InvestmentProduct]:
        if not data_dir.exists():
            raise FileNotFoundError(f"数据目录不存在: {data_dir}")

        usd_rate, hkd_rate = cls.get_exchange_rates(data_dir)

        dir_date_str = data_dir.name.split("_")[-1]
        parsed_reference_date = None
        try:
            from datetime import datetime

            parsed_reference_date = datetime.strptime(dir_date_str, "%Y%m%d")
        except ValueError:
            pass

        effective_reference_date = reference_date or parsed_reference_date

        patterns = [
            "投资产品-表格 1.csv",
            "投资产品.csv",
            "*工作表 1*.csv",
            "*工作表*1*.csv",
            "*Sheet1*.csv",
            "*.csv",
        ]

        csv_files = []
        for pattern in patterns:
            csv_files = list(data_dir.glob(pattern))
            if csv_files:
                break

        if not csv_files:
            raise FileNotFoundError(f"数据目录中没有找到 CSV 文件: {data_dir}")

        csv_path = csv_files[0]

        csv_reference_date: date | None = None
        if effective_reference_date and hasattr(effective_reference_date, 'date'):
            csv_reference_date = effective_reference_date.date()
        products = cls.parse_csv_file(csv_path, reference_date=csv_reference_date)

        if effective_reference_date:
            products = cls._calculate_irr_for_products(products, effective_reference_date, usd_rate, hkd_rate)

        return products
