import React from 'react';

interface ErrorBoundaryProps {
  children: React.ReactNode;
  /** Optional label for the boundary (e.g. 'Dashboard', 'Doctor') — shown in error state. */
  label?: string;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo): void {
    this.setState({ errorInfo });
    // Rule 14 (Anti-Stub): error is logged for developer diagnostics, not swallowed.
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary]', this.props.label ?? 'unknown', error, errorInfo);
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  private handleCopyDiagnostic = (): void => {
    const { error, errorInfo } = this.state;
    const text = [
      `Emberbird Manager — Error Report`,
      `Boundary: ${this.props.label ?? 'unknown'}`,
      `Time: ${new Date().toISOString()}`,
      `Error: ${error?.message ?? 'unknown'}`,
      `Stack: ${error?.stack ?? 'none'}`,
      `Component Stack: ${errorInfo?.componentStack ?? 'none'}`,
    ].join('\n');
    navigator.clipboard.writeText(text).catch(() => {/* clipboard unavailable */});
  };

  render(): React.ReactNode {
    if (!this.state.hasError) return this.props.children;

    const { error } = this.state;
    const label = this.props.label ?? 'This section';

    return (
      <div className="rounded-2xl border border-red-500/40 bg-surface-raised p-6 flex flex-col gap-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-500/15 border border-red-500/30 flex items-center justify-center flex-shrink-0">
            <span className="text-red-400 text-lg">!</span>
          </div>
          <div className="flex flex-col gap-1">
            <h3 className="text-sm font-semibold text-text-primary">
              {label} encountered an error
            </h3>
            <p className="text-xs text-text-secondary">
              {error?.message ?? 'An unexpected error occurred.'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={this.handleRetry}
            className="px-3 py-1.5 rounded-lg bg-accent text-surface-DEFAULT text-xs font-medium hover:bg-accent-hover transition-colors"
          >
            Retry
          </button>
          <button
            type="button"
            onClick={this.handleCopyDiagnostic}
            className="px-3 py-1.5 rounded-lg bg-surface-raised border border-border-DEFAULT text-xs text-text-secondary hover:text-text-primary transition-colors"
          >
            Copy Diagnostic
          </button>
        </div>
      </div>
    );
  }
}
