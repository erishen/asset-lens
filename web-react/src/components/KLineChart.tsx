import { useState, useEffect, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

interface KLineData {
  date: string;
  open: number;
  close: number;
  high: number;
  low: number;
  volume: number;
}

interface KLineChartProps {
  code: string;
  name?: string;
}

function calculateMA(data: KLineData[], days: number): (number | string)[] {
  const result: (number | string)[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < days - 1) {
      result.push('-');
    } else {
      let sum = 0;
      for (let j = 0; j < days; j++) {
        sum += data[i - j].close;
      }
      result.push(+(sum / days).toFixed(2));
    }
  }
  return result;
}

function calculateEMA(data: number[], period: number): number[] {
  const result: number[] = [];
  const multiplier = 2 / (period + 1);
  let ema = data[0];
  result.push(ema);
  for (let i = 1; i < data.length; i++) {
    ema = (data[i] - ema) * multiplier + ema;
    result.push(ema);
  }
  return result;
}

function calculateMACD(data: KLineData[], shortPeriod = 12, longPeriod = 26, signalPeriod = 9) {
  const closes = data.map((d) => d.close);
  const emaShort = calculateEMA(closes, shortPeriod);
  const emaLong = calculateEMA(closes, longPeriod);
  const dif = emaShort.map((v, i) => v - emaLong[i]);
  const dea = calculateEMA(dif, signalPeriod);
  const macd = dif.map((v, i) => (v - dea[i]) * 2);
  return { dif, dea, macd };
}

function calculateKDJ(data: KLineData[], n = 9, _m1 = 3, _m2 = 3) {
  const k: number[] = [];
  const d: number[] = [];
  const j: number[] = [];

  for (let i = 0; i < data.length; i++) {
    if (i < n - 1) {
      k.push(50);
      d.push(50);
      j.push(50);
    } else {
      let highestHigh = data[i].high;
      let lowestLow = data[i].low;
      for (let j = 0; j < n; j++) {
        highestHigh = Math.max(highestHigh, data[i - j].high);
        lowestLow = Math.min(lowestLow, data[i - j].low);
      }
      const rsv = highestHigh === lowestLow ? 50 : ((data[i].close - lowestLow) / (highestHigh - lowestLow)) * 100;
      const currentK = k.length > 0 ? (2 / 3) * k[k.length - 1] + (1 / 3) * rsv : rsv;
      const currentD = d.length > 0 ? (2 / 3) * d[d.length - 1] + (1 / 3) * currentK : currentK;
      const currentJ = 3 * currentK - 2 * currentD;
      k.push(currentK);
      d.push(currentD);
      j.push(currentJ);
    }
  }
  return { k, d, j };
}

