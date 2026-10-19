import { useState } from 'react';

export function MarketPage() {
  const [searchInput, setSearchInput] = useState('');
  const [result, setResult] = useState<null | { name: string; code: string; total_value?: number; items?: unknown[] }>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!searchInput.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch(`/api/stock/quote/${encodeURIComponent(searchInput.trim())}`);
      if (!response.ok) {
        const text = await response.text().catch(() => '');
        throw new Error(text || `请求失败: ${response.status}`);
      }
      const data = await response.json();
      setResult(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '查询失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="chart-container">
        <h3 className="chart-title">股票行情</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '15px' }}>
          输入股票代码进行实时行情查询。
        </p>
        <div className="search-box-full">
          <input
            type="text"
            placeholder="输入股票代码 (如 sh600519 或 600519)"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') void handleSearch();
            }}
            className="search-input"
          />
          <button className="search-btn" onClick={() => void handleSearch()} disabled={loading}>
            {loading ? '查询中…' : '查询'}
          </button>
        </div>
        {error && (
          <div className="error" style={{ marginTop: '12px' }}>
            {error}
          </div>
        )}
        {result && (
          <div style={{ marginTop: '16px' }}>
            <div>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>代码：</span>
              {result.code ?? searchInput}
            </div>
            <div>
              <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>名称：</span>
              {result.name}
            </div>
            {typeof result.total_value === 'number' && (
              <div>
                <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>市值：</span>
                {result.total_value.toLocaleString('zh-CN')}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
