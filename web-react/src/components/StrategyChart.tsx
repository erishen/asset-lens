import ReactECharts from 'echarts-for-react';
import type { Strategy } from '../types';

interface StrategyChartProps {
  strategies: Strategy[];
}

export function StrategyChart({ strategies }: StrategyChartProps) {
  const strategyNames = strategies.map((s) => s.name);
  const positionSizes = strategies.map((s) => (s.position_size * 100).toFixed(0));
  const stopLosses = strategies.map((s) => (Math.abs(s.stop_loss) * 100).toFixed(0));
  const takeProfits = strategies.map((s) => (s.take_profit * 100).toFixed(0));

  const option = {
    tooltip: {
      trigger: 'axis' as const,
      axisPointer: { type: 'shadow' as const },
      confine: true,
    },
    legend: {
      data: ['仓位比例', '止损比例', '止盈比例'],
      textStyle: { color: '#888', fontSize: 12 },
    },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: strategyNames,
      axisLabel: { color: '#888', fontSize: 12 },
    },
    yAxis: { type: 'value' as const, axisLabel: { color: '#888', formatter: '{value}%' } },
    series: [
      {
        name: '仓位比例',
        type: 'bar',
        data: positionSizes,
        itemStyle: { color: '#00d2ff' },
      },
      {
        name: '止损比例',
        type: 'bar',
        data: stopLosses,
        itemStyle: { color: '#ff5252' },
      },
      {
        name: '止盈比例',
        type: 'bar',
        data: takeProfits,
        itemStyle: { color: '#00c853' },
      },
    ],
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">策略参数对比</h3>
      <ReactECharts option={option} style={{ height: '400px' }} />
    </div>
  );
}
