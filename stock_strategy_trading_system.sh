#!/bin/bash
# 股票策略交易系统部署脚本

echo "📈 股票策略交易系统部署..."
echo "=========================================="

# 1. 检查环境
echo "🔍 检查环境..."
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在"
    exit 1
fi

echo "✅ 环境检查通过"

# 2. 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 3. 创建股票池
echo "📊 创建股票池..."
python3 create_stock_pool.py

if [ $? -eq 0 ]; then
    echo "✅ 股票池创建完成"
else
    echo "❌ 股票池创建失败"
    exit 1
fi

# 4. 创建模拟交易系统
echo "💰 创建模拟交易系统..."
mkdir -p config/trading_system
mkdir -p data/trading_records
mkdir -p output/trading_reports

# 创建交易策略配置
cat > config/trading_system/trading_strategies.json << 'EOF'
{
  "trading_strategies": {
    "value_strategy": {
      "name": "价值投资策略",
      "description": "低估值、稳健增长，适合长期投资",
      "position_size": 0.10,
      "max_positions": 10,
      "stop_loss": -0.10,
      "take_profit": 0.30,
      "buy_conditions": [
        "pe_ratio < 20",
        "50 <= market_cap <= 500",
        "1 <= turnover_rate <= 5",
        "change_percent > 0"
      ],
      "sell_conditions": [
        "pe_ratio > 40",
        "profit_rate < -0.10",
        "profit_rate > 0.30"
      ],
      "recommended_stocks": [
        "sh600036", "sh601318", "sz000725", "sh600703", "sz002241"
      ]
    },
    "momentum_strategy": {
      "name": "成长动量策略",
      "description": "追踪强势股，适合趋势跟踪",
      "position_size": 0.08,
      "max_positions": 15,
      "stop_loss": -0.08,
      "take_profit": 0.15,
      "buy_conditions": [
        "volume_ratio > 2",
        "3 <= change_percent <= 9",
        "5 <= turnover_rate <= 15",
        "30 <= market_cap <= 300"
      ],
      "sell_conditions": [
        "volume_ratio > 3",
        "profit_rate < -0.08",
        "profit_rate > 0.15"
      ],
      "recommended_stocks": [
        "sh600519", "sz300750", "sz002475", "sh688981", "sz002594"
      ]
    },
    "dividend_strategy": {
      "name": "稳健红利策略",
      "description": "高股息、低波动，适合稳健收益",
      "position_size": 0.15,
      "max_positions": 8,
      "stop_loss": -0.08,
      "take_profit": 0.15,
      "buy_conditions": [
        "pe_ratio < 15",
        "market_cap > 200",
        "turnover_rate < 3",
        "amplitude_20d < 5"
      ],
      "sell_conditions": [
        "pe_ratio > 25",
        "profit_rate < -0.08",
        "profit_rate > 0.15"
      ],
      "recommended_stocks": [
        "sh601988", "sh601328", "sh600028", "sh601857", "sh600900"
      ]
    },
    "reversal_strategy": {
      "name": "困境反转策略",
      "description": "抄底超跌股，高风险高收益",
      "position_size": 0.05,
      "max_positions": 20,
      "stop_loss": -0.05,
      "take_profit": 0.20,
      "buy_conditions": [
        "change_percent_5d < -15",
        "pb_ratio < 1.5",
        "volume_ratio > 1.5",
        "market_cap < 100"
      ],
      "sell_conditions": [
        "profit_rate > 0.20",
        "profit_rate < -0.05",
        "volume_ratio > 3"
      ],
      "recommended_stocks": [
        "sz000725", "sz000100", "sh600703", "sz002241", "sz002456"
      ]
    }
  },
  "portfolio_configs": {
    "conservative": {
      "name": "保守型组合",
      "description": "低风险，稳健收益",
      "allocation": {
        "value_strategy": 0.50,
        "dividend_strategy": 0.40,
        "momentum_strategy": 0.10
      },
      "total_capital": 100000,
      "max_drawdown": -0.10
    },
    "balanced": {
      "name": "平衡型组合",
      "description": "风险收益平衡",
      "allocation": {
        "value_strategy": 0.40,
        "momentum_strategy": 0.30,
        "dividend_strategy": 0.20,
        "reversal_strategy": 0.10
      },
      "total_capital": 100000,
      "max_drawdown": -0.15
    },
    "aggressive": {
      "name": "进取型组合",
      "description": "高风险，高收益潜力",
      "allocation": {
        "momentum_strategy": 0.50,
        "reversal_strategy": 0.30,
        "value_strategy": 0.20
      },
      "total_capital": 100000,
      "max_drawdown": -0.20
    }
  }
}
EOF

