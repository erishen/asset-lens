/** 使用说明：数据口径、量化指标含义、数据源与免责声明。 */

const CARD: React.CSSProperties = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border-color)',
  borderRadius: 16,
  padding: 24,
  marginBottom: 24,
};

const H2: React.CSSProperties = {
  fontSize: 18,
  margin: '0 0 14px',
  background: 'linear-gradient(90deg, var(--gradient-start), var(--gradient-end))',
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  backgroundClip: 'text',
};

const H3: React.CSSProperties = { fontSize: 15, margin: '0 0 8px', color: 'var(--text-primary)' };
const P: React.CSSProperties = { lineHeight: 1.8, color: 'var(--text-secondary)', margin: '8px 0', fontSize: 14 };
const LI: React.CSSProperties = { lineHeight: 1.9, color: 'var(--text-secondary)', fontSize: 14 };

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <tr>
      <td style={{ fontWeight: 600, whiteSpace: 'nowrap' }}>{label}</td>
      <td>{value}</td>
    </tr>
  );
}

const tableStyle: React.CSSProperties = { width: '100%', borderCollapse: 'collapse', fontSize: 14, lineHeight: 1.8 };

export function GuidePage() {
  return (
    <div>
      <div style={CARD}>
        <h2 style={H2}>关于 Asset Lens</h2>
        <p style={P}>
          个人资产运营与量化分析看板。数据来自本地 CSV 持仓明细与公开行情接口，
          全部计算在本机/容器内完成，不上传任何持仓数据。
        </p>
        <p style={P}>
          本页说明各页面数据的统计口径与量化指标含义，帮助正确解读图表。
        </p>
      </div>

      <div style={CARD}>
        <h2 style={H2}>数据口径</h2>
        <div className="table-container">
          <table style={tableStyle}>
            <tbody>
              <Row
                label="总资产（卡片）"
                value={<>资产汇总表最新一行的「总金额」，<b>全口径</b>：含微信/支付宝/各券商与银行卡账户、信用卡负债、黄金等。卡片副行同时列出投资市值与持仓数量。</>}
              />
              <Row label="投资市值" value={<>所有投资产品当前市值之和，仅含投资持仓，不含现金类账户。</>} />
              <Row label="持仓明细" value={<>来自最新一期 money_csv 数据目录的「投资产品」CSV，收益率/年化收益按 CSV 列计算。</>} />
              <Row label="最新数据目录" value={<>自动选择 money_csv_YYYYMMDD 中日期最新的一期（当前数据截至 2026-11-15）。</>} />
            </tbody>
          </table>
        </div>
      </div>

      <div style={CARD}>
        <h2 style={H2}>量化分析（数据分析页 → 量化分析）</h2>
        <p style={P}>
          用 8 类资产代理（沪深300 / 中证500 / 创业板指 / 黄金ETF / 国债ETF / 纳指ETF / 标普500ETF / 恒生ETF）
          的日收益率，做风险与组合分析。数据取自腾讯行情前复权日线，实时拉取、10 分钟缓存。
        </p>

        <h3 style={{ ...H3, marginTop: 18 }}>① 风险价值 VaR / CVaR</h3>
        <ul style={{ paddingLeft: 20, margin: 0 }}>
          <li style={LI}><b>VaR（风险价值）</b>：在给定置信水平（如 95%）下，单日最大可能损失。95% 置信意味着 100 个交易日里约有 5 天损失会超过该值。</li>
          <li style={LI}><b>CVaR（条件风险价值 / 期望缺口）</b>：损失超过 VaR 之后的那部分平均损失，衡量「尾部风险」，比 VaR 更保守。</li>
          <li style={LI}>面板中数值为<b>正数表示损失幅度</b>（如 2.4% 表示尾部平均亏损约 2.4%）；置信水平可在右上角切换 90% / 95% / 99%。</li>
        </ul>

        <h3 style={{ ...H3, marginTop: 18 }}>② 组合优化（Markowitz）</h3>
        <ul style={{ paddingLeft: 20, margin: 0 }}>
          <li style={LI}><b>最小方差</b>：在给定资产里使组合波动率最低。</li>
          <li style={LI}><b>最大夏普</b>：单位风险对应的超额收益最高。</li>
          <li style={LI}><b>最小 CVaR</b>：直接最小化尾部损失，对尖峰厚尾更稳健（不假设正态）。</li>
          <li style={LI}><b>有效前沿</b>：每个风险水平下的最高预期收益，横轴为日波动率、纵轴为日预期收益，悬停可见该点权重。</li>
          <li style={LI}>权重不允许做空（0~100%），结果权重之和为 100%。这些是<b>资产类别层面</b>的建议配置，非个股买卖建议。</li>
        </ul>

        <h3 style={{ ...H3, marginTop: 18 }}>③ 蒙特卡洛模拟</h3>
        <ul style={{ paddingLeft: 20, margin: 0 }}>
          <li style={LI}>从历史收益率重采样（Bootstrap，保留短期波动聚集）或按几何布朗运动（GBM）生成 1000 条未来 252 个交易日的路径，观其分布。</li>
          <li style={LI}>以 1.0 为本金：终值 &gt; 1 为盈利、&lt; 1 为亏损。「5%/95% 分位」是 90% 情形的上下边界，「中位数」是典型结果。</li>
          <li style={LI}>「亏损概率」为终值低于 1 的路径占比。模拟基于历史统计规律，<b>不是预测</b>。</li>
        </ul>

        <h3 style={{ ...H3, marginTop: 18 }}>④ MPC 滚动再平衡回测</h3>
        <ul style={{ paddingLeft: 20, margin: 0 }}>
          <li style={LI}>模型预测控制：每隔固定期数，用过去一段时间的数据重解一次最小方差组合，模拟「动态调仓」的真实过程。</li>
          <li style={LI}>净值曲线已扣除交易成本；「累计换手」与「交易成本」反映调仓频繁度与摩擦成本。</li>
          <li style={LI}>下方表格是最近几次调仓的目标权重，可与「买入持有」对比，判断调仓是否划算。</li>
        </ul>
      </div>

      <div style={CARD}>
        <h2 style={H2}>常见问题</h2>
        <div className="table-container">
          <table style={tableStyle}>
            <tbody>
              <Row label="为什么分析页是 8 类代理资产，不是我的持仓？" value={<>量化模块需要连续的历史收益率序列，而持仓 CSV 只有单期收益。故用宽基指数/ETF 代表资产类别，做配置层面的风险分析，而非逐笔持仓回测。</>} />
              <Row label="为什么模拟结果可能是亏损？" value={<>模拟区间（近一年）市场实际下跌，Bootstrap 从这段历史重采样，负收益是真实统计结果，不代表未来一定亏损。</>} />
              <Row label="数据会上传吗？" value={<>不会。行情接口仅用于拉取公开指数/ETF 历史数据；持仓 CSV 与计算结果全部留在本机。</>} />
              <Row label="K 线为什么用前复权？" value={<>前复权把分红送股还原到历史价格，避免除权当日的假跳空，更适合看长期走势。</>} />
            </tbody>
          </table>
        </div>
      </div>

      <div style={CARD}>
        <h2 style={H2}>免责声明</h2>
        <p style={P}>
          本系统所有数值与图表仅用于个人资产记录与技术演示，<b>不构成任何投资建议</b>。
          量化模型基于历史数据，存在失效风险；请以自身判断与专业意见为准，据此操作风险自负。
        </p>
      </div>
    </div>
  );
}
