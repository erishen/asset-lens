import ReactECharts from 'echarts-for-react';

export function RiskChart() {
  const option = {
    tooltip: { confine: true },
    radar: {
      indicator: [
        { name: '市场风险', max: 100 },
        { name: '集中度风险', max: 100 },
        { name: '流动性风险', max: 100 },
        { name: '信用风险', max: 100 },
        { name: '操作风险', max: 100 },
      ],
      axisName: { color: '#888', fontSize: 12 },
      radius: '70%',
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [60, 40, 30, 20, 25],
            name: '风险指标',
            areaStyle: { color: 'rgba(0, 210, 255, 0.3)' },
            lineStyle: { color: '#00d2ff' },
          },
        ],
      },
    ],
  };

  return (
    <div className="chart-container">
      <h3 className="chart-title">风险指标</h3>
      <ReactECharts option={option} style={{ height: '400px' }} />
    </div>
  );
}
