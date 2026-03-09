import ReactECharts from 'echarts-for-react';
import type { PortfolioItem } from '../types';

interface ProfitChartProps {
  items: PortfolioItem[];
}

function sampleData(data: PortfolioItem[], maxPoints = 20): PortfolioItem[] {
  if (data.length <= maxPoints) return data;
  const step = Math.ceil(data.length / maxPoints);
  const result: PortfolioItem[] = [];
  for (let i = 0; i < data.length; i += step) {
    result.push(data[i]);
  }
  return result;
}

export function ProfitChart({ items }: ProfitChartProps) {
  const profitData = sampleData(items, 20);

  const option = {
    tooltip: {
      trigger: 'axis' as const,
      axisPointer: { type: 'shadow' as const },
      confine: true,
    },
    grid: { left: '3%', right: '4%', bottom: '15%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: profitData.map((d) => d.name),
      axisLabel: { color: '#888', rotate: 30, fontSize: 12 },
    },
    yAxis: { type: 'value' as const, axisLabel: { color: '#888' } },
    series: [
      {
        type: 'bar',
        barWidth: 'auto',
        large: true,
        largeThreshold: 500,
        data: profitData.map((d) => ({
          value: d.profit,
          itemStyle: { color: d.profit >= 0 ? '#00c853' : '#ff5252' },
        })),
        animationDelay: (idx: number) => idx * 10,
      },
    ],
    animationEasing: 'elasticOut',
  };

  return (
    <div className="chart-container" style={{ marginTop: '30px' }}>
      <h3 className="chart-title">收益分布</h3>
      <ReactECharts option={option} style={{ height: '400px' }} />
    </div>
  );
}