export function KLineChart({ code, name }: KLineChartProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [klineData, setKlineData] = useState<KLineData[]>([]);
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily');
  const [showMA, setShowMA] = useState(true);
  const [showMACD, setShowMACD] = useState(true);
  const [showKDJ, setShowKDJ] = useState(false);

  useEffect(() => {
    fetchKLineData();
  }, [code, period]);

  const fetchKLineData = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`/api/stock/kline/${code}?period=${period}&count=120`);
      const data = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setKlineData(data.data || []);
      }
    } catch (e) {
      setError('获取 K 线数据失败');
    } finally {
      setLoading(false);
    }
  };

  const ma5 = useMemo(() => calculateMA(klineData, 5), [klineData]);
  const ma10 = useMemo(() => calculateMA(klineData, 10), [klineData]);
  const ma20 = useMemo(() => calculateMA(klineData, 20), [klineData]);
  const macdData = useMemo(() => calculateMACD(klineData), [klineData]);
  const kdjData = useMemo(() => calculateKDJ(klineData), [klineData]);

  const dates = klineData.map((d) => d.date);

  const chartOption = useMemo(() => {
    const gridTop = showMACD || showKDJ ? '35%' : '10%';
    const gridBottom = showMACD || showKDJ ? '25%' : '5%';

    const series: any[] = [
      {
        name: 'K线',
        type: 'candlestick',
        data: klineData.map((d) => [d.open, d.close, d.low, d.high]),
        itemStyle: {
          color: '#00c853',
          color0: '#ff5252',
          borderColor: '#00c853',
          borderColor0: '#ff5252',
        },
      },
    ];

    if (showMA) {
      series.push(
        { name: 'MA5', type: 'line', data: ma5, smooth: true, lineStyle: { width: 1 }, symbol: 'none', color: '#1E90FF' },
        { name: 'MA10', type: 'line', data: ma10, smooth: true, lineStyle: { width: 1 }, symbol: 'none', color: '#FF69B4' },
        { name: 'MA20', type: 'line', data: ma20, smooth: true, lineStyle: { width: 1 }, symbol: 'none', color: '#FFD700' }
      );
    }

    const xAxis: any[] = [
      {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: { color: '#888', fontSize: 10 },
        gridIndex: 0,
      },
    ];

    const yAxis: any[] = [
      {
        scale: true,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: { color: '#888' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
        gridIndex: 0,
      },
    ];

    const grid: any[] = [
      { left: '10%', right: '8%', top: gridTop, bottom: gridBottom },
    ];

    if (showMACD) {
      grid.push({ left: '10%', right: '8%', top: '75%', height: '10%' });
      xAxis.push({
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: { show: false },
        gridIndex: 1,
      });
      yAxis.push({
        scale: true,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: { color: '#888' },
        splitLine: { show: false },
        gridIndex: 1,
      });
      series.push(
        {
          name: 'MACD',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: macdData.macd.map((v) => ({
            value: v,
            itemStyle: { color: v >= 0 ? '#00c853' : '#ff5252' },
          })),
        },
        {
          name: 'DIF',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: macdData.dif,
          lineStyle: { width: 1 },
          symbol: 'none',
          color: '#FFD700',
        },
        {
          name: 'DEA',
          type: 'line',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: macdData.dea,
          lineStyle: { width: 1 },
          symbol: 'none',
          color: '#00d2ff',
        }
      );
    }

    if (showKDJ) {
      const kdjTop = showMACD ? '88%' : '75%';
      grid.push({ left: '10%', right: '8%', top: kdjTop, height: '10%' });
      xAxis.push({
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: { show: false },
        gridIndex: showMACD ? 2 : 1,
      });
      yAxis.push({
        scale: true,
        axisLine: { lineStyle: { color: '#888' } },
        axisLabel: { color: '#888' },
        splitLine: { show: false },
        gridIndex: showMACD ? 2 : 1,
      });
      series.push(
        {
          name: 'K',
          type: 'line',
          xAxisIndex: showMACD ? 2 : 1,
          yAxisIndex: showMACD ? 2 : 1,
          data: kdjData.k,
          lineStyle: { width: 1 },
          symbol: 'none',
          color: '#FF69B4',
        },
        {
          name: 'D',
          type: 'line',
          xAxisIndex: showMACD ? 2 : 1,
          yAxisIndex: showMACD ? 2 : 1,
          data: kdjData.d,
          lineStyle: { width: 1 },
          symbol: 'none',
          color: '#00d2ff',
        },
        {
          name: 'J',
          type: 'line',
          xAxisIndex: showMACD ? 2 : 1,
          yAxisIndex: showMACD ? 2 : 1,
          data: kdjData.j,
          lineStyle: { width: 1 },
          symbol: 'none',
          color: '#FFD700',
        }
      );
    }

    return {
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        confine: true,
      },
      legend: {
        data: showMA ? ['K线', 'MA5', 'MA10', 'MA20'] : ['K线'],
        textStyle: { color: '#888' },
        top: 5,
      },
      grid,
      xAxis,
      yAxis,
      dataZoom: [
        { type: 'inside', xAxisIndex: xAxis.map((_, i) => i), start: 50, end: 100 },
        { type: 'slider', xAxisIndex: xAxis.map((_, i) => i), start: 50, end: 100, height: 20 },
      ],
      series,
    };
  }, [klineData, showMA, showMACD, showKDJ, dates, ma5, ma10, ma20, macdData, kdjData]);

  if (loading) {
    return (
      <div className="chart-container">
        <h3 className="chart-title">{name || code} K 线图</h3>
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>加载 K 线数据中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="chart-container">
        <h3 className="chart-title">{name || code} K 线图</h3>
        <div className="error">{error}</div>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px', flexWrap: 'wrap', gap: '10px' }}>
        <h3 className="chart-title" style={{ margin: 0 }}>{name || code} K 线图</h3>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <div className="btn-group">
            <button
              className={`nav-btn ${period === 'daily' ? 'active' : ''}`}
              onClick={() => setPeriod('daily')}
              style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '0.85rem' }}
            >
              日K
            </button>
            <button
              className={`nav-btn ${period === 'weekly' ? 'active' : ''}`}
              onClick={() => setPeriod('weekly')}
              style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '0.85rem' }}
            >
              周K
            </button>
            <button
              className={`nav-btn ${period === 'monthly' ? 'active' : ''}`}
              onClick={() => setPeriod('monthly')}
              style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '0.85rem' }}
            >
              月K
            </button>
          </div>
          <div className="btn-group">
            <button
              className={`nav-btn ${showMA ? 'active' : ''}`}
              onClick={() => setShowMA(!showMA)}
              style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '0.85rem' }}
            >
              MA
            </button>
            <button
              className={`nav-btn ${showMACD ? 'active' : ''}`}
              onClick={() => setShowMACD(!showMACD)}
              style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '0.85rem' }}
            >
              MACD
            </button>
            <button
              className={`nav-btn ${showKDJ ? 'active' : ''}`}
              onClick={() => setShowKDJ(!showKDJ)}
              style={{ padding: '6px 12px', minWidth: 'auto', fontSize: '0.85rem' }}
            >
              KDJ
            </button>
          </div>
        </div>
      </div>
      <ReactECharts option={chartOption} style={{ height: showMACD && showKDJ ? '600px' : '500px' }} />
    </div>
  );
}
