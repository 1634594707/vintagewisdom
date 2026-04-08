'use client';

import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('ErrorBoundary caught:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="vw-panel rounded-xl p-8 text-center">
          <div className="text-4xl">⚠️</div>
          <h2 className="vw-title mt-4 text-2xl font-semibold">出错了</h2>
          <p className="mt-2 text-sm text-[var(--text-muted)]">
            {this.state.error?.message || '未知错误'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="vw-btn-primary mt-4 px-4 py-2 text-sm"
          >
            重试
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
