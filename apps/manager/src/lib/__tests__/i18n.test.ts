import { describe, it, expect } from 'vitest';
import { t, EN_STRINGS, getLocale } from '../i18n';

describe('i18n', () => {
  it('default locale is English', () => {
    expect(getLocale()).toBe('en');
  });

  it('translates simple keys', () => {
    expect(t('nav.dashboard')).toBe('Dashboard');
    expect(t('nav.doctor')).toBe('Doctor');
  });

  it('interpolates {label} variable', () => {
    expect(t('error.boundary.title', { label: 'Updates' })).toBe('Updates encountered an error');
  });

  it('all string values are non-empty', () => {
    for (const value of Object.values(EN_STRINGS)) {
      expect((value as string).length).toBeGreaterThan(0);
    }
  });

  it('all 6 nav tabs have translation keys', () => {
    const navKeys = ['nav.dashboard', 'nav.updates', 'nav.backup', 'nav.restore', 'nav.doctor', 'nav.licenses'] as const;
    for (const key of navKeys) {
      expect(t(key).length).toBeGreaterThan(0);
    }
  });
});
