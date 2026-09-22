/**
 * OperationsView component tests (PH-45 UI surface).
 *
 * The view renders the durable staging-operation history read-only; these
 * tests pin the empty state, the success/failed summaries, the id formatting,
 * and the expandable stage breakdown against the real zustand store.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OperationsView, formatOperationId } from '../OperationsView';
import { useEmberStore } from '../../lib/store';
import type { OperationRecord } from '../../lib/types';

vi.mock('../../lib/ipc', () => ({
  detectWsaStatus: vi.fn(),
  checkForUpdates: vi.fn(),
  getLifecycleReport: vi.fn(),
  getOperationHistory: vi.fn(),
}));

import { getOperationHistory } from '../../lib/ipc';

const SUCCESS: OperationRecord = {
  operation_id: 'STAGE-20260922-140301-a1b2c3d4',
  asset: 'WSA_2407.40000.4.0_x64_Release-Nightly.7z',
  result: 'success',
  error: null,
  started_at: '2026-09-22T14:03:01Z',
  finished_at: '2026-09-22T14:05:12Z',
  duration_ms: 131_000,
  stages: [
    { stage: 'download', started_at: '2026-09-22T14:03:01Z', duration_ms: 98_000 },
    { stage: 'verify', started_at: '2026-09-22T14:04:39Z', duration_ms: 22_000 },
  ],
  sha256: 'ab'.repeat(32),
  size_bytes: 1_610_612_736,
};

const FAILED: OperationRecord = {
  operation_id: 'STAGE-20260922-150000-deadbeef',
  asset: 'CONTROLLER.7z',
  result: 'failed',
  error: 'SHA-256 verification failed',
  started_at: '2026-09-22T15:00:00Z',
  finished_at: '2026-09-22T15:00:40Z',
  duration_ms: 40_000,
  stages: [{ stage: 'download', started_at: '2026-09-22T15:00:00Z', duration_ms: 40_000 }],
  sha256: null,
  size_bytes: 1234,
};

describe('formatOperationId', () => {
  it('renders the wire id as a human-readable stamp', () => {
    expect(formatOperationId('STAGE-20260922-140301-a1b2c3d4')).toBe(
      'STAGE 2026-09-22 14:03:01 · a1b2c3d4'
    );
  });

  it('passes through ids it does not recognize', () => {
    expect(formatOperationId('something-else')).toBe('something-else');
  });
});

describe('OperationsView', () => {
  beforeEach(() => {
    vi.mocked(getOperationHistory).mockReset();
    useEmberStore.setState({ operations: null, loadingOperations: false });
  });

  it('loads history on mount and shows the empty state when none exists', async () => {
    vi.mocked(getOperationHistory).mockResolvedValue([]);
    render(<OperationsView />);
    await waitFor(() => expect(screen.getByTestId('operations-summary')).toHaveTextContent('0 recorded · 0 failed'));
    expect(screen.getByTestId('operations-empty')).toHaveTextContent(/No operations recorded yet/);
  });

  it('renders success and failed records with counts and formatted ids', async () => {
    vi.mocked(getOperationHistory).mockResolvedValue([SUCCESS, FAILED]);
    render(<OperationsView />);
    await waitFor(() =>
      expect(screen.getByTestId('operations-summary')).toHaveTextContent('2 recorded · 1 failed')
    );
    expect(screen.getByText('STAGE 2026-09-22 14:03:01 · a1b2c3d4')).toBeInTheDocument();
    expect(screen.getByText('STAGE 2026-09-22 15:00:00 · deadbeef')).toBeInTheDocument();
    expect(screen.getByTestId('operation-result-success')).toHaveTextContent('success');
    expect(screen.getByTestId('operation-result-failed')).toHaveTextContent('failed');
  });

  it('expands a record to show stage timings and the digest', async () => {
    vi.mocked(getOperationHistory).mockResolvedValue([SUCCESS]);
    render(<OperationsView />);
    await waitFor(() => expect(screen.getByText(/STAGE 2026-09-22/)).toBeInTheDocument());
    fireEvent.click(screen.getByText(/STAGE 2026-09-22/));
    expect(screen.getByText('download: 98s')).toBeInTheDocument();
    expect(screen.getByText('verify: 22s')).toBeInTheDocument();
    expect(screen.getByText(/sha256: ab+/)).toBeInTheDocument();
  });

  it('surfaces the failure reason inside the expanded failed record', async () => {
    vi.mocked(getOperationHistory).mockResolvedValue([FAILED]);
    render(<OperationsView />);
    await waitFor(() => expect(screen.getByText(/STAGE 2026-09-22/)).toBeInTheDocument());
    fireEvent.click(screen.getByText(/STAGE 2026-09-22/));
    expect(screen.getByRole('alert')).toHaveTextContent('SHA-256 verification failed');
  });

  it('reloads from the backend when Refresh is pressed', async () => {
    vi.mocked(getOperationHistory).mockResolvedValue([]);
    render(<OperationsView />);
    await waitFor(() => expect(getOperationHistory).toHaveBeenCalledTimes(1));
    fireEvent.click(screen.getByRole('button', { name: 'Refresh' }));
    await waitFor(() => expect(getOperationHistory).toHaveBeenCalledTimes(2));
  });
});