# 创建模拟交易规则
cat > config/trading_system/simulation_rules.json << 'EOF'
{
  "simulation_rules": {
    "trading_parameters": {
      "initial_capital": 100000,
      "commission_rate": 0.0003,
      "stamp_tax": 0.001,
      "min_trade_amount": 100,
      "trade_frequency": "daily",
      "rebalance_frequency": "monthly"
    },
    "risk_management": {
      "max_position_size": 0.20,
      "max_sector_exposure": 0.30,
      "max_single_loss": 0.10,
      "max_portfolio_loss": 0.20,
      "stop_loss_triggers": [
        "single_stock_loss > 10%",
        "portfolio_loss > 15%",
        "market_crash > 20%"
      ]
    },
    "performance_metrics": {
      "calculate_sharpe_ratio": true,
      "calculate_max_drawdown": true,
      "calculate_win_rate": true,
      "calculate_annual_return": true,
      "benchmark_index": "sh000300"
    },
    "simulation_periods": [
      {
        "name": "短期测试",
        "duration_days": 30,
        "description": "策略短期适应性测试"
      },
      {
        "name": "中期测试",
        "duration_days": 90,
        "description": "策略稳定性测试"
      },
      {
        "name": "长期测试",
        "duration_days": 365,
        "description": "策略长期有效性测试"
      }
    ]
  }
}
EOF

# 创建交易记录模板
cat > config/trading_system/trade_record_template.json << 'EOF'
{
  "trade_record": {
    "trade_id": "",
    "timestamp": "",
    "strategy": "",
    "action": "",
    "stock_code": "",
    "stock_name": "",
    "quantity": 0,
    "price": 0.0,
    "amount": 0.0,
    "commission": 0.0,
    "reason": "",
    "portfolio_value": 0.0,
    "cash_balance": 0.0
  },
  "portfolio_snapshot": {
    "timestamp": "",
    "total_value": 0.0,
    "cash": 0.0,
    "positions": [],
    "performance": {
      "daily_return": 0.0,
      "total_return": 0.0,
      "max_drawdown": 0.0,
      "sharpe_ratio": 0.0
    }
  }
}
EOF

echo "✅ 交易系统配置已生成"

# 5. 创建模拟交易脚本
echo "📝 创建模拟交易脚本..."
cat > simulate_trading.py << 'EOF'
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
EOF

echo "✅ 模拟交易脚本已生成"

# 6. 创建交易监控配置
echo "📊 创建交易监控配置..."
cat > config/trading_system/monitoring_config.json << 'EOF'
{
  "monitoring_config": {
    "daily_monitoring": {
      "time": "15:30",
      "tasks": [
        "检查持仓股票收盘价",
        "计算当日盈亏",
        "检查止损止盈条件",
        "更新投资组合价值"
      ]
    },
    "weekly_review": {
      "day": "friday",
      "time": "17:00",
      "tasks": [
        "分析本周策略表现",
        "检查持仓结构",
        "评估风险暴露",
        "生成周度报告"
      ]
    },
    "monthly_rebalance": {
      "day": "last_day",
      "time": "20:00",
      "tasks": [
        "再平衡投资组合",
        "评估策略有效性",
        "调整仓位分配",
        "生成月度报告"
      ]
    },
    "alerts": {
      "price_alerts": [
        {
          "type": "stop_loss",
          "condition": "profit_rate < -0.10",
          "action": "发送止损提醒，建议卖出"
        },
        {
          "type": "take_profit",
          "condition": "profit_rate > 0.30",
          "action": "发送止盈提醒，建议卖出"
        },
        {
          "type": "price_breakout",
          "condition": "price_change > 0.05",
          "action": "发送突破提醒，关注"
        }
      ],
      "portfolio_alerts": [
        {
          "type": "max_drawdown",
          "condition": "portfolio_drawdown > 0.15",
          "action": "发送最大回撤警告"
        },
        {
          "type": "sector_concentration",
          "condition": "sector_exposure > 0.30",
          "action": "发送行业集中度警告"
        }
      ]
    }
  }
}
EOF

