import { useState, useEffect } from 'react';
import ReactECharts from 'echarts-for-react';

interface PerformanceData {
  total_initial: number;
  total_current: number;
  total_profit: number;
  total_return_rate: number;
  type_summary: TypeSummary[];
  history: HistoryItem[];
  update_time: string;
}

interface TypeSummary {
  type: string;
  count: number;
  initial: number;
  current: number;
  profit: number;
  return_rate: number;
}

interface HistoryItem {
  date: string;
  value: number;
  return_rate: number;
}

export function PerformanceChart() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [data, setData] = useState<PerformanceData | null>(null);

  useEffect(() => {
    fetchPerformanceData();
  }, []);

  const fetchPerformanceData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch('/api/portfolio/performance');
      const result = await response.json();

      if (result.error) {
        setError(result.error);
      } else {
        setData(result);
      }
    } catch (e) {
      setError('获取收益数据失败');
    } finally {
      setLoading(false);
    }
  };

  const formatMoney = (value: number) => {
    if (value >= 10000) {
      return '¥' + (value / 10000).toFixed(2) + '万';
    }
    return '¥' + value.toFixed(2);
  };

  const lineChartOption = {
    tooltip: {
      trigger: 'axis' as const,
      confine: true,
      formatter: (params: any) => {
        const item = params[0];
        return `${item.axisValue}<br/>资产: ${formatMoney(data?.history[item.dataIndex]?.value || 0)}<br/>收益率: ${(data?.history[item.dataIndex]?.return_rate || 0).toFixed(2)}%`;
      },
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category' as const,
      data: data?.history.map((h) => h.date.slice(5)) || [],
      axisLabel: { color: '#888', fontSize: 10 },
    },
    yAxis: [
      {
        type: 'value' as const,
        name: '资产',
        axisLabel: { color: '#888', formatter: (v: number) => (v / 10000).toFixed(0) + '万' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      },
      {
        type: 'value' as const,
        name: '收益率',
        axisLabel: { color: '#888', formatter: '{value}%' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '资产',
        type: 'line' as const,
        data: data?.history.map((h) => h.value) || [],
        smooth: true,
        areaStyle: { color: 'rgba(0, 210, 255, 0.1)' },
        lineStyle: { color: '#00d2ff', width: 2 },
        itemStyle: { color: '#00d2ff' },
      },
      {
        name: '收益率',
        type: 'line' as const,
        yAxisIndex: 1,
        data: data?.history.map((h) => h.return_rate.toFixed(2)) || [],
        smooth: true,
        lineStyle: { color: '#00c853', width: 2, type: 'dashed' as const },
        itemStyle: { color: '#00c853' },
      },
    ],
  };

  const pieChartOption = {
    tooltip: { trigger: 'item' as const, formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical' as const, left: 'left', textStyle: { color: '#888' } },
    series: [
      {
        type: 'pie' as const,
        radius: ['40%', '70%'],
        center: ['60%', '50%'],
        data: data?.type_summary.map((t) => ({ name: t.type, value: t.current })) || [],
        itemStyle: { borderRadius: 8, borderColor: '#1a1a2e', borderWidth: 2 },
        label: { show: false },
        emphasis: { label: { show: true, fontSize: 14 } },
      },
    ],
  };

  if (loading) {
    return (
      <div className="chart-container">
        <h3 className="chart-title">收益曲线</h3>
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>加载收益数据中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-container">
        <h3 className="chart-title">收益曲线</h3>
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="stats-bar">
        <span>总资产: {formatMoney(data?.total_current || 0)}</span>
        <span className={(data?.total_profit || 0) >= 0 ? 'positive' : 'negative'}>
          总收益: {formatMoney(data?.total_profit || 0)}
        </span>
        <span className={(data?.total_return_rate || 0) >= 0 ? 'positive' : 'negative'}>
          收益率: {(data?.total_return_rate || 0).toFixed(2)}%
        </span>
        <span>持仓: {data?.type_summary.reduce((sum, t) => sum + t.count, 0) || 0} 个</span>
      </div>

      <div className="chart-container">
        <h3 className="chart-title">资产趋势 (近30天)</h3>
        <ReactECharts option={lineChartOption} style={{ height: '350px' }} />
      </div>

      <div className="chart-container">
        <h3 className="chart-title">类型分布</h3>
        <ReactECharts option={pieChartOption} style={{ height: '350px' }} />
      </div>

      <div className="chart-container">
        <h3 className="chart-title">类型收益对比</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>类型</th>
                <th>数量</th>
                <th>初始金额</th>
                <th>当前金额</th>
                <th>收益</th>
                <th>收益率</th>
              </tr>
            </thead>
            <tbody>
              {data?.type_summary.map((t) => (
                <tr key={t.type}>
                  <td>{t.type}</td>
                  <td>{t.count}</td>
                  <td>{formatMoney(t.initial)}</td>
                  <td>{formatMoney(t.current)}</td>
                  <td className={t.profit >= 0 ? 'positive' : 'negative'}>{formatMoney(t.profit)}</td>
                  <td className={t.return_rate >= 0 ? 'positive' : 'negative'}>{t.return_rate.toFixed(2)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
