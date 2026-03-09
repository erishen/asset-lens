import { useState, useEffect, useCallback } from 'react';
import { portfolioApi, strategyApi } from './services/api';
import type { PortfolioSummary, PortfolioItem, Strategy } from './types';
import { SummaryCards } from './components/SummaryCards';
import { AllocationChart } from './components/AllocationChart';
import { PortfolioTable } from './components/PortfolioTable';
import { ProfitChart } from './components/ProfitChart';
import { StrategyCards } from './components/StrategyCards';
import { StrategyChart } from './components/StrategyChart';
import { StrategyRiskChart } from './components/StrategyRiskChart';
import { RiskChart } from './components/RiskChart';
import { MarketPage } from './components/MarketPage';
import { AnalysisPage } from './components/AnalysisPage';
import { useTheme } from './context/ThemeContext';
import './App.css';

type TabType = 'overview' | 'portfolio' | 'strategies' | 'risk' | 'market' | 'analysis';

function App() {
  const [currentTab, setCurrentTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const [summary, setSummary] = useState<PortfolioSummary>({
    total_assets: 0,
    total_profit: 0,
    total_return: 0,
    position_count: 0,
  });
  const [portfolioItems, setPortfolioItems] = useState<PortfolioItem[]>([]);
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [lastUpdate, setLastUpdate] = useState('');

  const fetchData = useCallback(async () => {
    try {
      const [summaryData, strategiesData, itemsData] = await Promise.all([
        portfolioApi.getSummary(),
        strategyApi.list(),
        portfolioApi.getItems(),
      ]);

      setSummary(summaryData);
      setStrategies(strategiesData);
      setPortfolioItems(itemsData);
      setLastUpdate(new Date().toLocaleString('zh-CN'));
      setError('');
    } catch (e) {
      setError('加载数据失败: ' + (e as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await fetchData();
    } finally {
      setRefreshing(false);
    }
  };

  const switchTab = (tab: TabType) => {
    setCurrentTab(tab);
    setMobileMenuOpen(false);
  };

  const renderContent = () => {
    if (loading && currentTab !== 'market') {
      return (
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>加载数据中...</p>
        </div>
      );
    }

    if (error && currentTab !== 'market') {
      return (
        <div className="error">
          <p>{error}</p>
          <button className="refresh-btn" onClick={fetchData} style={{ marginTop: '10px' }}>
            重试
          </button>
        </div>
      );
    }

    switch (currentTab) {
      case 'overview':
        return (
          <>
            <SummaryCards
              summary={summary}
              strategyCount={strategies.length}
              lastUpdate={lastUpdate}
            />
            <AllocationChart items={portfolioItems} />
          </>
        );
      case 'portfolio':
        return (
          <>
            <PortfolioTable
              items={portfolioItems}
              onRefresh={handleRefresh}
              refreshing={refreshing}
            />
            <ProfitChart items={portfolioItems} />
          </>
        );
      case 'strategies':
        return (
          <>
            <StrategyCards strategies={strategies} />
            <StrategyChart strategies={strategies} />
            <StrategyRiskChart strategies={strategies} />
          </>
        );
      case 'risk':
        return (
          <>
            <div className="cards">
              <div className="card">
                <div className="card-title">风险评分</div>
                <div className="card-value">50</div>
                <div className="card-change">综合风险评估</div>
              </div>
              <div className="card">
                <div className="card-title">风险等级</div>
                <div className="card-value">中等</div>
                <div className="card-change">当前风险状态</div>
              </div>
            </div>
            <RiskChart />
          </>
        );
      case 'market':
        return <MarketPage />;
      case 'analysis':
        return <AnalysisPage />;
    }
  };

  return (
    <>
      <div className={`overlay ${mobileMenuOpen ? 'active' : ''}`} onClick={() => setMobileMenuOpen(false)}></div>
      <div className="container">
        <div className="header">
          <div className="header-content">
            <div>
              <h1>Asset Lens</h1>
              <p>个人资产运营系统 - React 版本</p>
            </div>
            <button className="theme-toggle" onClick={toggleTheme} title="切换主题">
              {theme === 'dark' ? '☀️' : '🌙'}
            </button>
          </div>
        </div>

        <div className="nav-wrapper">
          <button
            className={`hamburger ${mobileMenuOpen ? 'active' : ''}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
          <div className={`nav ${mobileMenuOpen ? 'mobile-open' : ''}`}>
            <button
              className={`nav-btn ${currentTab === 'overview' ? 'active' : ''}`}
              onClick={() => switchTab('overview')}
            >
              概览
            </button>
            <button
              className={`nav-btn ${currentTab === 'portfolio' ? 'active' : ''}`}
              onClick={() => switchTab('portfolio')}
            >
              投资组合
            </button>
            <button
              className={`nav-btn ${currentTab === 'strategies' ? 'active' : ''}`}
              onClick={() => switchTab('strategies')}
            >
              策略分析
            </button>
            <button
              className={`nav-btn ${currentTab === 'risk' ? 'active' : ''}`}
              onClick={() => switchTab('risk')}
            >
              风险管理
            </button>
            <button
              className={`nav-btn ${currentTab === 'market' ? 'active' : ''}`}
              onClick={() => switchTab('market')}
            >
              市场行情
            </button>
            <button
              className={`nav-btn ${currentTab === 'analysis' ? 'active' : ''}`}
              onClick={() => switchTab('analysis')}
            >
              数据分析
            </button>
          </div>
        </div>

        {renderContent()}

        <div className="footer">
          <p>Asset Lens React v1.0.0 - Personal Asset Operating System</p>
        </div>
      </div>
    </>
  );
}

export default App;
