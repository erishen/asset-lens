import { useState, useMemo } from 'react';
import type { PortfolioItem } from '../types';

interface PortfolioTableProps {
  items: PortfolioItem[];
  onRefresh: () => void;
  refreshing: boolean;
}

const PAGE_SIZE = 15;

export function PortfolioTable({ items, onRefresh, refreshing }: PortfolioTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortField, setSortField] = useState<keyof PortfolioItem | null>(null);
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  const types = useMemo(() => {
    const typeSet = new Set(items.map((item) => item.type).filter(Boolean));
    return ['all', ...Array.from(typeSet)];
  }, [items]);

  const filteredItems = useMemo(() => {
    let result = [...items];

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(
        (item) =>
          item.name.toLowerCase().includes(term) ||
          item.type.toLowerCase().includes(term)
      );
    }

    if (filterType !== 'all') {
      result = result.filter((item) => item.type === filterType);
    }

    if (sortField) {
      result.sort((a, b) => {
        const aVal = a[sortField] ?? 0;
        const bVal = b[sortField] ?? 0;
        if (typeof aVal === 'number' && typeof bVal === 'number') {
          return sortOrder === 'asc' ? aVal - bVal : bVal - aVal;
        }
        return 0;
      });
    }

    return result;
  }, [items, searchTerm, filterType, sortField, sortOrder]);

  const totalPages = Math.ceil(filteredItems.length / PAGE_SIZE);

  const paginatedItems = useMemo(() => {
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredItems.slice(start, start + PAGE_SIZE);
  }, [filteredItems, currentPage]);

  const formatMoney = (value: number) => {
    if (!value) return '¥0';
    if (value >= 10000) {
      return '¥' + (value / 10000).toFixed(2) + '万';
    }
    return '¥' + value.toFixed(2);
  };

  const getTypeClass = (type: string) => {
    const typeMap: Record<string, string> = {
      A股: 'tag-stock',
      股票: 'tag-stock',
      基金: 'tag-fund',
      债券: 'tag-bond',
      现金: 'tag-cash',
      美股: 'tag-us-stock',
      港股: 'tag-hk-stock',
    };
    return typeMap[type] || 'tag';
  };

  const handleSort = (field: keyof PortfolioItem) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('desc');
    }
  };

  const exportToCSV = () => {
    const headers = ['名称', '类型', '当前金额', '收益', '收益率', '初始金额'];
    const rows = filteredItems.map((item) => [
      item.name,
      item.type,
      item.current_amount.toFixed(2),
      item.profit.toFixed(2),
      item.profit_rate.toFixed(2) + '%',
      item.initial_amount.toFixed(2),
    ]);

    const csvContent = [headers, ...rows].map((row) => row.join(',')).join('\n');
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `portfolio_${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
  };

  return (
    <div>
      <div className="toolbar">
        <div className="search-box">
          <input
            type="text"
            placeholder="搜索名称或类型..."
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="search-input"
          />
        </div>
        <div className="filter-box">
          <select
            value={filterType}
            onChange={(e) => {
              setFilterType(e.target.value);
              setCurrentPage(1);
            }}
            className="filter-select"
          >
            {types.map((type) => (
              <option key={type} value={type}>
                {type === 'all' ? '全部类型' : type}
              </option>
            ))}
          </select>
        </div>
        <button className="refresh-btn" onClick={onRefresh} disabled={refreshing}>
          🔄 {refreshing ? '刷新中...' : '刷新'}
        </button>
        <button className="export-btn" onClick={exportToCSV}>
          📥 导出 CSV
        </button>
      </div>

      <div className="stats-bar">
        <span>共 {filteredItems.length} 条记录</span>
        <span>
          总金额: {formatMoney(filteredItems.reduce((sum, item) => sum + item.current_amount, 0))}
        </span>
        <span className={filteredItems.reduce((sum, item) => sum + item.profit, 0) >= 0 ? 'positive' : 'negative'}>
          总收益: {formatMoney(filteredItems.reduce((sum, item) => sum + item.profit, 0))}
        </span>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th onClick={() => handleSort('name')} className="sortable">
                名称 {sortField === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th>类型</th>
              <th onClick={() => handleSort('current_amount')} className="sortable">
                当前金额 {sortField === 'current_amount' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('profit')} className="sortable">
                收益 {sortField === 'profit' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('profit_rate')} className="sortable">
                收益率 {sortField === 'profit_rate' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('annual_return')} className="sortable">
                年化 {sortField === 'annual_return' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedItems.map((item, idx) => (
              <tr key={`${item.name}-${idx}`}>
                <td>{item.name}</td>
                <td>
                  <span className={`tag ${getTypeClass(item.type)}`}>{item.type}</span>
                </td>
                <td>{formatMoney(item.current_amount)}</td>
                <td className={item.profit >= 0 ? 'positive' : 'negative'}>
                  {formatMoney(item.profit)}
                </td>
                <td className={item.profit_rate >= 0 ? 'positive' : 'negative'}>
                  {item.profit_rate.toFixed(2)}%
                </td>
                <td className={item.annual_return >= 0 ? 'positive' : 'negative'}>
                  {item.annual_return.toFixed(2)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {filteredItems.length > PAGE_SIZE && (
        <div className="pagination">
          <button
            className="pagination-btn"
            onClick={() => setCurrentPage((p) => p - 1)}
            disabled={currentPage === 1}
          >
            上一页
          </button>
          <span className="pagination-info">
            第 {currentPage} / {totalPages} 页 (共 {filteredItems.length} 条)
          </span>
          <button
            className="pagination-btn"
            onClick={() => setCurrentPage((p) => p + 1)}
            disabled={currentPage === totalPages}
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
}
