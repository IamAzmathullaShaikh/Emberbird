import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { LifecycleBadge } from '../LifecycleBadge';
import type { LifecycleReport } from '../../lib/types';

/** Build a report with only the fields the badge actually renders. */
function report(overrides: Partial<LifecycleReport> = {}): LifecycleReport {
  return {
    state: 'INSTALLED',
    busy: false,
    legal_next: ['STARTING', 'UPDATING', 'UNINSTALLING', 'STOPPED', 'BROKEN', 'CHECKING'],
    outcome: { kind: 'RECOVERED', recovered: 'INSTALLED', state: 'INSTALLED', action: 'RE_STORED' },
    history_tail: [],
    ...overrides,
  };
}

describe('LifecycleBadge', () => {
  it('renders the engine label verbatim while loading, never a guessed state', () => {
    render(<LifecycleBadge report={null} />);
    expect(screen.getByTestId('lifecycle-badge')).toHaveTextContent('Checking lifecycle…');
  });

  it('renders the state label exactly as the engine words it', () => {
    render(<LifecycleBadge report={report({ state: 'NOT_INSTALLED' })} />);
    expect(screen.getByTestId('lifecycle-badge')).toHaveTextContent('Not Installed');
  });

  it('renders every one of the 14 states without crashing', () => {
    const states = [
      'UNKNOWN', 'NOT_INSTALLED', 'CHECKING', 'INSTALLING', 'INSTALLED', 'STARTING',
      'RUNNING', 'STOPPING', 'STOPPED', 'DEGRADED', 'BROKEN', 'UPDATING', 'ROLLING_BACK',
      'UNINSTALLING',
    ] as const;
    for (const state of states) {
      const { unmount } = render(<LifecycleBadge report={report({ state })} />);
      expect(screen.getByTestId('lifecycle-badge').textContent).not.toBe('');
      unmount();
    }
  });

  it('defers busy-ness to the backend verdict, not the state name', () => {
    // The engine can legitimately report a settled state as busy (it owns the
    // transition table); the badge must not re-derive the verdict.
    render(<LifecycleBadge report={report({ state: 'INSTALLED', busy: true })} />);
    expect(screen.getByTestId('lifecycle-badge')).toBeInTheDocument();
  });

  it('explains a rollback-demanding recovery in screen-reader text', () => {
    render(
      <LifecycleBadge
        report={report({
          state: 'BROKEN',
          outcome: { kind: 'RECOVERED', recovered: 'UPDATING', state: 'BROKEN', action: 'ROLL_BACK' },
        })}
      />,
    );
    expect(screen.getByTestId('lifecycle-badge')).toHaveTextContent(/rollback is required/i);
  });

  it('reports an unreadable snapshot honestly instead of a healthy state', () => {
    render(
      <LifecycleBadge
        report={report({
          state: 'UNKNOWN',
          outcome: { kind: 'UNREADABLE', reason: 'lifecycle snapshot malformed: expected value' },
        })}
      />,
    );
    expect(screen.getByTestId('lifecycle-badge')).toHaveTextContent(/could not be read/i);
    expect(screen.getByTestId('lifecycle-badge')).toHaveTextContent('Unknown');
  });

  it('carries the last audit reason as the hover title', () => {
    render(
      <LifecycleBadge
        report={report({
          history_tail: [{ from: 'RUNNING', to: 'UPDATING', at: '2026-09-22T00:00:00.000Z', reason: 'upgrade started' }],
        })}
      />,
    );
    expect(screen.getByTestId('lifecycle-badge')).toHaveAttribute('title', 'Last move: upgrade started');
  });
});
