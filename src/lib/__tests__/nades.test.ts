import { describe, it, expect } from 'vitest';
import { seededShuffle, getMapsPresent } from '../nades';
import type { Nade } from '../nades';

describe('seededShuffle', () => {
  it('produces consistent output for same seed', () => {
    const arr = [1, 2, 3, 4, 5];
    const a = seededShuffle(arr, 42);
    const b = seededShuffle(arr, 42);
    expect(a).toEqual(b);
  });

  it('does not mutate original array', () => {
    const arr = [1, 2, 3];
    seededShuffle(arr, 1);
    expect(arr).toEqual([1, 2, 3]);
  });
});

describe('getMapsPresent', () => {
  it('returns maps in canonical order', () => {
    const nades = [
      { map: 'nuke' }, { map: 'mirage' }, { map: 'dust2' },
    ] as Nade[];
    expect(getMapsPresent(nades)).toEqual(['mirage', 'dust2', 'nuke']);
  });
});
