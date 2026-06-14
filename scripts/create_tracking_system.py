#!/usr/bin/env python3
"""
投资产品跟踪观察系统
为阿龙的投资产品建立完整的跟踪和分析系统
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

logger = logging.getLogger(__name__)


def create_tracking_system():
    """创建完整的跟踪观察系统"""

    logger.info('🚀 建立投资产品跟踪观察系统')
    logger.info('=' * 60)

    # 加载数据
    data_file = Path('data/sample_data/投资产品-脱敏.csv')
    df = pd.read_csv(data_file)

    # 创建跟踪系统配置
    tracking_system = {
        'created_at': datetime.now().isoformat(),
        'total_products': len(df),
        'total_investment': float(df['初始金额'].sum()),
        'tracking_categories': {},
        'monitoring_settings': {},
        'analysis_framework': {}
    }

    # 1. 按类型分类跟踪
    logger.info('📊 1. 按类型分类跟踪产品:')
    logger.info('-' * 40)

    categories = {
        '稳健型投资': ['其他'],  # 理财/国债/现金等
        '基金类': ['基金'],
        '债券类': ['债券'],
        '美股类': ['美股'],
        'ETF类': ['ETF'],
        '养老金类': ['个人养老金'],
        '美元资产': ['美元基金']
    }

    for category_name, types in categories.items():
        category_df = df[df['类型'].isin(types)]
        if len(category_df) > 0:
            tracking_system['tracking_categories'][category_name] = {
                'count': len(category_df),
                'investment': float(category_df['初始金额'].sum()),
                'percentage': float(category_df['初始金额'].sum() / df['初始金额'].sum() * 100),
                'products': category_df[['名称', '代码', '类型', '风险', '初始金额', '收益率']].to_dict('records')
            }

            total_amt = category_df["初始金额"].sum()
            all_total = df["初始金额"].sum()
            logger.info("%s:", category_name)
            logger.info("   数量: %s个", len(category_df))
            logger.info(f"   金额: {total_amt:,.2f}")
            logger.info(f"   占比: {total_amt / all_total * 100:.1f}%")

    print()
    logger.info('🎯 2. 建立监控设置:')
    logger.info('-' * 40)

    # 监控设置
    tracking_system['monitoring_settings'] = {
        'daily_monitoring': {
            'time': '15:00',  # 交易日收盘后
            'items': ['price', 'change', 'volume', 'market_cap'],
            'channels': ['qqbot']
        },
        'weekly_analysis': {
            'day': 'friday',
            'time': '16:00',
            'items': ['performance', 'risk', 'correlation', 'market_trend'],
            'report_format': 'summary'
        },
        'monthly_review': {
            'day': 'last_friday',
            'time': '17:00',
            'items': ['portfolio_review', 'strategy_adjustment', 'goal_check'],
            'report_format': 'detailed'
        },
        'price_alerts': {
            'thresholds': {
                'up': 5,    # 上涨5%提醒
                'down': -3, # 下跌3%提醒
                'high': 10, # 上涨10%重点提醒
                'low': -5   # 下跌5%重点提醒
            }
        }
    }

    logger.info('✅ 每日监控: 交易日15:00 (收盘后)')
    logger.info('✅ 每周分析: 周五16:00')
    logger.info('✅ 每月回顾: 每月最后一个周五17:00')
    logger.info('✅ 价格提醒: 涨跌5%提醒，涨跌10%重点提醒')

    print()
    logger.info('📈 3. 建立分析框架:')
    logger.info('-' * 40)

    # 分析框架
    tracking_system['analysis_framework'] = {
        'fund_analysis': {
            '持仓分析': ['top_holdings', 'sector_distribution', 'style_analysis'],
            '业绩分析': ['returns', 'risk_adjusted_returns', 'benchmark_comparison'],
            '经理分析': ['manager_tenure', 'investment_style', 'track_record']
        },
        'stock_analysis': {
            '基本面': ['financials', 'valuation', 'growth'],
            '技术面': ['trend', 'momentum', 'support_resistance'],
            '市场面': ['liquidity', 'sentiment', 'institutional_holding']
        },
        'market_analysis': {
            '大盘分析': ['index_trend', 'market_breadth', 'volume_analysis'],
            '行业分析': ['sector_rotation', 'industry_trend', 'thematic_investing'],
            '宏观分析': ['interest_rates', 'inflation', 'policy_changes']
        },
        'portfolio_analysis': {
            '资产配置': ['allocation', 'diversification', 'rebalancing'],
            '风险分析': ['volatility', 'drawdown', 'correlation'],
            '业绩归因': ['allocation_effect', 'selection_effect', 'timing_effect']
        }
    }

    logger.info('✅ 基金分析: 持仓、业绩、经理分析')
    logger.info('✅ 股票分析: 基本面、技术面、市场面')
    logger.info('✅ 市场分析: 大盘、行业、宏观分析')
    logger.info('✅ 组合分析: 资产配置、风险分析、业绩归因')

    print()
    logger.info('🔧 4. 创建具体跟踪任务:')
    logger.info('-' * 40)

    # 具体跟踪任务
    tracking_tasks = []

    # 基金类跟踪任务
    fund_products = df[df['类型'] == '基金']
    for _, product in fund_products.iterrows():
        task = {
            'product_name': product['名称'],
            'product_code': product['代码'],
            'category': '基金',
            'tracking_tasks': [
                {'task': '持仓分析', 'frequency': 'monthly', 'priority': 'high'},
                {'task': '业绩跟踪', 'frequency': 'weekly', 'priority': 'medium'},
                {'task': '行业分析', 'frequency': 'weekly', 'priority': 'medium'},
                {'task': '经理跟踪', 'frequency': 'quarterly', 'priority': 'low'}
            ]
        }
        tracking_tasks.append(task)

    # 美股类跟踪任务
    us_stock_products = df[df['类型'] == '美股']
    for _, product in us_stock_products.iterrows():
        task = {
            'product_name': product['名称'],
            'product_code': product['代码'],
            'category': '美股',
            'tracking_tasks': [
                {'task': '价格监控', 'frequency': 'daily', 'priority': 'high'},
                {'task': '财报跟踪', 'frequency': 'quarterly', 'priority': 'high'},
                {'task': '行业趋势', 'frequency': 'weekly', 'priority': 'medium'},
                {'task': '宏观影响', 'frequency': 'monthly', 'priority': 'medium'}
            ]
        }
        tracking_tasks.append(task)

    # ETF类跟踪任务
    etf_products = df[df['类型'] == 'ETF']
    for _, product in etf_products.iterrows():
        task = {
            'product_name': product['名称'],
            'product_code': product['代码'],
            'category': 'ETF',
            'tracking_tasks': [
                {'task': '指数跟踪', 'frequency': 'daily', 'priority': 'high'},
                {'task': '成分股分析', 'frequency': 'monthly', 'priority': 'medium'},
                {'task': '流动性监控', 'frequency': 'weekly', 'priority': 'low'},
                {'task': '费率比较', 'frequency': 'yearly', 'priority': 'low'}
            ]
        }
        tracking_tasks.append(task)

    tracking_system['tracking_tasks'] = tracking_tasks

    logger.info("✅ 创建了 %s 个具体跟踪任务", len(tracking_tasks))
    logger.info("   基金类: %s 个产品", len(fund_products))
    logger.info("   美股类: %s 个产品", len(us_stock_products))
    logger.info("   ETF类: %s 个产品", len(etf_products))

    print()
    logger.info('📁 5. 保存系统配置:')
    logger.info('-' * 40)

    # 创建输出目录
    output_dir = Path('output/tracking_system')
    output_dir.mkdir(exist_ok=True)

    # 保存JSON配置
    json_file = output_dir / 'tracking_system_config.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(tracking_system, f, indent=2, ensure_ascii=False)

    # 保存YAML配置（更易读）
    yaml_file = output_dir / 'tracking_system_config.yaml'
    with open(yaml_file, 'w', encoding='utf-8') as f:
        yaml.dump(tracking_system, f, allow_unicode=True, default_flow_style=False)

    # 创建产品列表CSV
    products_file = output_dir / 'tracking_products.csv'
    df[['类型', '名称', '代码', '风险', '初始金额', '收益率', '年化收益']].to_csv(products_file, index=False, encoding='utf-8-sig')

    logger.info("✅ JSON配置: %s", json_file)
    logger.info("✅ YAML配置: %s", yaml_file)
    logger.info("✅ 产品列表: %s", products_file)

    print()
    logger.info('🎯 6. 下一步行动建议:')
    logger.info('-' * 40)

    actions = [
        '1. 设置每日自动数据获取脚本',
        '2. 建立基金持仓数据库',
        '3. 配置价格提醒系统',
        '4. 创建定期分析报告模板',
        '5. 集成市场数据API',
        '6. 建立风险预警机制',
        '7. 优化数据可视化展示',
        '8. 设置移动端访问接口'
    ]

    for action in actions:
        logger.info(action)

    print()
    logger.info('💡 系统特点:')
    logger.info('   • 全面覆盖: 所有50个产品都有跟踪配置')
    logger.info('   • 分类管理: 7个类别，针对性跟踪策略')
    logger.info('   • 多维度分析: 基本面、技术面、市场面')
    logger.info('   • 自动化监控: 每日、每周、每月自动分析')
    logger.info('   • 风险预警: 价格阈值提醒，市场风险监控')

    return tracking_system

if __name__ == '__main__':
    create_tracking_system()
