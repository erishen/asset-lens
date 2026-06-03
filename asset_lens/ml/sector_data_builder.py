"""
Sector ML Data Builder.
板块机器学习数据集构建器
"""

import logging
from datetime import datetime, timedelta

import pandas as pd
from tqdm import tqdm

from asset_lens.db.database import db_manager
from asset_lens.ml.sector_rotation import SECTOR_MAPPING

logger = logging.getLogger(__name__)


class SectorDataBuilder:
    """构建用于板块预测的机器学习数据集"""

    def __init__(self, start_date: str, end_date: str, future_days: int = 5):
        self.start_date = start_date
        self.end_date = end_date
        self.future_days = future_days
        self.stock_klines: pd.DataFrame | None = None
        self.north_flow: pd.DataFrame | None = None
        self.market_index: pd.DataFrame | None = None

    def _fetch_data(self):
        """一次性获取所有需要的数据"""
        logger.info("Fetching all required data...")

        # 获取所有股票K线
        klines_dict = db_manager.get_klines_for_ml(
            days=(datetime.strptime(self.end_date, "%Y-%m-%d") - datetime.strptime(self.start_date, "%Y-%m-%d")).days
        )
        all_klines = []
        for code, klines in klines_dict.items():
            df = pd.DataFrame(klines)
            df["code"] = code
            all_klines.append(df)
        self.stock_klines = pd.concat(all_klines, ignore_index=True)
        self.stock_klines["date"] = pd.to_datetime(self.stock_klines["date"])

        # 获取北向行业流向
        north_flow_list = db_manager.get_north_industry_flow(days=365 * 5)  # Fetch 5 years of data
        self.north_flow = pd.DataFrame(north_flow_list)
        self.north_flow["date"] = pd.to_datetime(self.north_flow["date"])

        # 获取沪深300指数作为市场参考
        market_klines = db_manager.get_klines(
            code="sh000300", start_date=self.start_date, end_date=self.end_date, limit=9999
        )
        self.market_index = pd.DataFrame(market_klines)
        if not self.market_index.empty:
            self.market_index["date"] = pd.to_datetime(self.market_index["date"])

        logger.info(
            f"Data fetched. Klines: {len(self.stock_klines)}, North Flow: {len(self.north_flow)}, Market Index: {len(self.market_index)}"
        )

    def build_dataset(self, output_path: str = "sector_ml_dataset.csv"):
        """构建并保存数据集"""
        self._fetch_data()

        if self.stock_klines is None or self.stock_klines.empty:
            logger.error("Stock kline data is empty. Aborting.")
            return

        # A more efficient way to map stocks to sectors
        stock_info_list = [db_manager.get_stock_info(code) for code in self.stock_klines["code"].unique()]
        stock_to_sector = {info["code"]: info["industry"] for info in stock_info_list if info and info.get("industry")}

        self.stock_klines["sector"] = self.stock_klines["code"].map(stock_to_sector)

        # Fallback for stocks not in db_manager.get_stock_info
        unmapped_stocks = self.stock_klines[self.stock_klines["sector"].isna()]["code"].unique()
        if len(unmapped_stocks) > 0:
            # Simplified keyword matching (less efficient but as a fallback)
            # A stock's name is needed for this, which is not in klines.
            # For simplicity, we will drop unmapped stocks for now.
            self.stock_klines = self.stock_klines.dropna(subset=["sector"])

        all_features = []

        trading_dates = sorted(self.stock_klines["date"].unique())

        for date in tqdm(trading_dates, desc="Building dataset"):
            current_date = pd.to_datetime(date)
            if current_date < pd.to_datetime(self.start_date) or current_date > pd.to_datetime(self.end_date):
                continue

            future_date_end = current_date + timedelta(days=self.future_days)

            # Pre-filter data for the current date and future window
            daily_klines = self.stock_klines[self.stock_klines["date"] == current_date]
            future_klines = self.stock_klines[
                (self.stock_klines["date"] > current_date) & (self.stock_klines["date"] <= future_date_end)
            ]

            for sector in SECTOR_MAPPING:
                sector_stocks = daily_klines[daily_klines["sector"] == sector]
                if sector_stocks.empty:
                    continue

                # --- Feature Calculation (X) ---
                # 1. Sector-wide stats
                avg_change = sector_stocks["change_percent"].mean()
                avg_turnover = sector_stocks["turnover_rate"].mean()
                up_count = (sector_stocks["change_percent"] > 0).sum()
                down_count = (sector_stocks["change_percent"] < 0).sum()
                up_ratio = up_count / (up_count + down_count) if (up_count + down_count) > 0 else 0.5
                strength_score = avg_change * 10 + up_ratio * 20 + avg_turnover * 2

                # 2. Northbound Flow
                north_net_inflow = 0
                if self.north_flow is not None:
                    north_flow_today = self.north_flow[
                        (self.north_flow["industry"] == sector) & (self.north_flow["date"] == current_date)
                    ]
                    north_net_inflow = north_flow_today["net_inflow"].iloc[0] if not north_flow_today.empty else 0

                market_change = 0
                if self.market_index is not None:
                    market_today = self.market_index[self.market_index["date"] == current_date]
                    market_change = market_today["change_percent"].iloc[0] if not market_today.empty else 0

                # --- Label Calculation (Y) ---
                future_sector_klines = future_klines[future_klines["sector"] == sector]
                if future_sector_klines.empty:
                    continue

                # Calculate the average return of the sector in the next `future_days`
                # This is a simplified approach. A better one would be to calculate returns for each stock and average them.
                future_return = future_sector_klines.groupby("code")["change_percent"].sum().mean()

                feature_row = {
                    "date": current_date.strftime("%Y-%m-%d"),
                    "sector": sector,
                    "avg_change": avg_change,
                    "avg_turnover": avg_turnover,
                    "up_ratio": up_ratio,
                    "strength_score": strength_score,
                    "north_net_inflow": north_net_inflow,
                    "market_change": market_change,
                    "future_return": future_return,
                }
                all_features.append(feature_row)

        final_df = pd.DataFrame(all_features)
        final_df.to_csv(output_path, index=False)
        logger.info(f"Dataset with {len(final_df)} records saved to {output_path}")


if __name__ == "__main__":
    # Example usage
    builder = SectorDataBuilder(start_date="2023-01-01", end_date="2023-12-31")
    builder.build_dataset()
