import { describe, it, expect } from 'vitest';
import { formatTime, clamp, randomItem } from '../lib/utils';

describe('formatTime utility', () => {
  it('formats single digit minutes and seconds correctly', () => {
    expect(formatTime(65)).toBe('01:05');
  });

  it('formats zero seconds correctly', () => {
    expect(formatTime(0)).toBe('00:00');
  });

  it('formats large values correctly', () => {
    expect(formatTime(3599)).toBe('59:59');
  });
});

describe('clamp utility', () => {
  it('clamps a value between a min and max', () => {
    expect(clamp(15, 0, 10)).toBe(10);
    expect(clamp(-5, 0, 10)).toBe(0);
    expect(clamp(5, 0, 10)).toBe(5);
  });
});

describe('randomItem utility', () => {
  it('returns an item from the array', () => {
    const array = [1, 2, 3, 4, 5];
    const item = randomItem(array);
    expect(array).toContain(item);
  });
});
