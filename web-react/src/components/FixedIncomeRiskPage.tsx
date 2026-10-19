import { useState, useEffect } from 'react';
import { fixedIncomeApi } from '../services/api';
import type { FixedIncomeRiskView } from '../types';

function fmt(n: number): string {
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 0 });
}

function pct(n: number, digits = 1): string {
  return `${(n * 100).toFixed(digits)}%`;
}

const PRIORITY_CLASS: Record<string, string> = {
  high: 'negative',
  medium: '',
  low: 'positive',
};

export function FixedIncomeRiskPage() {
  const [view, setView] = useState<FixedIncomeRiskView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [nonce, setNonce] = useState(0);

  // 初始就是 loading，所以 effect 里不需要同步 setState（react-hooks/set-state-in-effect）。
  // setState 只发生在 promise 回调里，并挂 cancelled 防止卸载后写 state。
  useEffect(() => {
    let cancelled = false;
    fixedIncomeApi
      .getRiskView()
      .then((data) => {
        if (cancelled) return;
        setView(data);
        setError(null);
      })
      .catch((e: unknown) => {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : '加载失败');
      });
    return () => {
      cancelled = true;
    };
  }, [nonce]);

  const retry = () => {
    setView(null);
    setError(null);
    setNonce((n) => n + 1);
  };

  const loading = view === null && error === null;

  if (loading) return <div className="loading">加载固收风险数据…</div>;

  if (error) {
    return (
      <div className="error">
        <p>{error}</p>
        <button className="refresh-btn" onClick={retry}>
          重试
        </button>
      </div>
    );
  }

  if (!view) return null;

  if (view.error) {
    return (
      <div className="error">
        <p>{view.error}</p>
        <button className="refresh-btn" onClick={retry}>
          重试
        </button>
      </div>
    );
  }

  const { ladder, concentration, data_quality: dq, alerts } = view;
  const buckets = ladder.buckets.filter((b) => b.count > 0);
  const maxBucketAmount = Math.max(...buckets.map((b) => b.amount), 1);

  return (
    <div>
      <div className="cards">
        <div className="card">
          <div className="card-title">固收市值</div>
          <div className="card-value">{fmt(view.total_amount)}</div>
          <div className="card-change">
            {view.fixed_income_count} 只 · 截至 {view.as_of}
          </div>
        </div>
        <div className="card">
          <div className="card-title">最大发行方</div>
          <div className="card-value">
            {concentration.top1_name || '—'}
            <span style={{ fontSize: '1rem' }}>
              {' '}
              {pct(concentration.top1_share, 0)}
            </span>
          </div>
          <div className="card-change">HHI {concentration.hhi.toFixed(3)}</div>
        </div>
        <div className="card">
          <div className="card-title">赎回渠道依赖</div>
          <div className="card-value">
            {concentration.channel_top1_name || '—'}
            <span style={{ fontSize: '1rem' }}>
              {' '}
              {pct(concentration.channel_top1_share, 0)}
            </span>
          </div>
          <div className="card-change">渠道 ≠ 信用，两者分开看</div>
        </div>
        <div className="card">
          <div className="card-title">到期梯队可信度</div>
          <div className="card-value">
            {ladder.confidence === 'low' ? '偏低' : ladder.confidence === 'medium' ? '中等' : '高'}
          </div>
          <div className="card-change">
            覆盖 {pct(ladder.coverage, 0)} · 开放型 {ladder.open_ended_count} 只
          </div>
        </div>
      </div>

      {alerts.length > 0 && (
        <div className="chart-container">
          <h3 className="chart-title">风险提示</h3>
          {alerts.map((a) => (
            <div key={a.kind + a.title} style={{ marginBottom: 14 }}>
              <div className={PRIORITY_CLASS[a.priority] ?? ''} style={{ fontWeight: 600 }}>
                {a.title}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{a.detail}</div>
            </div>
          ))}
        </div>
      )}

      <div className="chart-container">
        <h3 className="chart-title">到期梯队</h3>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 15, fontSize: '0.9rem' }}>
          开放型（可赎）本来就没有到期日，不算数据缺失。
        </p>
        {buckets.map((b) => (
          <div key={b.label} style={{ marginBottom: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
              <span>{b.label}</span>
              <span>
                {b.count} 只 · {fmt(b.amount)} 元 · {pct(b.share, 1)}
              </span>
            </div>
            <div
              style={{
                height: 8,
                background: 'var(--border-color)',
                borderRadius: 4,
                marginTop: 5,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${(b.amount / maxBucketAmount) * 100}%`,
                  height: '100%',
                  background: 'linear-gradient(90deg, var(--gradient-start), var(--gradient-end))',
                }}
              />
            </div>
          </div>
        ))}
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 12 }}>
          30 天滚动 {view.rolling_count} 只 / {fmt(view.rolling_amount)} 元
        </p>
      </div>

      <div className="table-container">
        <h3 className="chart-title">发行方集中度</h3>
        <table>
          <thead>
            <tr>
              <th>发行方</th>
              <th>只数</th>
              <th>市值</th>
              <th>占比</th>
            </tr>
          </thead>
          <tbody>
            {concentration.exposures.map((e) => (
              <tr key={e.name}>
                <td>{e.name}</td>
                <td>{e.count}</td>
                <td>{fmt(e.amount)}</td>
                <td>{pct(e.share, 1)}</td>
              </tr>
            ))}
            <tr>
              <td style={{ color: 'var(--text-secondary)' }}>未识别（名称未归一）</td>
              <td>{concentration.unattributed_count}</td>
              <td>{fmt(concentration.unattributed_amount)}</td>
              <td style={{ color: 'var(--text-secondary)' }}>
                {pct(concentration.unattributed_amount / view.total_amount, 1)}
              </td>
            </tr>
          </tbody>
        </table>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 12 }}>
          HHI 按已识别发行方归一（{pct(concentration.issuer_attribution_rate, 0)} 金额可归属），
          未识别部分单独列出而非摊进分母。
        </p>
      </div>

      {view.equity_exposure_count > 0 && (
        <div className="chart-container">
          <h3 className="chart-title">固收口径内含权益敞口</h3>
          <div className="card-value">
            {view.equity_exposure_count} 只 / {fmt(view.equity_exposure_amount)} 元
          </div>
          <p style={{ color: 'var(--text-secondary)', marginTop: 8, fontSize: '0.9rem' }}>
            养老金、理财账户里的指数、混合、ETF联接类产品，收益来源是权益波动而非信用。
            其中 {view.equity_exposure_losing_count} 只当前亏损。
          </p>
        </div>
      )}

      {view.yield_anomalies.length > 0 && (
        <div className="table-container">
          <h3 className="chart-title">固收收益异常</h3>
          <table>
            <thead>
              <tr>
                <th>产品</th>
                <th>类型</th>
                <th>说明</th>
              </tr>
            </thead>
            <tbody>
              {view.yield_anomalies.map((a) => (
                <tr key={a.kind + a.name}>
                  <td>{a.name}</td>
                  <td>
                    <span className="tag tag-bond">
                      {a.kind === 'negative_return' ? '负收益' : '数值异常'}
                    </span>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{a.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div className="table-container">
        <h3 className="chart-title">数据完整度</h3>
        <table>
          <tbody>
            <tr>
              <td>明确到期日</td>
              <td>{dq.dated_count}</td>
              <td style={{ color: 'var(--text-secondary)' }}>可做到期梯队</td>
            </tr>
            <tr>
              <td>开放型（可赎）</td>
              <td>
                {dq.open_ended_count}（{pct(dq.open_ended_rate, 0)}）
              </td>
              <td style={{ color: 'var(--text-secondary)' }}>正常，非缺失</td>
            </tr>
            <tr>
              <td>到期日填错</td>
              <td>{dq.dirty_maturity_count}</td>
              <td style={{ color: 'var(--text-secondary)' }}>需修 CSV</td>
            </tr>
            <tr>
              <td>到期日真缺失</td>
              <td>{dq.missing_maturity_count}</td>
              <td style={{ color: 'var(--text-secondary)' }}>需补数据</td>
            </tr>
            <tr>
              <td>缺起购日 / 缺年化</td>
              <td>
                {dq.missing_start_date_count} / {dq.missing_annual_count}
              </td>
              <td style={{ color: 'var(--text-secondary)' }}>影响滚动与年化核对</td>
            </tr>
          </tbody>
        </table>
        {view.note && (
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginTop: 12 }}>
            {view.note}
          </p>
        )}
      </div>
    </div>
  );
}
