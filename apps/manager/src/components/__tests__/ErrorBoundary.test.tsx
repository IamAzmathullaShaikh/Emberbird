/* eslint-disable no-console */
// Intentional: ErrorBoundary tests mock console.error to suppress expected boundary output.
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { ErrorBoundary } from '../ErrorBoundary';

// A component that throws on render
const ThrowingComponent: React.FC<{ shouldThrow?: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) throw new Error('Test render error');
  return <div>All good</div>;
};

describe('ErrorBoundary', () => {
  // Suppress console.error for expected error boundary output in tests
  const originalError = console.error;
  beforeEach(() => {
    console.error = vi.fn();
  });
  afterEach(() => {
    console.error = originalError;
  });

  it('renders children when there is no error', () => {
    render(
      <ErrorBoundary label="Test">
        <div>Child content</div>
      </ErrorBoundary>
    );
    expect(screen.getByText('Child content')).toBeInTheDocument();
  });

  it('renders error state when child throws', () => {
    render(
      <ErrorBoundary label="Dashboard">
        <ThrowingComponent shouldThrow />
      </ErrorBoundary>
    );
    expect(screen.getByText('Dashboard encountered an error')).toBeInTheDocument();
    expect(screen.getByText('Test render error')).toBeInTheDocument();
  });

  it('shows Retry and Copy Diagnostic buttons when in error state', () => {
    render(
      <ErrorBoundary label="Updates">
        <ThrowingComponent shouldThrow />
      </ErrorBoundary>
    );
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /copy diagnostic/i })).toBeInTheDocument();
  });

  it('resets error state when Retry is clicked', () => {
    let localShouldThrow = true;
    const LocalThrowingComponent = () => {
      if (localShouldThrow) throw new Error('Test render error');
      return <div>All good</div>;
    };

    render(
      <ErrorBoundary label="Test">
        <LocalThrowingComponent />
      </ErrorBoundary>
    );
    // Error state shown
    expect(screen.getByText('Test encountered an error')).toBeInTheDocument();
    
    // Change the condition so the retry render succeeds
    localShouldThrow = false;
    
    // Click retry
    fireEvent.click(screen.getByRole('button', { name: /retry/i }));
    
    expect(screen.getByText('All good')).toBeInTheDocument();
  });

  it('uses generic label when no label prop is provided', () => {
    render(
      <ErrorBoundary>
        <ThrowingComponent shouldThrow />
      </ErrorBoundary>
    );
    expect(screen.getByText('This section encountered an error')).toBeInTheDocument();
  });
});
