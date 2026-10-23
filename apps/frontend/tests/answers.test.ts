import { describe, expect, it } from 'vitest';
import { compareDemoAnswer, parseStudentAnswer } from '../src/modules/math-lab/answers';

describe('Respostas modo estudo', () => {
  it('aceita escalares, vetores e objetos JSON', () => {
    expect(parseStudentAnswer('3.5')).toBe(3.5);
    expect(parseStudentAnswer('[2,-1]')).toEqual([2, -1]);
    expect(parseStudentAnswer('{"a":2,"b":-1}')).toEqual({ a: 2, b: -1 });
  });
  it('rejeita entrada que não é JSON', () => {
    expect(() => parseStudentAnswer('2,5')).toThrow();
  });
  it('compara estruturas com tolerância só no demo', () => {
    expect(compareDemoAnswer({ a: 2.005, b: [1, true] }, { a: 2, b: [1, true] })).toBe(true);
    expect(compareDemoAnswer({ is_subspace: false }, { is_subspace: true })).toBe(false);
  });
});
