import type { PortfolioSummary } from '../types';

interface SummaryCardsProps {
  summary: PortfolioSummary;
  strategyCount: number;
  lastUpdate: string;
}

export function SummaryCards({ summary, strategyCount, lastUpdate }: SummaryCardsProps) {
  const formatMoney = (value: number) => {
    if (!value) return '¥0';
    if (value >= 10000) {
      return '¥' + (value / 10000).toFixed(2) + '万';
    }
    return '¥' + value.toFixed(2);
  };

  return (
    <div className="cards">
      <div className="card">
        <div className="card-title">总资产</div>
        <div className="card-value">{formatMoney(summary.total_assets)}</div>
        <div className="card-change">持仓数量: {summary.position_count}</div>
      </div>
      <div className="card">
        <div className="card-title">总收益</div>
        <div className={`card-value ${summary.total_profit >= 0 ? 'positive' : 'negative'}`}>
          {formatMoney(summary.total_profit)}
        </div>
        <div className={`card-change ${summary.total_return >= 0 ? 'positive' : 'negative'}`}>
          收益率: {summary.total_return.toFixed(2)}%
        </div>
      </div>
      <div className="card">
        <div className="card-title">策略数量</div>
        <div className="card-value">{strategyCount}</div>
        <div className="card-change">已配置策略</div>
      </div>
      <div className="card">
        <div className="card-title">系统状态</div>
        <div className="card-value positive">正常</div>
        <div className="card-change">{lastUpdate}</div>
      </div>
    </div>
  );
}
