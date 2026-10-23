import { describe, expect, it } from 'vitest';
import { mergeSamples, normalizeFrame, nearestBySequence } from '../src/lib/telemetry';
import { demoSamples } from '../src/lib/demo';

describe('Contrato de telemetria REST + WS', () => {
  it('normaliza um sample REST', () => {
    expect(normalizeFrame(demoSamples[0])).toMatchObject({ sequence: 0 });
  });
  it('normaliza um sample WS sem sampled_at e speed_mps', () => {
    const { sampled_at: _sampled, speed_mps: _speed, ...ws } = demoSamples[0];
    const frame = normalizeFrame({ ...ws, timestamp_unix_ns: Date.parse(demoSamples[0].sampled_at) * 1e6 });
    expect(frame?.sampled_at).toBe(demoSamples[0].sampled_at);
    expect(frame?.speed_mps).toBeCloseTo(frame!.speed_kmh / 3.6);
    void _sampled; void _speed;
  });
  it('rejeita posição malformada', () => {
    expect(normalizeFrame({ ...demoSamples[0], position_world_m: [1,2] })).toBeNull();
  });
  it('deduplica usando sequence e mantém os últimos itens', () => {
    const result = mergeSamples(demoSamples.slice(0, 3), demoSamples.slice(2, 6), 4);
    expect(result.map((v) => v.sequence)).toEqual([2,3,4,5]);
  });
  it('seleciona amostra por sequência mais próxima', () => {
    expect(nearestBySequence([demoSamples[0], demoSamples[10]], 7)?.sequence).toBe(10);
  });
});
