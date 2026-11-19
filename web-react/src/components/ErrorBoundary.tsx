import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * 全局错误边界：任何子组件渲染期抛错（如 undefined.toFixed / undefined.map）
 * 都在此降级为友好提示，避免整页白屏。用户点击「重新加载」可重置边界重试。
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // 保留控制台堆栈，便于排查；生产环境用户看到的是下方友好提示。
    console.error('[Asset Lens] 组件渲染错误:', error, info.componentStack);
  }

  handleReset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    const { error } = this.state;
    if (!error) return this.props.children;

    return (
      <div
        style={{
          maxWidth: 640,
          margin: '48px auto',
          padding: 24,
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 12,
          color: 'var(--text-primary)',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: 36, marginBottom: 12 }}>⚠️</div>
        <h2 style={{ margin: '0 0 12px', fontSize: 20 }}>页面出现了一个错误</h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: 14, lineHeight: 1.7, margin: '0 0 8px' }}>
          这部分内容暂时无法显示。你可以点击下方按钮重试，或刷新整个页面。
        </p>
        <details
          style={{
            textAlign: 'left',
            margin: '16px 0',
            padding: 12,
            background: 'var(--bg-secondary)',
            borderRadius: 8,
            fontSize: 12,
            color: 'var(--text-secondary)',
          }}
        >
          <summary style={{ cursor: 'pointer' }}>错误详情</summary>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', marginTop: 8 }}>
            {error.message}
          </pre>
        </details>
        <button
          onClick={this.handleReset}
          style={{
            padding: '10px 24px',
            border: 'none',
            borderRadius: 8,
            background: 'var(--text-primary)',
            color: 'var(--bg-primary)',
            fontSize: 14,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          重新加载
        </button>
      </div>
    );
  }
}
