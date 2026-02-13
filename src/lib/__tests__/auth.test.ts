import { describe, it, expect } from 'vitest';
import { hashNickname } from '../auth';

describe('hashNickname', () => {
  it('produces consistent SHA-256 hex for same input', () => {
    const a = hashNickname('purple-tiger-42');
    const b = hashNickname('purple-tiger-42');
    expect(a).toBe(b);
    expect(a).toMatch(/^[a-f0-9]{64}$/);
  });

  it('produces different hashes for different inputs', () => {
    expect(hashNickname('aaa')).not.toBe(hashNickname('bbb'));
  });

  it('normalizes input (trim + lowercase)', () => {
    expect(hashNickname('  Hello  ')).toBe(hashNickname('hello'));
  });
});
