"""
Stock tracker for asset-lens.
股票跟踪监控模块 - 追踪股票池表现，识别妖股

功能:
1. 每日跟踪 - 记录股票池中股票的每日表现
2. 妖股识别 - 识别连续涨停、大幅上涨等妖股特征
3. 预警系统 - 设置预警条件，触发时提醒
4. 跟踪报告 - 生成跟踪分析报告
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..config import config
from ..trading.stock_pool import StockPool


@dataclass
class DailyRecord:
    """每日记录"""

    date: str
    code: str
    name: str
    open_price: float
    close_price: float
    high_price: float
    low_price: float
    change_percent: float
    turnover_rate: float
    volume: float
    amount: float


@dataclass
class MonsterStockSignal:
    """妖股信号"""

    code: str
    name: str
    signal_type: str
    signal_date: str
    description: str
    score: float
    details: dict[str, Any]


@dataclass
class TrackerConfig:
    """跟踪器配置"""

    limit_up_threshold: float = 9.5
    limit_down_threshold: float = -9.5
    consecutive_days: int = 3
    volume_surge_ratio: float = 2.0
    turnover_surge_ratio: float = 2.0
    monster_score_threshold: float = 70.0


class StockTracker:
    """股票跟踪器"""

    def __init__(self, pool_name: str = "default"):
        self.pool_name = pool_name
        self.tracker_path = config.cache_path / "stock_tracker"
        self.tracker_path.mkdir(parents=True, exist_ok=True)
        self.tracker_file = self.tracker_path / f"{pool_name}_tracker.json"
        self.stock_pool = StockPool(pool_name)
        self.config = TrackerConfig()
        self.daily_records: dict[str, list[DailyRecord]] = {}
        self.monster_signals: list[MonsterStockSignal] = []
        self._load_tracker()

    def _load_tracker(self) -> None:
        """加载跟踪数据"""
        if self.tracker_file.exists():
            try:
                with open(self.tracker_file, encoding="utf-8") as f:
                    data = json.load(f)

                for code, records in data.get("daily_records", {}).items():
                    self.daily_records[code] = [
                        DailyRecord(
                            date=r.get("date", ""),
                            code=r.get("code", ""),
                            name=r.get("name", ""),
                            open_price=r.get("open_price", 0),
                            close_price=r.get("close_price", 0),
                            high_price=r.get("high_price", 0),
                            low_price=r.get("low_price", 0),
                            change_percent=r.get("change_percent", 0),
                            turnover_rate=r.get("turnover_rate", 0),
                            volume=r.get("volume", 0),
                            amount=r.get("amount", 0),
                        )
                        for r in records
                    ]

                self.monster_signals = [
                    MonsterStockSignal(
                        code=s.get("code", ""),
                        name=s.get("name", ""),
                        signal_type=s.get("signal_type", ""),
                        signal_date=s.get("signal_date", ""),
                        description=s.get("description", ""),
                        score=s.get("score", 0),
                        details=s.get("details", {}),
                    )
                    for s in data.get("monster_signals", [])
                ]

            except Exception as e:
                print(f"加载跟踪数据失败: {e}")

    def _save_tracker(self) -> None:
        """保存跟踪数据"""
        data = {
            "pool_name": self.pool_name,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "daily_records": {
                code: [
                    {
                        "date": r.date,
                        "code": r.code,
                        "name": r.name,
                        "open_price": r.open_price,
                        "close_price": r.close_price,
                        "high_price": r.high_price,
                        "low_price": r.low_price,
                        "change_percent": r.change_percent,
                        "turnover_rate": r.turnover_rate,
                        "volume": r.volume,
                        "amount": r.amount,
                    }
                    for r in records
                ]
                for code, records in self.daily_records.items()
            },
            "monster_signals": [
                {
                    "code": s.code,
                    "name": s.name,
                    "signal_type": s.signal_type,
                    "signal_date": s.signal_date,
                    "description": s.description,
                    "score": s.score,
                    "details": s.details,
                }
                for s in self.monster_signals
            ],
        }

        with open(self.tracker_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def record_daily(self, stock_data: dict[str, Any]) -> bool:
        """
        记录每日数据

        Args:
            stock_data: 股票数据字典，包含 code, name, open, close, high, low, change_percent 等

        Returns:
            是否成功记录（True=新增，False=跳过）
        """
        code = stock_data.get("code", "")
        if not code:
            return False

        today = datetime.now().strftime("%Y-%m-%d")

        record = DailyRecord(
            date=today,
            code=code,
            name=stock_data.get("name", ""),
            open_price=stock_data.get("open", stock_data.get("current_price", 0)),
            close_price=stock_data.get("close", stock_data.get("current_price", 0)),
            high_price=stock_data.get("high", stock_data.get("current_price", 0)),
            low_price=stock_data.get("low", stock_data.get("current_price", 0)),
            change_percent=stock_data.get("change_percent", 0),
            turnover_rate=stock_data.get("turnover_rate", 0),
            volume=stock_data.get("volume", 0),
            amount=stock_data.get("amount", 0),
        )

        if code not in self.daily_records:
            self.daily_records[code] = []

        # 检查是否已存在同一天的记录，避免重复
        existing_dates = {r.date for r in self.daily_records[code]}
        if today not in existing_dates:
            self.daily_records[code].append(record)
            self._save_tracker()
            return True

        return False

    def record_batch(self, stocks_data: list[dict[str, Any]]) -> int:
        """
        批量记录每日数据

        Args:
            stocks_data: 股票数据列表

        Returns:
            记录数量
        """
        count = 0
        for stock in stocks_data:
            if stock.get("code") in self.stock_pool.positions and self.record_daily(stock):
                count += 1

        self._save_tracker()
        return count

    def detect_monster_stocks(self, code: str | None = None) -> list[MonsterStockSignal]:
        """
        检测妖股信号

        Args:
            code: 指定股票代码，None则检测所有

        Returns:
            妖股信号列表
        """
        signals = []
        codes = [code] if code else list(self.daily_records.keys())

        for c in codes:
            records = self.daily_records.get(c, [])
            if len(records) < 2:
                continue

            records.sort(key=lambda x: x.date, reverse=True)
            recent_records = records[:10]

            signal = self._analyze_monster_signals(c, recent_records)
            if signal:
                signals.append(signal)
                self.monster_signals.append(signal)

        signals.sort(key=lambda x: x.score, reverse=True)
        self._save_tracker()
        return signals

    def _analyze_monster_signals(self, code: str, records: list[DailyRecord]) -> MonsterStockSignal | None:
        """分析妖股信号"""
        if not records:
            return None

        score: int = 0
        signal_types: list[str] = []
        details: dict[str, Any] = {}

        name = records[0].name

        consecutive_up = self._check_consecutive_limit_up(records)
        if consecutive_up > 0:
            score += consecutive_up * 30
            signal_types.append(f"连续{consecutive_up}涨停")
            details["consecutive_limit_up"] = consecutive_up

        max_gain = self._check_max_gain(records)
        if max_gain >= 20:
            score += 25
            signal_types.append(f"最大涨幅{max_gain:.1f}%")
            details["max_gain"] = max_gain
        elif max_gain >= 10:
            score += 15
            signal_types.append(f"涨幅{max_gain:.1f}%")
            details["max_gain"] = max_gain
        elif max_gain >= 5:
            score += 5

        volume_surge = self._check_volume_surge(records)
        if volume_surge:
            score += 20
            signal_types.append("放量突破")
            details["volume_surge"] = volume_surge

        turnover_surge = self._check_turnover_surge(records)
        if turnover_surge:
            score += 15
            signal_types.append("换手率放大")
            details["turnover_surge"] = turnover_surge

        trend_strength = self._check_trend_strength(records)
        if trend_strength >= 3:
            score += 10
            signal_types.append(f"强势{trend_strength}天")
            details["trend_strength"] = trend_strength

        acceleration = self._check_price_acceleration(records)
        if acceleration:
            score += 15
            signal_types.append("加速上涨")
            details["acceleration"] = acceleration

        new_high = self._check_new_high(records)
        if new_high:
            score += 12
            signal_types.append("创新高")
            details["new_high"] = new_high

        gap_up = self._check_gap_up(records)
        if gap_up:
            score += 10
            signal_types.append("跳空高开")
            details["gap_up"] = gap_up

        volatility_breakout = self._check_volatility_breakout(records)
        if volatility_breakout:
            score += 8
            signal_types.append("波动突破")
            details["volatility_breakout"] = volatility_breakout

        if score < self.config.monster_score_threshold:
            return None

        return MonsterStockSignal(
            code=code,
            name=name,
            signal_type="|".join(signal_types),
            signal_date=datetime.now().strftime("%Y-%m-%d"),
            description=f"妖股信号: {', '.join(signal_types)}",
            score=score,
            details=details,
        )

    def _check_consecutive_limit_up(self, records: list[DailyRecord]) -> int:
        """检查连续涨停"""
        count = 0
        for r in records:
            if r.change_percent >= self.config.limit_up_threshold:
                count += 1
            else:
                break
        return count

    def _check_max_gain(self, records: list[DailyRecord]) -> float:
        """检查最大涨幅"""
        if not records:
            return 0.0

        recent = records[:5]
        total_gain: float = 0.0
        for r in recent:
            total_gain += r.change_percent
        return total_gain

    def _check_volume_surge(self, records: list[DailyRecord]) -> float | None:
        """检查成交量放大"""
        if len(records) < 5:
            return None

        recent_volume = records[0].volume
        avg_volume = sum(r.volume for r in records[1:5]) / 4

        if avg_volume > 0 and recent_volume / avg_volume >= self.config.volume_surge_ratio:
            return recent_volume / avg_volume
        return None

    def _check_turnover_surge(self, records: list[DailyRecord]) -> float | None:
        """检查换手率放大"""
        if len(records) < 5:
            return None

        recent_turnover = records[0].turnover_rate
        avg_turnover = sum(r.turnover_rate for r in records[1:5]) / 4

        if avg_turnover > 0 and recent_turnover / avg_turnover >= self.config.turnover_surge_ratio:
            return recent_turnover / avg_turnover
        return None

    def _check_trend_strength(self, records: list[DailyRecord]) -> int:
        """检查趋势强度"""
        count = 0
        for r in records:
            if r.change_percent > 0:
                count += 1
            else:
                break
        return count

    def _check_price_acceleration(self, records: list[DailyRecord]) -> float | None:
        """检查价格加速上涨"""
        if len(records) < 3:
            return None

        changes = [r.change_percent for r in records[:3]]
        if all(c > 0 for c in changes) and changes[0] > changes[1] > changes[2]:
            return changes[0] - changes[2]
        return None

    def _check_new_high(self, records: list[DailyRecord]) -> float | None:
        """检查创新高"""
        if len(records) < 5:
            return None

        current_high = records[0].high_price
        prev_highs = [r.high_price for r in records[1:5]]

        if prev_highs and current_high > max(prev_highs):
            return current_high - max(prev_highs)
        return None

    def _check_gap_up(self, records: list[DailyRecord]) -> float | None:
        """检查跳空高开"""
        if len(records) < 2:
            return None

        current_open = records[0].open_price
        prev_close = records[1].close_price

        if prev_close > 0:
            gap_pct = ((current_open - prev_close) / prev_close) * 100
            if gap_pct >= 2:
                return gap_pct
        return None

    def _check_volatility_breakout(self, records: list[DailyRecord]) -> float | None:
        """检查波动突破"""
        if len(records) < 5:
            return None

        current_range = records[0].high_price - records[0].low_price
        avg_range = sum(r.high_price - r.low_price for r in records[1:5]) / 4

        if avg_range > 0 and current_range / avg_range >= 1.5:
            return current_range / avg_range
        return None

    def get_tracking_report(self) -> dict[str, Any]:
        """
        生成跟踪报告

        Returns:
            跟踪报告
        """
        pool_status = self.stock_pool.get_performance()

        watching_stocks = self.stock_pool.list_stocks("watching")
        holding_stocks = self.stock_pool.list_stocks("holding")
        sold_stocks = self.stock_pool.list_stocks("sold")

        recent_monsters = [
            s for s in self.monster_signals if (datetime.now() - datetime.strptime(s.signal_date, "%Y-%m-%d")).days <= 7
        ]

        return {
            "pool_name": self.pool_name,
            "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pool_status": pool_status,
            "watching_count": len(watching_stocks),
            "holding_count": len(holding_stocks),
            "sold_count": len(sold_stocks),
            "tracked_days": max((len(records) for records in self.daily_records.values()), default=0),
            "monster_signals_count": len(self.monster_signals),
            "recent_monsters": [
                {
                    "code": s.code,
                    "name": s.name,
                    "signal_type": s.signal_type,
                    "signal_date": s.signal_date,
                    "score": s.score,
                    "description": s.description,
                }
                for s in recent_monsters
            ],
            "best_performers": self.stock_pool.get_best_performers(5),
            "worst_performers": self.stock_pool.get_worst_performers(5),
        }

    def print_tracking_report(self) -> None:
        """打印跟踪报告"""
        report = self.get_tracking_report()

        print("\n" + "=" * 60)
        print(f"📊 股票跟踪报告 - {report['pool_name']}")
        print("=" * 60)
        print(f"更新时间: {report['update_time']}")
        print(f"跟踪天数: {report['tracked_days']} 天")

        print("\n" + "-" * 60)
        print("📈 股票池状态")
        print("-" * 60)
        print(f"观察中: {report['watching_count']} 只")
        print(f"持有中: {report['holding_count']} 只")
        print(f"已卖出: {report['sold_count']} 只")

        if report.get("recent_monsters"):
            print("\n" + "-" * 60)
            print("🔥 近期妖股信号")
            print("-" * 60)
            for s in report["recent_monsters"]:
                print(f"  {s['name']}({s['code']})")
                print(f"    信号: {s['signal_type']}")
                print(f"    得分: {s['score']:.0f}")
                print(f"    日期: {s['signal_date']}")

        if report.get("best_performers"):
            print("\n" + "-" * 60)
            print("🏆 表现最佳")
            print("-" * 60)
            for i, s in enumerate(report["best_performers"], 1):
                print(f"  {i}. {s['name']}({s['code']}): {s['profit_rate']:+.2f}%")

        if report.get("worst_performers"):
            print("\n" + "-" * 60)
            print("⚠️ 表现最差")
            print("-" * 60)
            for i, s in enumerate(report["worst_performers"], 1):
                print(f"  {i}. {s['name']}({s['code']}): {s['profit_rate']:+.2f}%")

        print("\n" + "=" * 60)


stock_tracker = StockTracker()
