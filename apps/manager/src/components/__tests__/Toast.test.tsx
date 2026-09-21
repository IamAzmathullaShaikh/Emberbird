import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, act } from '@testing-library/react';
import { Toast } from '../Toast';
import type { ToastNotification } from '../Toast';

const makeNotif = (overrides: Partial<ToastNotification> = {}): ToastNotification => ({
  id: 'test-1',
  type: 'info',
  title: 'Test notification',
  durationMs: 0, // 0 = no auto-dismiss in tests
  ...overrides,
});

describe('Toast', () => {
  it('renders nothing when notifications list is empty', () => {
    const { container } = render(<Toast notifications={[]} onDismiss={vi.fn()} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders a notification with its title', () => {
    render(
      <Toast
        notifications={[makeNotif({ title: 'Update successful' })]}
        onDismiss={vi.fn()}
      />
    );
    expect(screen.getByText('Update successful')).toBeInTheDocument();
  });

  it('renders the notification message when provided', () => {
    render(
      <Toast
        notifications={[makeNotif({ title: 'Error', message: 'Connection refused' })]}
        onDismiss={vi.fn()}
      />
    );
    expect(screen.getByText('Connection refused')).toBeInTheDocument();
  });

  it('calls onDismiss with the notification id when dismiss button is clicked', () => {
    const onDismiss = vi.fn();
    render(
      <Toast
        notifications={[makeNotif({ id: 'notif-abc' })]}
        onDismiss={onDismiss}
      />
    );
    fireEvent.click(screen.getByLabelText('Dismiss'));
    expect(onDismiss).toHaveBeenCalledWith('notif-abc');
  });

  it('renders at most 4 notifications', () => {
    const notifications = Array.from({ length: 6 }, (_, i) =>
      makeNotif({ id: `n-${i}`, title: `Notification ${i}` })
    );
    render(<Toast notifications={notifications} onDismiss={vi.fn()} />);
    // Only 4 visible (slice -4)
    const titles = screen.getAllByText(/Notification \d/);
    expect(titles.length).toBe(4);
  });

  it('auto-dismisses after durationMs when > 0', async () => {
    vi.useFakeTimers();
    const onDismiss = vi.fn();
    render(
      <Toast
        notifications={[makeNotif({ id: 'timed', durationMs: 1000 })]}
        onDismiss={onDismiss}
      />
    );
    expect(onDismiss).not.toHaveBeenCalled();
    act(() => {
      vi.advanceTimersByTime(1001);
    });
    expect(onDismiss).toHaveBeenCalledWith('timed');
    vi.useRealTimers();
  });
});
