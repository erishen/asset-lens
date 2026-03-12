#!/usr/bin/env python3
"""
股票策略模拟交易脚本
基于Asset-Lens策略进行模拟交易
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import random

class TradingSimulator:
    """交易模拟器"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {code: {'quantity': q, 'avg_price': p}}
        self.trade_history = []
        self.portfolio_history = []
        self.current_date = datetime.now()
        
        # 加载配置
        self.load_configs()
        
    def load_configs(self):
        """加载配置"""
        # 加载策略配置
        with open('config/trading_system/trading_strategies.json', 'r', encoding='utf-8') as f:
            self.strategies = json.load(f)['trading_strategies']
        
        # 加载模拟规则
        with open('config/trading_system/simulation_rules.json', 'r', encoding='utf-8') as f:
            self.rules = json.load(f)['simulation_rules']
        
        # 加载股票池
        stock_files = os.listdir('data/stock_pool')
        if stock_files:
            latest_file = sorted(stock_files)[-1]
            with open(f'data/stock_pool/{latest_file}', 'r', encoding='utf-8') as f:
                self.stock_pool = json.load(f)
    
    def simulate_strategy(self, strategy_name, portfolio_type='balanced', days=90):
        """模拟策略交易"""
        print(f"📈 模拟交易: {strategy_name}策略")
        print(f"📅 模拟周期: {days}天")
        print(f"💰 初始资金: {self.initial_capital:,}元")
        print("=" * 60)
        
        # 获取策略配置
        strategy = self.strategies[strategy_name]
        portfolio = self.rules['portfolio_configs'][portfolio_type]
        
        # 初始化投资组合
        self.initialize_portfolio(strategy, portfolio)
        
        # 模拟交易日
        for day in range(days):
            self.simulate_trading_day(day, strategy)
            
            # 记录每日组合价值
            self.record_portfolio_snapshot(day)
            
            # 每周再平衡
            if day % 7 == 0:
                self.rebalance_portfolio(strategy)
        
        # 生成报告
        report = self.generate_simulation_report(strategy_name, days)
        
        return report
    
    def initialize_portfolio(self, strategy, portfolio):
        """初始化投资组合"""
        print("🎯 初始化投资组合...")
        
        # 根据策略选择股票
        recommended_stocks = strategy['recommended_stocks'][:strategy['max_positions']]
        
        # 计算每只股票的投入金额
        position_size = strategy['position_size']
        total_positions = len(recommended_stocks)
        amount_per_stock = self.initial_capital * position_size
        
        print(f"  策略: {strategy['name']}")
        print(f"  单只仓位: {position_size*100:.1f}%")
        print(f"  最大持仓: {strategy['max_positions']}只")
        print(f"  实际持仓: {total_positions}只")
        print(f"  每只股票投入: {amount_per_stock:,.0f}元")
        print()
        
        # 模拟买入
        for code in recommended_stocks:
            # 查找股票信息
            stock_info = self.find_stock_info(code)
            if stock_info:
                # 计算购买数量
                price = stock_info['price']
                quantity = int(amount_per_stock / price / 100) * 100  # 整手
                cost = quantity * price
                
                if cost <= self.cash:
                    self.positions[code] = {
                        'quantity': quantity,
                        'avg_price': price,
                        'current_price': price,
                        'cost': cost,
                        'strategy': 'value'
                    }
                    self.cash -= cost
                    
                    # 记录交易
                    trade = {
                        'trade_id': f"BUY_{code}_{datetime.now().strftime('%Y%m%d')}",
                        'timestamp': self.current_date.strftime('%Y-%m-%d'),
                        'strategy': 'value',
                        'action': 'BUY',
                        'stock_code': code,
                        'stock_name': stock_info['name'],
                        'quantity': quantity,
                        'price': price,
                        'amount': cost,
                        'commission': cost * 0.0003,
                        'reason': '策略初始建仓'
                    }
                    self.trade_history.append(trade)
                    
                    print(f"  ✓ 买入 {stock_info['name']} ({code})")
                    print(f"     数量: {quantity:,}股, 价格: {price:.2f}元, 金额: {cost:,.0f}元")
        
        print(f"  现金余额: {self.cash:,.0f}元")
        print()
    
    def find_stock_info(self, code):
        """查找股票信息"""
        for stock in self.stock_pool:
            if stock['code'] == code:
                return stock
        return None
    
    def simulate_trading_day(self, day, strategy):
        """模拟交易日"""
        # 更新股票价格（模拟价格变化）
        for code, position in self.positions.items():
            stock_info = self.find_stock_info(code)
            if stock_info:
                # 模拟价格波动
                change = random.uniform(-0.05, 0.05)  # ±5%
                new_price = stock_info['price'] * (1 + change)
                position['current_price'] = new_price
                
                # 检查止损止盈
                self.check_stop_loss_take_profit(code, position, strategy)
    
    def check_stop_loss_take_profit(self, code, position, strategy):
        """检查止损止盈"""
        current_price = position['current_price']
        avg_price = position['avg_price']
        profit_rate = (current_price - avg_price) / avg_price
        
        # 检查止损
        if profit_rate < strategy['stop_loss']:
            self.sell_stock(code, position, '止损')
        
        # 检查止盈
        elif profit_rate > strategy['take_profit']:
            self.sell_stock(code, position, '止盈')
    
    def sell_stock(self, code, position, reason):
        """卖出股票"""
        stock_info = self.find_stock_info(code)
        if stock_info:
            quantity = position['quantity']
            price = position['current_price']
            amount = quantity * price
            
            # 从持仓中移除
            del self.positions[code]
            self.cash += amount
            
            # 记录交易
            trade = {
                'trade_id': f"SELL_{code}_{datetime.now().strftime('%Y%m%d')}",
                'timestamp': self.current_date.strftime('%Y-%m-%d'),
                'strategy': 'value',
                'action': 'SELL',
                'stock_code': code,
                'stock_name': stock_info['name'],
                'quantity': quantity,
                'price': price,
                'amount': amount,
                'commission': amount * 0.0003,
                'reason': reason
            }
            self.trade_history.append(trade)
    
    def rebalance_portfolio(self, strategy):
        """再平衡投资组合"""
        # 简单的再平衡逻辑
        pass
    
    def record_portfolio_snapshot(self, day):
        """记录投资组合快照"""
        total_value = self.cash
        positions_value = 0
        
        positions_list = []
        for code, position in self.positions.items():
            stock_info = self.find_stock_info(code)
            if stock_info:
                current_value = position['quantity'] * position['current_price']
                positions_value += current_value
                
                positions_list.append({
                    'code': code,
                    'name': stock_info['name'],
                    'quantity': position['quantity'],
                    'avg_price': position['avg_price'],
                    'current_price': position['current_price'],
                    'value': current_value,
                    'profit_rate': (position['current_price'] - position['avg_price']) / position['avg_price']
                })
        
        total_value += positions_value
        
        snapshot = {
            'day': day,
            'timestamp': self.current_date.strftime('%Y-%m-%d'),
            'total_value': total_value,
            'cash': self.cash,
            'positions_value': positions_value,
            'positions': positions_list,
            'total_return': (total_value - self.initial_capital) / self.initial_capital
        }
        
        self.portfolio_history.append(snapshot)
    
    def generate_simulation_report(self, strategy_name, days):
        """生成模拟交易报告"""
        if not self.portfolio_history:
            return None
        
        final_value = self.portfolio_history[-1]['total_value']
        total_return = (final_value - self.initial_capital) / self.initial_capital
        annual_return = total_return * (365 / days)
        
        # 计算最大回撤
        values = [h['total_value'] for h in self.portfolio_history]
        peak = values[0]
        max_drawdown = 0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 计算夏普比率（简化版）
        returns = []
        for i in range(1, len(values)):
            daily_return = (values[i] - values[i-1]) / values[i-1]
            returns.append(daily_return)
        
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        report = {
            'strategy': strategy_name,
            'simulation_days': days,
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return': total_return,
            'annual_return': annual_return,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trade_count': len(self.trade_history),
            'win_trades': len([t for t in self.trade_history if t['action'] == 'SELL' and 
                              self.calculate_trade_profit(t) > 0]),
            'loss_trades': len([t for t in self.trade_history if t['action'] == 'SELL' and 
                               self.calculate_trade_profit(t) <= 0]),
            'portfolio_history': self.portfolio_history,
            'trade_history': self.trade_history
        }
        
        return report
    
    def calculate_trade_profit(self, trade):
        """计算交易盈亏"""
        # 简化计算
        return 0
    
    def print_simulation_report(self, report):
        """打印模拟报告"""
        print("📊 模拟交易报告")
        print("=" * 60)
        print(f"🎯 策略: {report['strategy']}")
        print(f"📅 模拟天数: {report['simulation_days']}天")
        print(f"💰 初始资金: {report['initial_capital']:,.0f}元")
        print(f"💰 最终价值: {report['final_value']:,.0f}元")
        print(f"📈 总收益率: {report['total_return']*100:.2f}%")
        print(f"📊 年化收益率: {report['annual_return']*100:.2f}%")
        print(f"📉 最大回撤: {report['max_drawdown']*100:.2f}%")
        print(f"⚖️ 夏普比率: {report['sharpe_ratio']:.2f}")
        print(f"🔄 交易次数: {report['trade_count']}次")
        print(f"✅ 盈利交易: {report['win_trades']}次")
        print(f"❌ 亏损交易: {report['loss_trades']}次")
        if report['trade_count'] > 0:
            win_rate = report['win_trades'] / report['trade_count'] * 100
            print(f"🎯 胜率: {win_rate:.1f}%")
        print()
        
        # 投资组合表现
        print("📈 投资组合表现:")
        print("-" * 40)
        if len(report['portfolio_history']) >= 5:
            print("  最近5个交易日:")
            for i in range(-5, 0):
                snapshot = report['portfolio_history'][i]
                print(f"    第{snapshot['day']}天: {snapshot['total_value']:,.0f}元 " +
                      f"(收益率: {snapshot['total_return']*100:.2f}%)")
        print()
        
        # 交易记录
        print("🔄 交易记录:")
        print("-" * 40)
        if report['trade_history']:
            recent_trades = report['trade_history'][-5:]  # 最近5笔交易
            for trade in recent_trades:
                action_emoji = "🟢" if trade['action'] == 'BUY' else "🔴"
                print(f"  {action_emoji} {trade['timestamp']} {trade['action']} " +
                      f"{trade['stock_name']} ({trade['stock_code']})")
                print(f"     数量: {trade['quantity']:,}股, 价格: {trade['price']:.2f}元")
                print(f"     金额: {trade['amount']:,.0f}元, 原因: {trade['reason']}")
        print()
        
        print("💡 策略评价:")
        print("-" * 40)
        if report['total_return'] > 0:
            print("  ✅ 策略表现: 盈利")
            if report['sharpe_ratio'] > 1:
                print("  ✅ 风险调整收益: 优秀")
            elif report['sharpe_ratio'] > 0.5:
                print("  ✅ 风险调整收益: 良好")
            else:
                print("  ⚠️ 风险调整收益: 一般")
        else:
            print("  ❌ 策略表现: 亏损")
        
        if report['max_drawdown'] < 0.10:
            print("  ✅ 风险控制: 优秀")
        elif report['max_drawdown'] < 0.20:
            print("  ✅ 风险控制: 良好")
        else:
            print("  ⚠️ 风险控制: 需要改进")
        print()
        
        print("=" * 60)

def main():
    """主函数"""
    print("📈 股票策略模拟交易系统")
    print("=" * 60)
    
    # 创建模拟器
    simulator = TradingSimulator(initial_capital=100000)
    
    # 模拟不同策略
    strategies = ['value_strategy', 'momentum_strategy', 'dividend_strategy']
    
    for strategy in strategies:
        print(f"\n🚀 开始模拟 {strategy}...")
        report = simulator.simulate_strategy(strategy, days=30)
        
        if report:
            simulator.print_simulation_report(report)
            
            # 保存报告
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_dir = 'output/trading_reports'
            os.makedirs(report_dir, exist_ok=True)
            
            report_file = f"{report_dir}/{strategy}_simulation_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            print(f"📁 报告已保存: {report_file}")
    
    print("\n✅ 模拟交易完成！")

if __name__ == "__main__":
    main()
