#!/usr/bin/env python
"""
Fundamental Data Updater.
基本面数据定时更新脚本

功能:
1. 定期更新所有股票的基本面数据
2. 增量更新资金流向数据
3. 支持全量更新和增量更新
4. 自动清理过期缓存

使用:
    python update_fundamental_data.py --mode full     # 全量更新
    python update_fundamental_data.py --mode incremental  # 增量更新
    python update_fundamental_data.py --mode daily    # 每日更新
"""
import warnings

warnings.filterwarnings("ignore", message="Pandas requires version")
warnings.filterwarnings("ignore", message=".*unclosed.*socket.*")
warnings.filterwarnings("ignore", category=ResourceWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

from asset_lens.data.fundamental_fetcher import (
    FundamentalFetcher,
    MoneyFlowFetcher,
    EnhancedFeatureBuilder,
)
from asset_lens.db.database import db_manager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FundamentalDataUpdater:
    """基本面数据更新器"""
    
    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path(__file__).parent.parent / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.fundamental_fetcher = FundamentalFetcher(cache_path=self.cache_dir)
        self.money_flow_fetcher = MoneyFlowFetcher(cache_path=self.cache_dir)
        self.feature_builder = EnhancedFeatureBuilder()
        
        self.status_file = self.cache_dir / "update_status.json"
        self._load_status()
    
    def _load_status(self):
        """加载更新状态"""
        self.status: dict[str, str | int | None] = {
            'last_full_update': None,
            'last_incremental_update': None,
            'last_daily_update': None,
            'total_stocks': 0,
            'updated_stocks': 0,
        }
        
        if self.status_file.exists():
            try:
                with open(self.status_file, encoding='utf-8') as f:
                    self.status.update(json.load(f))
            except Exception as e:
                logger.warning(f"加载状态文件失败: {e}")
    
    def _save_status(self):
        """保存更新状态"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, default=str)
    
    def get_all_stock_codes(self) -> list[str]:
        """获取所有股票代码"""
        try:
            codes = db_manager.get_stock_codes()
            logger.info(f"获取到 {len(codes)} 只股票代码")
            return codes
        except Exception as e:
            logger.error(f"获取股票代码失败: {e}")
            return []
    
    def update_fundamentals_full(self, codes: list[str] | None = None):
        """全量更新基本面数据"""
        logger.info("=" * 50)
        logger.info("开始全量更新基本面数据")
        logger.info("=" * 50)
        
        if codes is None:
            codes = self.get_all_stock_codes()
        
        if not codes:
            logger.warning("没有股票代码需要更新")
            return
        
        total = len(codes)
        updated = 0
        failed = 0
        
        for i, code in enumerate(codes):
            try:
                self.fundamental_fetcher.get_fundamental(code)
                updated += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i + 1}/{total} ({(i+1)/total*100:.1f}%)")
                    self.fundamental_fetcher._save_cache()
                    
            except Exception as e:
                failed += 1
                logger.debug(f"更新 {code} 失败: {e}")
        
        self.fundamental_fetcher._save_cache()
        
        self.status['last_full_update'] = datetime.now().isoformat()
        self.status['total_stocks'] = total
        self.status['updated_stocks'] = updated
        self._save_status()
        
        logger.info(f"全量更新完成: 成功 {updated}, 失败 {failed}")
    
    def update_money_flow_daily(self, codes: list[str] | None = None, days: int = 30):
        """每日更新资金流向数据"""
        logger.info("=" * 50)
        logger.info("开始更新资金流向数据")
        logger.info("=" * 50)
        
        if codes is None:
            codes = self.get_all_stock_codes()
        
        if not codes:
            logger.warning("没有股票代码需要更新")
            return
        
        total = len(codes)
        updated = 0
        
        for i, code in enumerate(codes):
            try:
                self.money_flow_fetcher.get_money_flow(code, days=days)
                updated += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f"进度: {i + 1}/{total} ({(i+1)/total*100:.1f}%)")
                    
            except Exception as e:
                logger.debug(f"更新 {code} 资金流向失败: {e}")
        
        self.money_flow_fetcher._save_cache()
        
        self.status['last_daily_update'] = datetime.now().isoformat()
        self._save_status()
        
        logger.info(f"资金流向更新完成: 成功 {updated}/{total}")
    
    def update_incremental(self, codes: list[str] | None = None):
        """增量更新 - 只更新变化的数据"""
        logger.info("=" * 50)
        logger.info("开始增量更新")
        logger.info("=" * 50)
        
        if codes is None:
            codes = self.get_all_stock_codes()
        
        last_update = self.status.get('last_incremental_update')
        if last_update and isinstance(last_update, str):
            last_update_dt = datetime.fromisoformat(last_update)
            logger.info(f"上次更新时间: {last_update_dt}")
        
        self.update_money_flow_daily(codes, days=5)
        
        self.status['last_incremental_update'] = datetime.now().isoformat()
        self._save_status()
        
        logger.info("增量更新完成")
    
    def cleanup_old_cache(self, days: int = 30):
        """清理过期缓存"""
        logger.info(f"清理 {days} 天前的缓存...")
        
        cutoff = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if mtime < cutoff:
                    cache_file.unlink()
                    cleaned += 1
            except Exception as e:
                logger.debug(f"清理 {cache_file} 失败: {e}")
        
        logger.info(f"清理完成: 删除 {cleaned} 个过期缓存文件")
    
    def get_update_summary(self) -> dict:
        """获取更新摘要"""
        return {
            'last_full_update': self.status.get('last_full_update'),
            'last_incremental_update': self.status.get('last_incremental_update'),
            'last_daily_update': self.status.get('last_daily_update'),
            'total_stocks': self.status.get('total_stocks', 0),
            'updated_stocks': self.status.get('updated_stocks', 0),
            'cache_dir': str(self.cache_dir),
        }


def main():
    parser = argparse.ArgumentParser(description='基本面数据更新工具')
    parser.add_argument(
        '--mode',
        choices=['full', 'incremental', 'daily', 'status', 'cleanup'],
        default='daily',
        help='更新模式: full=全量更新, incremental=增量更新, daily=每日更新, status=查看状态, cleanup=清理缓存'
    )
    parser.add_argument(
        '--codes',
        nargs='+',
        help='指定股票代码列表 (可选)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='更新天数 (默认30天)'
    )
    parser.add_argument(
        '--cache-dir',
        type=str,
        help='缓存目录'
    )
    
    args = parser.parse_args()
    
    cache_dir = Path(args.cache_dir) if args.cache_dir else None
    updater = FundamentalDataUpdater(cache_dir=cache_dir)
    
    codes = args.codes
    
    if args.mode == 'full':
        updater.update_fundamentals_full(codes)
        updater.update_money_flow_daily(codes, days=args.days)
        
    elif args.mode == 'incremental':
        updater.update_incremental(codes)
        
    elif args.mode == 'daily':
        updater.update_money_flow_daily(codes, days=args.days)
        
    elif args.mode == 'status':
        summary = updater.get_update_summary()
        print("\n📊 基本面数据更新状态:")
        print("-" * 40)
        for key, value in summary.items():
            print(f"  {key}: {value}")
            
    elif args.mode == 'cleanup':
        updater.cleanup_old_cache(days=args.days)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
