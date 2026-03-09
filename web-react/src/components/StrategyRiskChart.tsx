import ReactECharts from 'echarts-for-react';
import type { Strategy } from '../types';

interface StrategyRiskChartProps {
  strategies: Strategy[];
}

export function StrategyRiskChart({ strategies }: StrategyRiskChartProps) {
  const data = strategies.map((s) => [
    Math.abs(s.stop_loss) * 100,
    s.take_profit * 100,
    s.name,
  ]);

  const option = {
    tooltip: {
      confine: true,
      formatter: (params: { data: (string | number)[] }) => {
        return `${params.data[2]}<br/>风险: ${Number(params.data[0]).toFixed(0)}%<br/>收益: ${Number(params.data[1]).toFixed(0)}%`;
      },
    },
    grid: { left: '10%', right: '10%', bottom: '15%', containLabel: true },
    xAxis: {
      name: '风险(止损%)',
      nameTextStyle: { color: '#888', fontSize: 12 },
      axisLabel: { color: '#888', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    },
    yAxis: {
      name: '收益(止盈%)',
      nameTextStyle: { color: '#888', fontSize: 12 },
      axisLabel: { color: '#888', fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 20,
        large: true,
        largeThreshold: 100,
        data: data,
        itemStyle: {
          color: (params: { dataIndex: number }) => {
            const colors = ['#00d2ff', '#00c853', '#ff9800', '#9c27b0', '#2196f3'];
            return colors[params.dataIndex % colors.length];
          },
        },
      },
    ],
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">策略风险收益分布</h3>
      <ReactECharts option={option} style={{ height: '400px' }} />
    </div>
  );
}
