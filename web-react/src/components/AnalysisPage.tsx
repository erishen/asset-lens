import { useState } from 'react';
import { KLineChart } from './KLineChart';
import { PerformanceChart } from './PerformanceChart';

export function AnalysisPage() {
  const [stockCode, setStockCode] = useState('sh600519');
  const [stockName, setStockName] = useState('贵州茅台');
  const [searchInput, setSearchInput] = useState('');

  const handleSearch = async () => {
    if (!searchInput.trim()) return;
    try {
      const response = await fetch(`/api/stock/quote/${searchInput}`);
      if (response.ok) {
        const data = await response.json();
        setStockCode(searchInput);
        setStockName(data.name);
      }
    } catch (e) {
      console.error('Search failed:', e);
    }
  };

  return (
    <div>
      <div className="search-section">
        <h3 className="chart-title">股票 K 线分析</h3>
        <div className="search-box-full">
          <input
            type="text"
            placeholder="输入股票代码 (如 sh600519)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            className="search-input"
          />
          <button className="search-btn" onClick={handleSearch}>
            查询
          </button>
        </div>
      </div>

      <KLineChart code={stockCode} name={stockName} />

      <PerformanceChart />

      <div className="chart-container">
        <h3 className="chart-title">导出报告</h3>
        <p style={{ color: '#888', marginBottom: '15px' }}>
          导出投资组合报告，包含持仓明细、收益分析等内容
        </p>
        <a
          href="/api/report/export"
          target="_blank"
          className="refresh-btn"
          style={{ textDecoration: 'none', display: 'inline-block' }}
        >
          导出 HTML 报告
        </a>
      </div>
    </div>
  );
}
