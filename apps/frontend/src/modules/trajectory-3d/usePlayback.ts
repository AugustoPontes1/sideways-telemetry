import { useEffect, useRef, useState } from 'react';
import type { TelemetrySample } from '../../lib/types';
import { sampleTimeSeconds } from '../../lib/telemetry';

export function usePlayback(samples: TelemetrySample[], selectedSeq: number | null, onCursor: (seq: number) => void) {
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const frozenSamples = useRef(samples);
  const cursorRef = useRef(selectedSeq);
  cursorRef.current = selectedSeq;
  const onCursorRef = useRef(onCursor);
  onCursorRef.current = onCursor;

  useEffect(() => { setPlaying(false); }, [samples[0]?.sequence]);
  useEffect(() => { if (!playing) frozenSamples.current = samples; }, [playing, samples]);

  useEffect(() => {
    const playback = frozenSamples.current;
    if (!playing || playback.length < 2) return;
    let frame = 0;
    const current = playback.findIndex((s) => s.sequence === cursorRef.current);
    const index = current >= playback.length - 1 ? 0 : Math.max(0, current);
    const startT = sampleTimeSeconds(playback[index]);
    const clockStart = performance.now();
    const lastT = sampleTimeSeconds(playback[playback.length - 1]);
    onCursorRef.current(playback[index].sequence);
    function loop(now: number) {
      const target = startT + (now - clockStart) / 1000 * speed;
      if (target >= lastT) {
        onCursorRef.current(playback[playback.length - 1].sequence);
        setPlaying(false);
        return;
      }
// Use binary search instead of scanning the entire session on every frame.
      let lo = 0, hi = playback.length - 1;
      while (lo < hi) {
        const middle = Math.floor((lo + hi + 1) / 2);
        if (sampleTimeSeconds(playback[middle]) <= target) lo = middle;
        else hi = middle - 1;
      }
      if (playback[lo].sequence !== cursorRef.current) onCursorRef.current(playback[lo].sequence);
      frame = requestAnimationFrame(loop);
    }
    frame = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(frame);
  }, [playing, speed]);

  return { playing, setPlaying, speed, setSpeed };
}
