import { useCallback, useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { quantApi } from '../services/api';
import type {
  QuantCvarResponse,
  QuantMeta,
  QuantMpcResponse,
  QuantOptimizeResponse,
  QuantSimulateResponse,
} from '../types';

type Tab = 'cvar' | 'optimize' | 'simulate' | 'mpc';

const TABS: { key: Tab; label: string }[] = [
  { key: 'cvar', label: '风险价值 CVaR' },
  { key: 'optimize', label: '组合优化' },
  { key: 'simulate', label: '蒙特卡洛' },
  { key: 'mpc', label: 'MPC 回测' },
];

const pct = (v: number, digits = 2) => `${(v * 100).toFixed(digits)}%`;
const num = (v: number, digits = 3) => v.toFixed(digits);

/** 数据源说明：明确是资产类别代理行情，不是逐笔持仓回测。 */
function SourceNote({ meta }: { meta?: QuantMeta }) {
  if (!meta) return null;
  return (
    <div className="info-row" style={{ fontSize: 12, color: '#888', marginBottom: 12 }}>
      数据源：{meta.source} · {meta.periods} 个交易日（{meta.start_date} ~ {meta.end_date}）· 组合口径：{meta.portfolio}
    </div>
  );
}

function Stat({ label, value, cls = '' }: { label: string; value: string; cls?: string }) {
  return (
    <div className="card" style={{ flex: 1, minWidth: 150 }}>
      <div className="card-title">{label}</div>
      <div className={`card-value ${cls}`} style={{ fontSize: 20 }}>{value}</div>
    </div>
  );
}

export function QuantAnalysis() {
  const [tab, setTab] = useState<Tab>('cvar');
  const [level, setLevel] = useState(0.95);
  const [objective, setObjective] = useState('min_variance');
  const [method, setMethod] = useState('bootstrap');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [cvar, setCvar] = useState<QuantCvarResponse | null>(null);
  const [optimize, setOptimize] = useState<QuantOptimizeResponse | null>(null);
  const [simulate, setSimulate] = useState<QuantSimulateResponse | null>(null);
  const [mpc, setMpc] = useState<QuantMpcResponse | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      if (tab === 'cvar') setCvar(await quantApi.getCvar(level));
      else if (tab === 'optimize') setOptimize(await quantApi.optimize(objective));
      else if (tab === 'simulate') setSimulate(await quantApi.simulate(method));
      else setMpc(await quantApi.mpc());
    } catch (e: unknown) {
      // 后端统一用 FastAPI HTTPException → {"detail": "..."}；兼容旧的 {error:{message}} 形态。
      const err = e as {
        response?: { data?: { detail?: string; error?: { message?: string } | string } };
        message?: string;
      };
      const data = err?.response?.data;
      const detail = typeof data?.detail === 'string' ? data.detail : '';
      const legacy = typeof data?.error === 'string' ? data.error : data?.error?.message;
      setError(detail || legacy || err?.message || '量化分析请求失败');
    } finally {
      setLoading(false);
    }
  }, [tab, level, objective, method]);

  useEffect(() => {
    void load();
  }, [load]);

  const meta = tab === 'cvar' ? cvar?.meta
    : tab === 'optimize' ? optimize?.meta
    : tab === 'simulate' ? simulate?.meta
    : mpc?.meta;

  return (
    <div className="chart-container">
      <h3 className="chart-title">量化分析（真实行情构造的资产类别收益率）</h3>
      <div className="toolbar" style={{ marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`nav-btn ${tab === t.key ? 'active' : ''}`}
            onClick={() => setTab(t.key)}
          >
            {t.label}
          </button>
        ))}
        {tab === 'cvar' && (
          <select className="filter-select" value={level} onChange={(e) => setLevel(Number(e.target.value))}>
            <option value={0.9}>90% 置信</option>
            <option value={0.95}>95% 置信</option>
            <option value={0.99}>99% 置信</option>
          </select>
        )}
        {tab === 'optimize' && (
          <select className="filter-select" value={objective} onChange={(e) => setObjective(e.target.value)}>
            <option value="min_variance">最小方差</option>
            <option value="max_sharpe">最大夏普</option>
            <option value="min_cvar">最小 CVaR</option>
            <option value="frontier">有效前沿</option>
          </select>
        )}
        {tab === 'simulate' && (
          <select className="filter-select" value={method} onChange={(e) => setMethod(e.target.value)}>
            <option value="bootstrap">Bootstrap 重采样</option>
            <option value="gbm">几何布朗运动</option>
          </select>
        )}
        <button className="refresh-btn" onClick={() => void load()} disabled={loading}>
          {loading ? '计算中…' : '刷新'}
        </button>
      </div>

      <SourceNote meta={meta} />

      {error && <div className="error">{error}</div>}
      {loading && <div className="loading">正在基于真实行情计算…</div>}

      {/* CVaR */}
      {tab === 'cvar' && cvar && !loading && (
        <>
          <div className="cards" style={{ marginBottom: 12 }}>
            <Stat label={`等权组合 VaR (${pct(cvar.level, 0)})`} value={pct(cvar.portfolio.var)} cls="negative" />
            <Stat label={`等权组合 CVaR (${pct(cvar.level, 0)})`} value={pct(cvar.portfolio.cvar)} cls="negative" />
            <Stat label="资产类别数" value={String(cvar.assets.length)} />
          </div>
          <ReactECharts
            style={{ height: 320 }}
            option={{
              tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, confine: true,
                formatter: (params: any) => `${params[0].name}<br/>CVaR: ${pct(params[0].value)}` },
              grid: { left: '3%', right: '8%', bottom: '3%', containLabel: true },
              xAxis: { type: 'value', axisLabel: { color: '#888', formatter: (v: number) => pct(v, 1) } },
              yAxis: { type: 'category', data: cvar.assets.map((a) => a.name).reverse(), axisLabel: { color: '#888' } },
              series: [{
                type: 'bar',
                // data 存原始小数（与后端 cvar 口径一致），三处显示统一走 pct 乘 100
                data: cvar.assets.map((a) => a.cvar).reverse(),
                itemStyle: { color: '#ff6b6b' },
                label: { show: true, position: 'right', formatter: (p: any) => pct(p.value), color: '#888' },
              }],
            }}
          />
          <div className="table-container" style={{ marginTop: 12 }}>
            <table>
              <thead><tr><th>资产类别</th><th>日收益均值</th><th>日波动率</th><th>VaR</th><th>CVaR</th></tr></thead>
              <tbody>
                {cvar.assets.map((a) => (
                  <tr key={a.name}>
                    <td>{a.name}</td>
                    <td className={a.mean >= 0 ? 'positive' : 'negative'}>{pct(a.mean)}</td>
                    <td>{pct(a.volatility)}</td>
                    <td className="negative">{pct(a.var)}</td>
                    <td className="negative">{pct(a.cvar)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}

      {/* 组合优化 */}
      {tab === 'optimize' && optimize && !loading && (
        <>
          {objective === 'frontier' ? (
            <>
              <div className="info-row">有效前沿：每个波动率水平下的最高预期收益（{optimize.frontier.length} 个解）。</div>
              <ReactECharts
                style={{ height: 400 }}
                option={{
                  tooltip: { trigger: 'item', confine: true,
                    formatter: (p: any) => `波动率 ${p.value[0]}%<br/>预期收益 ${p.value[1]}%<br/>组合 ${p.data[2]}` },
                  grid: { left: '3%', right: '5%', bottom: '8%', containLabel: true },
                  xAxis: { type: 'value', name: '日波动率', axisLabel: { color: '#888', formatter: (v: number) => `${v}%` } },
                  yAxis: { type: 'value', name: '日预期收益', axisLabel: { color: '#888', formatter: (v: number) => `${v}%` } },
                  series: [{
                    type: 'line',
                    symbolSize: 10,
                    data: optimize.frontier.map((p) => [
                      +(p.volatility * 100).toFixed(3),
                      +(p.expected_return * 100).toFixed(3),
                      Object.entries(p.weights).filter(([, w]) => w > 0.01).map(([n, w]) => `${n} ${pct(w, 0)}`).join(' / '),
                    ]),
                    lineStyle: { color: '#00d2ff', width: 2 },
                    itemStyle: { color: '#00d2ff' },
                  }],
                }}
              />
            </>
          ) : optimize.result ? (
            <>
              <div className="cards" style={{ marginBottom: 12 }}>
                <Stat label="预期日收益" value={pct(optimize.result.expected_return)} cls={optimize.result.expected_return >= 0 ? 'positive' : 'negative'} />
                <Stat label="日波动率" value={pct(optimize.result.volatility)} />
                <Stat label="CVaR (95%)" value={pct(optimize.result.cvar)} cls="negative" />
                <Stat label="目标值" value={optimize.result.objective_value === null ? '无定义' : num(optimize.result.objective_value, 4)} />
              </div>
              <ReactECharts
                style={{ height: 380 }}
                option={{
                  tooltip: { trigger: 'item', confine: true, formatter: (p: any) => `${p.name}: ${p.value}%` },
                  legend: { type: 'scroll', bottom: 0, textStyle: { color: '#888' } },
                  series: [{
                    type: 'pie',
                    radius: ['40%', '70%'],
                    data: Object.entries(optimize.result.weights)
                      .filter(([, w]) => w > 0.0001)
                      .map(([name, weight]) => ({ name, value: +(weight * 100).toFixed(2) })),
                    label: { color: '#888', formatter: '{b}: {d}%' },
                  }],
                }}
              />
              {optimize.result.message && <div className="info-row">{optimize.result.message}</div>}
            </>
          ) : null}
        </>
      )}

      {/* 蒙特卡洛 */}
      {tab === 'simulate' && simulate && !loading && (
        <>
          <div className="cards" style={{ marginBottom: 12 }}>
            <Stat label="终值均值" value={num(simulate.summary.mean_terminal)} cls={simulate.summary.mean_terminal >= 1 ? 'positive' : 'negative'} />
            <Stat label="5% 分位" value={num(simulate.summary.p05)} cls="negative" />
            <Stat label="95% 分位" value={num(simulate.summary.p95)} cls="positive" />
            <Stat label="亏损概率" value={pct(simulate.summary.prob_loss, 1)} cls="negative" />
          </div>
          <ReactECharts
            style={{ height: 400 }}
            option={{
              tooltip: { trigger: 'axis', confine: true },
              legend: { data: ['5% 分位', '中位数', '95% 分位', '示例路径'], bottom: 0, textStyle: { color: '#888' } },
              grid: { left: '3%', right: '4%', bottom: '12%', containLabel: true },
              xAxis: { type: 'category', data: simulate.timeline, axisLabel: { color: '#888' } },
              yAxis: { type: 'value', name: '净值', axisLabel: { color: '#888' } },
              series: [
                { name: '5% 分位', type: 'line', data: simulate.quantiles.p05, showSymbol: false, lineStyle: { color: '#ff6b6b', width: 1, type: 'dashed' }, itemStyle: { color: '#ff6b6b' } },
                { name: '95% 分位', type: 'line', data: simulate.quantiles.p95, showSymbol: false, lineStyle: { color: '#00c853', width: 1, type: 'dashed' }, itemStyle: { color: '#00c853' } },
                { name: '中位数', type: 'line', data: simulate.quantiles.p50, showSymbol: false, lineStyle: { color: '#00d2ff', width: 2 }, itemStyle: { color: '#00d2ff' },
                  areaStyle: { color: 'rgba(0,210,255,0.08)' } },
                ...simulate.sample_paths.map((path, i) => ({
                  name: '示例路径', type: 'line' as const, data: path, showSymbol: false,
                  lineStyle: { color: 'rgba(255,255,255,0.15)', width: 1 }, itemStyle: { color: 'rgba(255,255,255,0.15)' },
                  tooltip: { show: i === 0 },
                })),
              ],
            }}
          />
          <div className="info-row" style={{ marginTop: 8 }}>
            {simulate.summary.n_paths} 条路径 × {simulate.summary.horizon} 个交易日 · 终值以 1.0 为本金 · VaR {pct(simulate.summary.var)} / CVaR {pct(simulate.summary.cvar)}
          </div>
        </>
      )}

      {/* MPC */}
      {tab === 'mpc' && mpc && !loading && (
        <>
          <div className="cards" style={{ marginBottom: 12 }}>
            <Stat label="期末净值" value={num(mpc.summary.final_wealth)} cls={mpc.summary.total_return >= 0 ? 'positive' : 'negative'} />
            <Stat label="区间收益" value={pct(mpc.summary.total_return)} cls={mpc.summary.total_return >= 0 ? 'positive' : 'negative'} />
            <Stat label="累计双边换手" value={pct(mpc.summary.total_turnover, 1)} />
            <Stat label="交易成本" value={pct(mpc.summary.total_cost, 2)} />
          </div>
          <ReactECharts
            style={{ height: 340 }}
            option={{
              tooltip: { trigger: 'axis', confine: true },
              grid: { left: '3%', right: '4%', bottom: '8%', containLabel: true },
              xAxis: { type: 'category', data: mpc.dates.map((d) => d.slice(5)), axisLabel: { color: '#888' } },
              yAxis: { type: 'value', name: '净值', scale: true, axisLabel: { color: '#888' } },
              series: [{
                type: 'line', data: mpc.wealth, showSymbol: false, smooth: true,
                lineStyle: { color: '#00d2ff', width: 2 }, itemStyle: { color: '#00d2ff' },
                areaStyle: { color: 'rgba(0,210,255,0.08)' },
                markLine: { silent: true, data: [{ yAxis: 1, label: { formatter: '本金' } }], lineStyle: { color: '#888', type: 'dashed' } },
              }],
            }}
          />
          <div className="table-container" style={{ marginTop: 12 }}>
            <table>
              <thead><tr><th>日期</th><th>双边换手</th><th>成本</th><th>当期收益</th><th>目标权重（前 4）</th></tr></thead>
              <tbody>
                {mpc.recent_steps.slice().reverse().map((s) => (
                  <tr key={s.step}>
                    <td>{s.date}</td>
                    <td>{pct(s.turnover, 1)}</td>
                    <td>{pct(s.cost, 2)}</td>
                    <td className={s.portfolio_return >= 0 ? 'positive' : 'negative'}>{pct(s.portfolio_return)}</td>
                    <td>{Object.entries(s.weights).filter(([, w]) => w > 0.01).slice(0, 4).map(([n, w]) => `${n} ${pct(w, 0)}`).join(' / ')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
