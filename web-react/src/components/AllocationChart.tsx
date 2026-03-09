import ReactECharts from 'echarts-for-react';
import type { PortfolioItem } from '../types';

interface AllocationChartProps {
  items: PortfolioItem[];
}

export function AllocationChart({ items }: AllocationChartProps) {
  const typeData: Record<string, number> = {};
  items.forEach((item) => {
    const type = item.type || '其他';
    typeData[type] = (typeData[type] || 0) + (item.current_amount || 0);
  });

  const chartData = Object.entries(typeData).map(([name, value]) => ({ name, value }));

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: ¥{c} ({d}%)',
      confine: true,
    },
    legend: {
      orient: 'vertical' as const,
      left: 'left',
      top: 'middle',
      textStyle: { color: '#fff', fontSize: 14 },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#1a1a2e',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)',
          },
        },
        labelLine: { show: false },
        data: chartData,
        animationType: 'scale',
        animationEasing: 'elasticOut',
      },
    ],
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">资产配置</h3>
      <ReactECharts option={option} style={{ height: '400px' }} />
    </div>
  );
}
