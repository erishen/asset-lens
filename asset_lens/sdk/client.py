"""
Asset-Lens Python SDK.
方便的 Python 调用接口
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class AssetLensClient:
    """Asset-Lens 客户端"""
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        初始化客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path or Path("config/asset_lens.yaml")
        self._cache: Dict[str, Any] = {}
    
    def get_stock_quote(self, code: str) -> Dict[str, Any]:
        """
        获取股票实时行情
        
        Args:
            code: 股票代码（如 sh600519, sz000001）
            
        Returns:
            股票行情数据
        """
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'asset_lens', 'fetch-stock', code],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'data': result.stdout,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"获取股票行情失败: {code}, {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_fund_nav(self, code: str) -> Dict[str, Any]:
        """
        获取基金净值
        
        Args:
            code: 基金代码
            
        Returns:
            基金净值数据
        """
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'asset_lens', 'fetch-fund', code],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'data': result.stdout,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"获取基金净值失败: {code}, {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def analyze_portfolio(self) -> Dict[str, Any]:
        """
        分析投资组合
        
        Returns:
            投资组合分析数据
        """
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'asset_lens', 'analyze'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'data': result.stdout,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"分析投资组合失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def screen_stocks(self, strategy: str = "momentum", limit: int = 10) -> Dict[str, Any]:
        """
        股票筛选
        
        Args:
            strategy: 策略类型（momentum, value, reversal, dividend）
            limit: 返回数量
            
        Returns:
            筛选结果
        """
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'asset_lens', 'strategy-screen', 'NAME', strategy],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'data': result.stdout,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"股票筛选失败: {strategy}, {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_market_indices(self) -> Dict[str, Any]:
        """
        获取市场指数
        
        Returns:
            市场指数数据
        """
        try:
            indices = {
                'sh000300': '沪深300',
                'sh000016': '上证50',
                'sz399006': '创业板指',
                'sh000688': '科创50'
            }
            
            results = {}
            for code, name in indices.items():
                result = self.get_stock_quote(code)
                if result['success']:
                    results[name] = result
            
            return {
                'success': True,
                'data': results,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"获取市场指数失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def calculate_risk_metrics(self, returns: List[float]) -> Dict[str, Any]:
        """
        计算风险指标
        
        Args:
            returns: 收益率序列
            
        Returns:
            风险指标数据
        """
        try:
            from asset_lens.monitoring.risk_analyzer import RiskAnalyzer
            
            risk_analyzer = RiskAnalyzer()
            metrics = risk_analyzer.calculate_all_metrics(returns)
            
            return {
                'success': True,
                'data': {
                    'volatility': metrics.volatility,
                    'max_drawdown': metrics.max_drawdown,
                    'sharpe_ratio': metrics.sharpe_ratio,
                    'var_95': metrics.var_95
                },
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def generate_report(self, report_type: str = "daily") -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            report_type: 报告类型（daily, weekly, monthly）
            
        Returns:
            报告数据
        """
        try:
            from asset_lens.monitoring.investment_monitor import InvestmentMonitor
            
            monitor = InvestmentMonitor()
            
            if report_type == "daily":
                report = monitor.generate_daily_report()
            elif report_type == "weekly":
                report = monitor.generate_weekly_report()
            else:
                report = monitor.generate_daily_report()
            
            return {
                'success': True,
                'data': report,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"生成报告失败: {report_type}, {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def add_to_stock_pool(self, code: str, name: str, price: float) -> Dict[str, Any]:
        """
        添加股票到股票池
        
        Args:
            code: 股票代码
            name: 股票名称
            price: 买入价格
            
        Returns:
            操作结果
        """
        try:
            import subprocess
            result = subprocess.run(
                ['asset-lens', 'stock-pool', 'add', '--code', code, '--name', name, '--price', str(price)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': f"股票 {code} 已添加到股票池",
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"添加股票到股票池失败: {code}, {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    
    def get_stock_pool_status(self) -> Dict[str, Any]:
        """
        获取股票池状态
        
        Returns:
            股票池状态数据
        """
        try:
            import subprocess
            result = subprocess.run(
                ['python', '-m', 'asset_lens', 'stock-pool-status'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'data': result.stdout,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr,
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
        except Exception as e:
            logger.error(f"获取股票池状态失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }


def create_client(config_path: Optional[Path] = None) -> AssetLensClient:
    """创建客户端实例"""
    return AssetLensClient(config_path)
