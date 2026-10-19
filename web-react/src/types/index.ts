export interface PortfolioSummary {
  total_assets: number;
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
