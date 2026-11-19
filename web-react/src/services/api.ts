import axios from 'axios';
import type {
  PortfolioSummary,
  PortfolioItem,
  Strategy,
  FixedIncomeRiskView,
  QuantCvarResponse,
  QuantOptimizeResponse,
  QuantSimulateResponse,
  QuantMpcResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// 后端 /api/portfolio/items 的字段名与前端 PortfolioItem 声明不一致：
//   investment_type -> type, profit_amount -> profit, return_rate -> profit_rate
// 在适配层统一归一化，并对数值字段兜底，避免 undefined.toFixed() 导致整页崩溃。
interface PortfolioItemRaw {
  name?: string;
  type?: string;
  investment_type?: string;
  current_amount?: number;
  profit?: number;
  profit_amount?: number;
  profit_rate?: number;
  return_rate?: number;
  annual_return?: number;
  initial_amount?: number;
}

const toFinite = (value: unknown): number => {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
};

const normalizePortfolioItem = (raw: PortfolioItemRaw): PortfolioItem => ({
  name: raw.name ?? '',
  type: raw.type ?? raw.investment_type ?? '其他',
  current_amount: toFinite(raw.current_amount),
  profit: toFinite(raw.profit ?? raw.profit_amount),
  profit_rate: toFinite(raw.profit_rate ?? raw.return_rate),
  annual_return: toFinite(raw.annual_return),
  initial_amount: toFinite(raw.initial_amount),
});

export const portfolioApi = {
  getSummary: async (): Promise<PortfolioSummary> => {
    const response = await api.get<PortfolioSummary>('/api/portfolio/summary');
    return response.data;
  },

  getItems: async (): Promise<PortfolioItem[]> => {
    const response = await api.get<{ items: PortfolioItemRaw[] }>('/api/portfolio/items');
    return (response.data.items || []).map(normalizePortfolioItem);
  },
};

export const strategyApi = {
  list: async (): Promise<Strategy[]> => {
    const response = await api.get<Strategy[]>('/api/strategies');
    return response.data;
  },
};

export const fixedIncomeApi = {
  getRiskView: async (): Promise<FixedIncomeRiskView> => {
    const response = await api.get<FixedIncomeRiskView>('/api/fixed-income/risk-view');
    return response.data;
  },
};

export const quantApi = {
  getCvar: async (level = 0.95): Promise<QuantCvarResponse> => {
    const { data } = await api.get<QuantCvarResponse>('/api/quant/cvar', { params: { level } });
    return data;
  },
  optimize: async (objective: string): Promise<QuantOptimizeResponse> => {
    const { data } = await api.get<QuantOptimizeResponse>('/api/quant/optimize', {
      params: { objective },
    });
    return data;
  },
  simulate: async (method = 'bootstrap'): Promise<QuantSimulateResponse> => {
    const { data } = await api.get<QuantSimulateResponse>('/api/quant/simulate', {
      params: { method },
      timeout: 60000,
    });
    return data;
  },
  mpc: async (): Promise<QuantMpcResponse> => {
    const { data } = await api.get<QuantMpcResponse>('/api/quant/mpc', { timeout: 60000 });
    return data;
  },
};

export const healthApi = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};
