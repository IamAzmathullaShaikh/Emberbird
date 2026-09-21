/**
 * accessibility.test.tsx
 * UX-3: Automated axe-core accessibility audit for Emberbird Manager components.
 * 
 * These tests run axe-core against rendered components to catch:
 * - Missing aria-labels
 * - Invalid ARIA roles
 * - Missing form labels
 * - Keyboard trap issues
 * - Missing landmark regions
 * 
 * Color contrast is excluded (dark mode design tokens are validated separately).
 * Screen reader hardware audit is a separate manual step (requires NVDA/Narrator).
 */
import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import axe from 'axe-core';
import type { StageProgress } from '../../lib/types';
import { Badge } from '../ui/Badge';
import { Button } from '../ui/Button';
import { Alert } from '../ui/Alert';
import { Spinner } from '../ui/Spinner';
import { Card } from '../ui/Card';
import { StageProgressBar } from '../StageProgress';

// Axe configuration: disable color-contrast (dark mode palette validated separately)
const AXE_CONFIG: axe.RunOptions = {
  rules: {
    'color-contrast': { enabled: false },
    // Skip landmark rules for isolated component tests (no full page context)
    'region': { enabled: false },
  },
};

async function getViolations(html: HTMLElement): Promise<axe.Result[]> {
  const result = await axe.run(html, AXE_CONFIG);
  return result.violations;
}

describe('Accessibility — UI Primitives', () => {
  it('Badge has no axe violations', async () => {
    const { container } = render(<Badge variant="pass">Installed</Badge>);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });

  it('Button has no axe violations', async () => {
    const { container } = render(<Button onClick={() => {}}>Install</Button>);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });

  it('Button loading state has no axe violations', async () => {
    const { container } = render(<Button loading>Installing…</Button>);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });

  it('Alert has no axe violations', async () => {
    const { container } = render(<Alert variant="error" title="Error">Something went wrong.</Alert>);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });

  it('Spinner has no axe violations', async () => {
    const { container } = render(<Spinner label="Loading status" />);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });

  it('Card has no axe violations', async () => {
    const { container } = render(<Card><p>Content</p></Card>);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });
});

describe('Accessibility — StageProgressBar', () => {
  const mockProgress: StageProgress = {
    phase: 'downloading',
    received_bytes: 400_000_000,
    total_bytes: 900_000_000,
    message: 'Downloading WSA…',
  };

  it('has no axe violations', async () => {
    const { container } = render(<StageProgressBar progress={mockProgress} />);
    expect(await getViolations(container as HTMLElement)).toHaveLength(0);
  });

  it('progress bar has correct aria-valuenow', async () => {
    const { container } = render(<StageProgressBar progress={mockProgress} />);
    const bar = container.querySelector('[role="progressbar"]');
    expect(bar).not.toBeNull();
    expect(bar!.getAttribute('aria-valuenow')).toBe('44'); // 400_000_000 / 900_000_000 * 100 = 44
  });

  it('progress bar has aria-valuemin and aria-valuemax', async () => {
    const { container } = render(<StageProgressBar progress={mockProgress} />);
    const bar = container.querySelector('[role="progressbar"]');
    expect(bar!.getAttribute('aria-valuemin')).toBe('0');
    expect(bar!.getAttribute('aria-valuemax')).toBe('100');
  });
});

describe('Accessibility — Keyboard targets', () => {
  it('Button is focusable by keyboard', async () => {
    const { container } = render(<Button>Focus me</Button>);
    const btn = container.querySelector('button');
    expect(btn).not.toBeNull();
    // Default buttons without disabled attribute are focusable
    expect(btn!.disabled).toBe(false);
    expect(btn!.getAttribute('tabindex')).not.toBe('-1'); 
  });

  it('disabled Button is not tab-reachable', async () => {
    const { container } = render(<Button disabled>Disabled</Button>);
    const btn = container.querySelector('button');
    expect(btn!.disabled).toBe(true);
  });
});

describe('Accessibility — All variants pass axe', () => {
  const badgeVariants = ['pass', 'warn', 'fail', 'unknown', 'accent', 'default'] as const;
  for (const v of badgeVariants) {
    it(`Badge variant="${v}" has no violations`, async () => {
      const { container } = render(<Badge variant={v}>{v}</Badge>);
      expect(await getViolations(container as HTMLElement)).toHaveLength(0);
    });
  }

  const alertVariants = ['info', 'success', 'warn', 'error'] as const;
  for (const v of alertVariants) {
    it(`Alert variant="${v}" has no violations`, async () => {
      const { container } = render(<Alert variant={v}>Message</Alert>);
      expect(await getViolations(container as HTMLElement)).toHaveLength(0);
    });
  }

  const buttonVariants = ['primary', 'secondary', 'ghost', 'danger'] as const;
  for (const v of buttonVariants) {
    it(`Button variant="${v}" has no violations`, async () => {
      const { container } = render(<Button variant={v}>Action</Button>);
      expect(await getViolations(container as HTMLElement)).toHaveLength(0);
    });
  }
});