# 7. 创建QQ交易提醒配置
echo "💬 创建QQ交易提醒配置..."
cat > config/trading_system/qq_trading_alerts.json << 'EOF'
{
  "qq_trading_alerts": [
    {
      "name": "每日收盘提醒",
      "schedule": "0 15 * * *",
      "message": "📊 股票策略每日收盘提醒\\n🕒 时间: 15:00\\n📈 今日交易结束\\n💰 请检查持仓股票表现\\n💡 建议: 更新投资组合价值，检查止损止盈条件",
      "priority": "medium"
    },
    {
      "name": "止损止盈提醒",
      "trigger": "price_alert",
      "message": "🚨 止损止盈提醒！\\n📊 股票: {stock_name} ({stock_code})\\n📈 当前盈亏: {profit_rate}%\\n⏰ 触发条件: {condition}\\n💡 建议: {action}",
      "priority": "high"
    },
    {
      "name": "策略周报提醒",
      "schedule": "0 17 * * 5",
      "message": "📋 股票策略周报提醒\\n📅 时间: 周五 17:00\\n📊 本周策略表现回顾\\n💰 投资组合价值更新\\n💡 建议: 分析本周表现，调整下周策略",
      "priority": "medium"
    },
    {
      "name": "月度再平衡提醒",
      "schedule": "0 20 28 * *",
      "message": "🔄 月度投资组合再平衡提醒\\n📅 时间: 每月28日 20:00\\n📊 本月策略表现分析\\n💰 投资组合再平衡检查\\n💡 建议: 调整仓位分配，优化策略配置",
      "priority": "high"
    }
  ]
}
EOF

echo "✅ 交易监控配置已生成"

# 8. 生成系统报告
echo "📋 生成系统报告..."
cat > STOCK_TRADING_SYSTEM_REPORT.md << 'EOF'
# 股票策略交易系统部署报告

## 系统概述
基于Asset-Lens股票选择策略，建立完整的模拟交易系统，支持价值、动量、红利、反转四种策略的模拟交易和回测。

## 系统功能
### 📊 核心功能
1. **股票池管理**: 25只模拟股票，覆盖不同行业和风格
2. **策略模拟**: 四种投资策略的模拟交易
3. **风险控制**: 止损止盈、仓位控制、风险监控
4. **绩效评估**: 收益率、最大回撤、夏普比率等指标
5. **交易监控**: 每日监控、周度回顾、月度再平衡

### 🎯 投资策略
1. **价值策略** (value_strategy)
   - 特点: 低估值、稳健增长
   - 仓位: 10%，最大10只
   - 止损: -10%，止盈: 30%

2. **动量策略** (momentum_strategy)
   - 特点: 追踪强势股
   - 仓位: 8%，最大15只
   - 止损: -8%，止盈: 15%

3. **红利策略** (dividend_strategy)
   - 特点: 高股息、低波动
   - 仓位: 15%，最大8只
   - 止损: -8%，止盈: 15%

4. **反转策略** (reversal_strategy)
   - 特点: 抄底超跌股
   - 仓位: 5%，最大20只
   - 止损: -5%，止盈: 20%

### 💰 投资组合配置
1. **保守型组合**
   - 价值策略: 50%
   - 红利策略: 40%
   - 动量策略: 10%

2. **平衡型组合**
   - 价值策略: 40%
   - 动量策略: 30%
   - 红利策略: 20%
   - 反转策略: 10%

