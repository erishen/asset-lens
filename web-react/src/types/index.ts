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

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}
