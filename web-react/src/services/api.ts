import axios from 'axios';
import type { PortfolioSummary, PortfolioItem, Strategy } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export const portfolioApi = {
  getSummary: async (): Promise<PortfolioSummary> => {
    const response = await api.get<PortfolioSummary>('/api/portfolio/summary');
    return response.data;
  },

  getItems: async (): Promise<PortfolioItem[]> => {
    const response = await api.get<{ items: PortfolioItem[] }>('/api/portfolio/items');
    return response.data.items || [];
  },
};

export const strategyApi = {
  list: async (): Promise<Strategy[]> => {
    const response = await api.get<Strategy[]>('/api/strategies');
    return response.data;
  },
};

export const healthApi = {
  check: async () => {
    const response = await api.get('/health');
    return response.data;
  },
};