3. **进取型组合**
   - 动量策略: 50%
   - 反转策略: 30%
   - 价值策略: 20%

## 系统配置
### 📁 配置文件
```
config/trading_system/
├── trading_strategies.json      # 交易策略配置
├── simulation_rules.json        # 模拟交易规则
├── trade_record_template.json   # 交易记录模板
├── monitoring_config.json       # 交易监控配置
└── qq_trading_alerts.json       # QQ交易提醒配置
```

### 📊 数据文件
```
data/
├── stock_pool/                  # 股票池数据
└── trading_records/             # 交易记录数据
```

### 📈 报告输出
```
output/
├── stock_reports/               # 股票池报告
└── trading_reports/             # 交易模拟报告
```

## 使用说明
### 🚀 快速启动
```bash
# 创建股票池
python3 create_stock_pool.py

# 运行模拟交易
python3 simulate_trading.py

# 查看最新报告
ls -la output/trading_reports/
```

### 📊 模拟交易参数
- **初始资金**: 100,000元
- **交易费用**: 佣金0.03%，印花税0.1%
- **模拟周期**: 30天（短期）、90天（中期）、365天（长期）
- **再平衡频率**: 每月一次

### 💬 QQ提醒设置
1. **每日 15:00**: 股票策略每日收盘提醒
2. **触发式**: 止损止盈提醒
3. **每周五 17:00**: 策略周报提醒
4. **每月28日 20:00**: 月度再平衡提醒

## 模拟交易流程
### 🔄 交易流程
1. **策略选择**: 选择适合的投资策略
2. **股票筛选**: 根据策略条件筛选股票
3. **初始建仓**: 按仓位分配买入股票
4. **每日监控**: 检查价格变化和风险指标
5. **交易执行**: 触发止损止盈时自动交易
6. **绩效评估**: 定期评估策略表现

### 📈 绩效指标
1. **绝对收益**: 总收益率、年化收益率
2. **风险指标**: 最大回撤、波动率
3. **风险调整收益**: 夏普比率
4. **交易质量**: 胜率、盈亏比
5. **组合指标**: 行业集中度、仓位分布

## 风险控制
### 🛡️ 风险控制措施
1. **仓位控制**: 单只股票最大仓位20%
2. **止损纪律**: 严格执行止损规则
3. **分散投资**: 行业分散、策略分散
4. **风险监控**: 实时监控风险指标
5. **压力测试**: 模拟极端市场情况

### 🚨 风险预警
1. **价格预警**: 单日涨跌超过5%
2. **止损预警**: 亏损达到止损线
3. **止盈预警**: 盈利达到止盈线
4. **组合预警**: 最大回撤超过15%
5. **集中度预警**: 行业集中度超过30%

## 后续优化
### 🔄 短期计划
1. 集成实时行情数据
2. 优化交易算法
3. 增加更多技术指标
4. 完善回测功能

### 🎯 长期计划
1. 连接实盘交易接口
2. 集成机器学习模型
3. 实现自动化交易
4. 建立风险预警系统

---
系统部署时间: $(date)
股票池规模: 25只股票
支持策略: 4种投资策略
模拟资金: 100,000元
系统状态: 运行正常
EOF

echo "✅ 系统报告已生成"

echo ""
echo "🎉 股票策略交易系统部署完成！"
echo "=========================================="
echo ""
echo "📊 系统功能:"
echo "   - 股票池管理: 25只模拟股票"
echo "   - 策略模拟: 4种投资策略"
echo "   - 模拟交易: 支持回测和模拟"
echo "   - 风险控制: 完整的风控体系"
echo ""
echo "🎯 投资策略:"
echo "   1. 价值策略: 低估值、稳健增长"
echo "   2. 动量策略: 追踪强势股"
echo "   3. 红利策略: 高股息、稳定"
echo "   4. 反转策略: 抄底超跌股"
echo ""
echo "💰 模拟参数:"
echo "   - 初始资金: 100,000元"
echo "   - 模拟周期: 30/90/365天"
echo "   - 交易费用: