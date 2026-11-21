export interface PortfolioSummary {
  total_assets: number;
  /** 全口径总资产：资产汇总表末行「总金额」（含现金/各账户/信用卡负债） */
  total_assets_overview?: number;
  total_profit: number;
  total_return: number;
  position_count: number;
}

export interface PortfolioItem {
  name: string;
  type: string;
  current_amount: number;
  profit: number;
  profit_rate: number;
  annual_return: number;
  initial_amount: number;
}

export interface Strategy {
  name: string;
  description: string;
  buy_conditions: number;
  sell_conditions: number;
  position_size: number;
  max_positions: number;
  stop_loss: number;
  take_profit: number;
}

export interface MaturityLadder {
  as_of: string;
  buckets: MaturityBucket[];
  total_amount: number;
  open_ended_count: number;
  open_ended_amount: number;
  no_maturity_count: number;
  overdue_count: number;
  overdue_amount: number;
  overdue_share: number;
  dirty_count: number;
  dirty_amount: number;
  /** 有明确到期日的金额占比 */
  coverage: number;
  confidence: string;
}

export interface IssuerExposure {
  name: string;
  count: number;
  amount: number;
  share: number;
}

export interface MaturityBucket {
  key: string;
  label: string;
  count: number;
  amount: number;
  share: number;
}

export interface InstitutionConcentration {
  hhi: number;
  top1_name: string;
  top1_share: number;
  top3_share: number;
  exposures: IssuerExposure[];
  unattributed_count: number;
  unattributed_amount: number;
  issuer_attribution_rate: number;
  channel_hhi: number;
  channel_top1_name: string;
  channel_top1_share: number;
}

export interface DataQualityReport {
  total_count: number;
  dated_count: number;
  open_ended_count: number;
  open_ended_rate: number;
  missing_maturity_count: number;
  missing_maturity_rate: number;
  dirty_maturity_count: number;
  missing_start_date_count: number;
  missing_start_date_rate: number;
  missing_days_count: number;
  missing_days_rate: number;
  missing_annual_count: number;
  missing_annual_rate: number;
}

export interface YieldAnomaly {
  kind: string;
  name: string;
  severity: number;
  message: string;
}

export interface RiskAlert {
  kind: string;
  priority: string;
  title: string;
  detail: string;
  amount?: number;
}

export interface FixedIncomeRiskView {
  as_of: string;
  total_amount: number;
  fixed_income_count: number;
  equity_or_fund_excluded_amount: number;
  equity_exposure_count: number;
  equity_exposure_amount: number;
  equity_exposure_losing_count: number;
  rolling_amount: number;
  rolling_count: number;
  ladder: MaturityLadder;
  concentration: InstitutionConcentration;
  data_quality: DataQualityReport;
  yield_anomalies: YieldAnomaly[];
  alerts: RiskAlert[];
  note?: string;
  error?: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

// ===== 量化分析（CVaR / Markowitz / Monte Carlo / MPC）=====
export interface QuantMeta {
  source: string;
  assets: string[];
  proxies: { name: string; code: string }[];
  start_date: string;
  end_date: string;
  periods: number;
  portfolio: string;
}

export interface QuantCvarAsset {
  name: string;
  var: number;
  cvar: number;
  mean: number;
  volatility: number;
}

export interface QuantCvarResponse {
  level: number;
  assets: QuantCvarAsset[];
  portfolio: { name: string; var: number; cvar: number };
  meta: QuantMeta;
}

export interface QuantOptimizeResult {
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  /** 优化目标值；无定义（如夏普比率分母为 0）时后端返回 null。 */
  objective_value: number | null;
  cvar: number;
  success: boolean;
  message: string;
}

export interface QuantOptimizeResponse {
  objective: string;
  level: number;
  result: QuantOptimizeResult | null;
  frontier: QuantOptimizeResult[];
  meta: QuantMeta;
}

export interface QuantSimulateResponse {
  method: string;
  summary: {
    mean_terminal: number;
    median_terminal: number;
    p05: number;
    p95: number;
    var: number;
    cvar: number;
    prob_loss: number;
    horizon: number;
    n_paths: number;
  };
  timeline: number[];
  quantiles: { p05: number[]; p50: number[]; p95: number[] };
  sample_paths: number[][];
  meta: QuantMeta;
}

export interface QuantMpcStep {
  step: number;
  date: string;
  turnover: number;
  cost: number;
  portfolio_return: number;
  weights: Record<string, number>;
}

export interface QuantMpcResponse {
  dates: string[];
  wealth: number[];
  summary: {
    final_wealth: number;
    total_return: number;
    total_turnover: number;
    total_cost: number;
    n_rebalances: number;
    annualized_return: number;
  };
  recent_steps: QuantMpcStep[];
  meta: QuantMeta;
}
