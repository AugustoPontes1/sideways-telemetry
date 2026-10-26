import type { ExerciseValue } from '../../lib/types';

/** Student input must be valid JSON: a number, boolean, array, or object. */
export function parseStudentAnswer(raw: string): ExerciseValue {
  const trimmed = raw.trim();
  if (!trimmed) throw new Error('Digite uma resposta.');
  try {
    return JSON.parse(trimmed) as ExerciseValue;
  } catch {
    throw new Error('Use JSON válido: 3.5, true, [2,-1] ou {"a":2,"b":-1}.');
  }
}

/** DEMO mode only. In production, answers are checked by the Django backend. */
export function compareDemoAnswer(expected: ExerciseValue, actual: ExerciseValue): boolean {
  if (typeof expected === 'number') return typeof actual === 'number' && Number.isFinite(actual) &&
    Math.abs(expected - actual) <= Math.max(.02, Math.abs(expected) * .001);
  if (Array.isArray(expected)) return Array.isArray(actual) && expected.length === actual.length &&
    expected.every((value, i) => compareDemoAnswer(value, actual[i]));
  if (expected && typeof expected === 'object') {
    if (!actual || typeof actual !== 'object' || Array.isArray(actual)) return false;
    const a = actual as Record<string, ExerciseValue>;
    return Object.keys(expected).length === Object.keys(a).length &&
      Object.entries(expected).every(([key, val]) => Object.hasOwn(a, key) && compareDemoAnswer(val, a[key]));
  }
  return expected === actual;
}

export const prettyJson = (value: ExerciseValue) =>
  typeof value === 'object' ? JSON.stringify(value, null, 2) : JSON.stringify(value);
