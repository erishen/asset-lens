import type { Strategy } from '../types';

interface StrategyCardsProps {
  strategies: Strategy[];
}

export function StrategyCards({ strategies }: StrategyCardsProps) {
  return (
    <div className="cards">
      {strategies.map((strategy) => (
        <div className="card" key={strategy.name}>
          <div className="card-title">{strategy.name}</div>
          <div className="card-value" style={{ fontSize: '1rem' }}>
            {strategy.description || '暂无描述'}
          </div>
          <div className="card-change">
            仓位: {(strategy.position_size * 100).toFixed(0)}% | 止损:{' '}
            {(strategy.stop_loss * 100).toFixed(0)}% | 止盈:{' '}
            {(strategy.take_profit * 100).toFixed(0)}%
          </div>
        </div>
      ))}
    </div>
  );
}
