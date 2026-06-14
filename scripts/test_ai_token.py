#!/usr/bin/env python3
"""测试 AI 分析器 Token 使用"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

# 加载 .env 文件
env_path = project_root / ".env"
load_dotenv(env_path)

from asset_lens.strategy.stock_ai_analyzer import stock_ai_analyzer


def test_token_usage():
    """测试 token 使用"""

    if not ai_analyzer.enabled:
        print("❌ AI 分析器未启用")
        return

    print(f"✅ API Key: {ai_analyzer.api_key[:20]}...")
    print(f"   Model: {ai_analyzer.model}")

    # 测试分析
    result = ai_analyzer.analyze_stock_sync(
        stock_data={
            'code': '300750',
            'name': '宁德时代',
            'price': 413.0,
            'change_percent': 3.12,
            'volume': 125000,
            'turnover_rate': 2.35,
            'market_cap': 9800,
            'pe_ratio': 25.5,
        },
        strategy_signal='策略得分85分'
    )

    print("\n📊 Token 使用统计:")
    print(f"  输入 tokens: {result.prompt_tokens}")
    print(f"  输出 tokens: {result.completion_tokens}")
    print(f"  总计 tokens: {result.total_tokens}")

    # DeepSeek 价格估算
    input_cost = result.prompt_tokens * 0.001 / 1000
    output_cost = result.completion_tokens * 0.002 / 1000
    total_cost = input_cost + output_cost

    print("\n💰 费用估算 (DeepSeek 价格):")
    print(f"  输入费用: ¥{input_cost:.6f}")
    print(f"  输出费用: ¥{output_cost:.6f}")
    print(f"  总费用: ¥{total_cost:.6f}")

    print("\n📝 分析结果:")
    print(f"  决策: {result.decision.value}")
    print(f"  信心: {result.confidence}%")
    print(f"  风险: {result.risk_level}")
    print(f"  理由: {result.reasoning[:200]}..." if len(result.reasoning) > 200 else f"  理由: {result.reasoning}")
    print(f"  关键因素: {result.key_factors}")
    print(f"  市场情绪: {result.market_sentiment}")

    if result.stop_loss:
        print(f"  建议止损: {result.stop_loss}")
    if result.take_profit:
        print(f"  建议止盈: {result.take_profit}")

    print("\n📈 累计统计:")
    print(f"  总 tokens: {ai_analyzer.total_tokens_used}")
    print(f"  总费用: ¥{ai_analyzer.total_cost:.6f}")

if __name__ == "__main__":
    test_token_usage()
