"""
Personal data integrator for asset-lens.
个人数据整合模块 - 整合用户每周记录的指数、汇率等数据

功能:
1. 读取每周记录的指数数据（上证、沪深、中证、QQQ、黄金等）
2. 读取汇率数据（美元、港元）
3. 读取美联储利率等宏观指标
4. 整合到市场环境分析中
"""

import csv
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..config import config


@dataclass
class WeeklyIndexRecord:
    """每周指数记录"""
    date: str
    indices: Dict[str, float]  # 指数名称 -> 数值
    etfs: Dict[str, float]  # ETF名称 -> 数值
    rates: Dict[str, float]  # 汇率名称 -> 数值


@dataclass
class PersonalDataConfig:
    """个人数据配置"""
    ts_demo_path: str = ""
    index_file_pattern: str = "股市指数-表格 1.csv"
    etf_file_pattern: str = "美元ETF-表格 1.csv"
    asset_file_pattern: str = "资产汇总-表格 1.csv"


class PersonalDataIntegrator:
    """个人数据整合器"""

    INDEX_MAPPING = {
        "沪深300": "hs300",
        "中证500": "zz500",
        "科创50": "kc50",
        "中证1000": "zz1000",
        "国证2000": "gz2000",
        "上证50": "sz50",
        "恒生指数": "hsi",
        "国企指数": "hscei",
        "恒生科技指数": "hstech",
        "上证指数": "szzs",
        "深证成指": "szcz",
        "创业板指": "cybz",
    }

    ETF_MAPPING = {
        "QQQ": "qqq",
        "SPY": "spy",
        "GLD": "gld",
        "VXX": "vxx",
    }

    RATE_MAPPING = {
        "美元汇率": "usd_rate",
        "港元汇率": "hkd_rate",
    }

    def __init__(self):
        self.cache_path = config.cache_path
        self.cache_file = self.cache_path / "personal_market_data.json"
        self.weekly_records: List[WeeklyIndexRecord] = []
        self.config = PersonalDataConfig()

        ts_demo_path = Path(__file__).parent.parent.parent.parent / "ts-demo" / "data"
        if ts_demo_path.exists():
            self.config.ts_demo_path = str(ts_demo_path)

        self._load_cache()

    def _load_cache(self) -> None:
        """加载缓存数据"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.weekly_records = [
                        WeeklyIndexRecord(
                            date=r.get("date", ""),
                            indices=r.get("indices", {}),
                            etfs=r.get("etfs", {}),
                            rates=r.get("rates", {}),
                        )
                        for r in data.get("weekly_records", [])
                    ]
            except Exception as e:
                print(f"加载个人数据缓存失败: {e}")

    def _save_cache(self) -> None:
        """保存缓存数据"""
        data = {
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weekly_records": [
                {
                    "date": r.date,
                    "indices": r.indices,
                    "etfs": r.etfs,
                    "rates": r.rates,
                }
                for r in self.weekly_records
            ],
        }
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_weekly_data(self) -> int:
        """
        从 ts-demo 目录加载每周数据

        Returns:
            加载的记录数
        """
        if not self.config.ts_demo_path:
            print("未找到 ts-demo 数据目录")
            return 0

        ts_demo_path = Path(self.config.ts_demo_path)
        backup_path = ts_demo_path / "backup"

        if not backup_path.exists():
            backup_path = ts_demo_path

        loaded = 0
        for folder in sorted(backup_path.iterdir()):
            if not folder.is_dir():
                continue

            date_str = folder.name.replace("money_csv_", "")
            try:
                record = self._load_folder_data(folder, date_str)
                if record:
                    existing = [r for r in self.weekly_records if r.date == record.date]
                    if existing:
                        idx = self.weekly_records.index(existing[0])
                        self.weekly_records[idx] = record
                    else:
                        self.weekly_records.append(record)
                    loaded += 1
            except Exception as e:
                print(f"加载 {folder.name} 失败: {e}")

        for folder in sorted(ts_demo_path.iterdir()):
            if not folder.is_dir() or folder.name == "backup" or folder.name == "demo_data":
                continue

            date_str = folder.name.replace("money_csv_", "")
            try:
                record = self._load_folder_data(folder, date_str)
                if record:
                    existing = [r for r in self.weekly_records if r.date == record.date]
                    if existing:
                        idx = self.weekly_records.index(existing[0])
                        self.weekly_records[idx] = record
                    else:
                        self.weekly_records.append(record)
                    loaded += 1
            except Exception as e:
                print(f"加载 {folder.name} 失败: {e}")

        self.weekly_records.sort(key=lambda x: x.date)
        self._save_cache()
        return loaded

    def _load_folder_data(self, folder: Path, date_str: str) -> Optional[WeeklyIndexRecord]:
        """加载单个文件夹的数据"""
        indices = {}
        etfs = {}
        rates = {}

        index_file = folder / self.config.index_file_pattern
        if index_file.exists():
            indices = self._parse_index_file(index_file)

        etf_file = folder / self.config.etf_file_pattern
        if etf_file.exists():
            etfs = self._parse_etf_file(etf_file)

        asset_file = folder / self.config.asset_file_pattern
        if asset_file.exists():
            rates = self._parse_asset_file(asset_file)

        if indices or etfs or rates:
            return WeeklyIndexRecord(
                date=date_str,
                indices=indices,
                etfs=etfs,
                rates=rates,
            )
        return None

    def _parse_index_file(self, file_path: Path) -> Dict[str, float]:
        """解析指数文件"""
        indices = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过标题行
                for row in reader:
                    if len(row) >= 2:
                        name = row[0].strip()
                        try:
                            value = float(row[1].strip())
                            if name in self.INDEX_MAPPING:
                                indices[self.INDEX_MAPPING[name]] = value
                        except (ValueError, IndexError):
                            pass
        except Exception as e:
            print(f"解析指数文件失败 {file_path}: {e}")
        return indices

    def _parse_etf_file(self, file_path: Path) -> Dict[str, float]:
        """解析ETF文件"""
        etfs = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # 跳过标题行
                for row in reader:
                    if len(row) >= 2:
                        name = row[0].strip()
                        try:
                            value = float(row[1].strip())
                            if name in self.ETF_MAPPING:
                                etfs[self.ETF_MAPPING[name]] = value
                        except (ValueError, IndexError):
                            pass
        except Exception as e:
            print(f"解析ETF文件失败 {file_path}: {e}")
        return etfs

    def _parse_asset_file(self, file_path: Path) -> Dict[str, float]:
        """解析资产汇总文件"""
        rates: Dict[str, float] = {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, None)
                if not header:
                    return rates

                usd_idx: Optional[int] = None
                hkd_idx: Optional[int] = None
                for i, h in enumerate(header):
                    if "美元汇率" in h:
                        usd_idx = i
                    elif "港元汇率" in h:
                        hkd_idx = i

                last_row: Optional[List[str]] = None
                for row in reader:
                    if row:
                        last_row = row

                if last_row:
                    if usd_idx is not None and usd_idx < len(last_row):
                        try:
                            rates["usd_rate"] = float(last_row[usd_idx])
                        except ValueError:
                            pass
                    if hkd_idx and hkd_idx < len(last_row):
                        try:
                            rates["hkd_rate"] = float(last_row[hkd_idx])
                        except ValueError:
                            pass

        except Exception as e:
            print(f"解析资产文件失败 {file_path}: {e}")
        return rates

    def get_index_history(self, index_name: str, days: int = 60) -> List[Tuple[str, float]]:
        """
        获取指数历史数据

        Args:
            index_name: 指数名称（支持中文或英文代码）
            days: 天数

        Returns:
            [(日期, 数值), ...]
        """
        key = self.INDEX_MAPPING.get(index_name, index_name)
        history = []

        for record in self.weekly_records[-days:]:
            if key in record.indices:
                history.append((record.date, record.indices[key]))

        return history

    def get_etf_history(self, etf_name: str, days: int = 60) -> List[Tuple[str, float]]:
        """
        获取ETF历史数据

        Args:
            etf_name: ETF名称
            days: 天数

        Returns:
            [(日期, 数值), ...]
        """
        key = self.ETF_MAPPING.get(etf_name, etf_name.lower())
        history = []

        for record in self.weekly_records[-days:]:
            if key in record.etfs:
                history.append((record.date, record.etfs[key]))

        return history

    def get_rate_history(self, rate_name: str, days: int = 60) -> List[Tuple[str, float]]:
        """
        获取汇率历史数据

        Args:
            rate_name: 汇率名称
            days: 天数

        Returns:
            [(日期, 数值), ...]
        """
        key = self.RATE_MAPPING.get(rate_name, rate_name.lower())
        history = []

        for record in self.weekly_records[-days:]:
            if key in record.rates:
                history.append((record.date, record.rates[key]))

        return history

    def calculate_index_change(
        self, index_name: str, days: int = 5
    ) -> Tuple[float, float, float]:
        """
        计算指数涨跌幅

        Args:
            index_name: 指数名称
            days: 天数

        Returns:
            (当前值, 涨跌幅, 涨跌点数)
        """
        history = self.get_index_history(index_name, days + 1)
        if len(history) < 2:
            return 0, 0, 0

        current = history[-1][1]
        previous = history[0][1]

        if previous == 0:
            return current, 0, 0

        change = current - previous
        change_pct = (change / previous) * 100

        return current, change_pct, change

    def get_market_summary(self) -> Dict[str, Any]:
        """
        获取市场概况

        Returns:
            市场概况数据
        """
        if not self.weekly_records:
            return {"error": "没有数据"}

        latest_with_indices = None
        latest_with_etfs = None
        latest_with_rates = None

        for record in reversed(self.weekly_records):
            if not latest_with_indices and record.indices:
                latest_with_indices = record
            if not latest_with_etfs and record.etfs:
                latest_with_etfs = record
            if not latest_with_rates and record.rates:
                latest_with_rates = record
            if latest_with_indices and latest_with_etfs and latest_with_rates:
                break

        previous_with_indices = None
        previous_with_etfs = None
        previous_with_rates = None

        if latest_with_indices:
            for record in reversed(self.weekly_records):
                if record.date != latest_with_indices.date and record.indices:
                    previous_with_indices = record
                    break

        if latest_with_etfs:
            for record in reversed(self.weekly_records):
                if record.date != latest_with_etfs.date and record.etfs:
                    previous_with_etfs = record
                    break

        if latest_with_rates:
            for record in reversed(self.weekly_records):
                if record.date != latest_with_rates.date and record.rates:
                    previous_with_rates = record
                    break

        summary: Dict[str, Any] = {
            "date": self.weekly_records[-1].date,
            "index_date": latest_with_indices.date if latest_with_indices else None,
            "etf_date": latest_with_etfs.date if latest_with_etfs else None,
            "rate_date": latest_with_rates.date if latest_with_rates else None,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indices": {},
            "etfs": {},
            "rates": {},
        }

        indices_dict: Dict[str, Any] = summary["indices"]
        etfs_dict: Dict[str, Any] = summary["etfs"]
        rates_dict: Dict[str, Any] = summary["rates"]

        if latest_with_indices:
            for name, key in self.INDEX_MAPPING.items():
                current = latest_with_indices.indices.get(key, 0)
                prev_val = previous_with_indices.indices.get(key, 0) if previous_with_indices else 0

                if current and prev_val:
                    change_pct = ((current - prev_val) / prev_val) * 100
                else:
                    change_pct = 0

                indices_dict[name] = {
                    "value": current,
                    "change_pct": round(change_pct, 2),
                }

        if latest_with_etfs:
            for name, key in self.ETF_MAPPING.items():
                current = latest_with_etfs.etfs.get(key, 0)
                prev_val = previous_with_etfs.etfs.get(key, 0) if previous_with_etfs else 0

                if current and prev_val:
                    change_pct = ((current - prev_val) / prev_val) * 100
                else:
                    change_pct = 0

                etfs_dict[name] = {
                    "value": current,
                    "change_pct": round(change_pct, 2),
                }

        if latest_with_rates:
            rates_dict["usd_rate"] = latest_with_rates.rates.get("usd_rate", 0)
            rates_dict["hkd_rate"] = latest_with_rates.rates.get("hkd_rate", 0)

        return summary

    def print_market_summary(self) -> None:
        """打印市场概况"""
        summary = self.get_market_summary()

        print("\n" + "=" * 60)
        print("📊 个人数据市场概况")
        print("=" * 60)
        print(f"数据日期: {summary.get('date', 'N/A')}")

        if summary.get("index_date"):
            print(f"指数数据日期: {summary.get('index_date')}")
        if summary.get("rate_date"):
            print(f"汇率数据日期: {summary.get('rate_date')}")

        indices = summary.get("indices", {})
        if indices:
            print("\n📈 国内指数:")
            print("-" * 40)
            for name, data in indices.items():
                value = data.get("value", 0)
                change = data.get("change_pct", 0)
                change_str = f"{change:+.2f}%" if change else "-"
                print(f"  {name}: {value:.2f} ({change_str})")

        etfs = summary.get("etfs", {})
        if etfs:
            print("\n🌍 海外ETF:")
            print("-" * 40)
            for name, data in etfs.items():
                value = data.get("value", 0)
                change = data.get("change_pct", 0)
                change_str = f"{change:+.2f}%" if change else "-"
                print(f"  {name}: {value:.2f} ({change_str})")

        rates = summary.get("rates", {})
        if rates:
            print("\n💱 汇率:")
            print("-" * 40)
            for name, data in rates.items():
                value = data.get("value", 0)
                change = data.get("change", 0)
                change_str = f"{change:+.4f}" if change else "-"
                print(f"  {name}: {value:.4f} ({change_str})")

        print("\n" + "=" * 60)


personal_data_integrator = PersonalDataIntegrator()
