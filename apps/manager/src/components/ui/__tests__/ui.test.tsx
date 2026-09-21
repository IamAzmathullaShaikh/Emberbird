import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge, Button, Alert, Spinner, Card } from '../index';

describe('Card', () => {
  it('renders children', () => {
    render(<Card>Content</Card>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });
  it('applies raised styles when raised=true', () => {
    const { container } = render(<Card raised>Content</Card>);
    expect(container.firstChild).toHaveClass('bg-surface-raised');
  });
});

describe('Badge', () => {
  it('renders with default variant', () => {
    render(<Badge>OK</Badge>);
    expect(screen.getByText('OK')).toBeInTheDocument();
  });
  it('renders dot when dot=true', () => {
    const { container } = render(<Badge dot>Status</Badge>);
    expect(container.querySelector('.rounded-full')).toBeInTheDocument();
  });
});

describe('Button', () => {
  it('renders children', () => {
    render(<Button>Click</Button>);
    expect(screen.getByRole('button', { name: 'Click' })).toBeInTheDocument();
  });
  it('is disabled when loading', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
  it('is disabled when disabled prop set', () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });
});

describe('Alert', () => {
  it('renders message', () => {
    render(<Alert>Something happened</Alert>);
    expect(screen.getByText('Something happened')).toBeInTheDocument();
  });
  it('renders title when provided', () => {
    render(<Alert title="Error">Detail</Alert>);
    expect(screen.getByText('Error')).toBeInTheDocument();
  });
  it('has alert role', () => {
    render(<Alert>msg</Alert>);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });
});

describe('Spinner', () => {
  it('has status role', () => {
    render(<Spinner />);
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
  it('uses custom label', () => {
    render(<Spinner label="Processing" />);
    expect(screen.getByLabelText('Processing')).toBeInTheDocument();
  });
});
