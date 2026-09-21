import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StageProgressBar } from '../StageProgress';
import type { StageProgress } from '../../lib/types';

const makeProgress = (overrides: Partial<StageProgress> = {}): StageProgress => ({
  phase: 'downloading',
  received_bytes: 0,
  total_bytes: 1000,
  message: '',
  ...overrides,
});

describe('StageProgressBar', () => {
  it('renders the phase label', () => {
    render(<StageProgressBar progress={makeProgress({ phase: 'downloading' })} />);
    expect(screen.getByText('Downloading')).toBeInTheDocument();
  });

  it('renders 0% when no bytes received', () => {
    render(<StageProgressBar progress={makeProgress({ received_bytes: 0, total_bytes: 1000 })} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });

  it('renders 50% at half progress', () => {
    render(<StageProgressBar progress={makeProgress({ received_bytes: 500, total_bytes: 1000 })} />);
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('renders 100% at completion', () => {
    render(<StageProgressBar progress={makeProgress({ received_bytes: 1000, total_bytes: 1000 })} />);
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders Verifying SHA-256 label for verifying phase', () => {
    render(<StageProgressBar progress={makeProgress({ phase: 'verifying' })} />);
    expect(screen.getByText('Verifying SHA-256')).toBeInTheDocument();
  });

  it('renders Complete label for done phase', () => {
    render(<StageProgressBar progress={makeProgress({ phase: 'done', received_bytes: 1000, total_bytes: 1000 })} />);
    expect(screen.getByText('Complete')).toBeInTheDocument();
  });

  it('has progressbar role with correct aria values', () => {
    render(<StageProgressBar progress={makeProgress({ received_bytes: 750, total_bytes: 1000 })} />);
    const progressbar = screen.getByRole('progressbar');
    expect(progressbar).toHaveAttribute('aria-valuenow', '75');
    expect(progressbar).toHaveAttribute('aria-valuemin', '0');
    expect(progressbar).toHaveAttribute('aria-valuemax', '100');
  });

  it('renders message text when provided', () => {
    render(<StageProgressBar progress={makeProgress({ message: 'Connecting to CDN...' })} />);
    expect(screen.getByText('Connecting to CDN...')).toBeInTheDocument();
  });

  it('handles zero total_bytes gracefully (shows 0%)', () => {
    render(<StageProgressBar progress={makeProgress({ received_bytes: 0, total_bytes: 0 })} />);
    expect(screen.getByText('0%')).toBeInTheDocument();
  });
});
