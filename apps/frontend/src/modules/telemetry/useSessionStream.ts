import { useEffect, useRef, useState } from 'react';
import { getRecentSamples, getSamples, liveSocketUrl } from '../../lib/api';
import { demoSamples } from '../../lib/demo';
import { MAX_SAMPLES_IN_MEMORY, mergeSamples, normalizeFrame } from '../../lib/telemetry';
import type { DrivingSession, LiveMessage, LiveStatus, TelemetrySample } from '../../lib/types';

interface StreamResult {
  samples: TelemetrySample[];
  status: LiveStatus;
  error: string | null;
}

/** REST for history + WS for deltas + periodic reconciliation after packet loss. */
export function useSessionStream(session: DrivingSession | null, demo: boolean): StreamResult {
  const [samples, setSamples] = useState<TelemetrySample[]>(demo ? demoSamples : []);
  const [status, setStatus] = useState<LiveStatus>(demo ? 'demo' : 'offline');
  const [error, setError] = useState<string | null>(null);
  const latestSeq = useRef(-1);
  const reconciledSeq = useRef(-1);
  const streamId = session?.stream_id || '';

  useEffect(() => {
    if (demo) {
      setSamples(demoSamples);
      setStatus('demo');
      setError(null);
      latestSeq.current = demoSamples.at(-1)?.sequence ?? -1;
      reconciledSeq.current = latestSeq.current;
      return;
    }
    setSamples([]);
    setError(null);
    latestSeq.current = -1;
    reconciledSeq.current = -1;
    if (!session) {
      setStatus('offline');
      return;
    }

    let cancelled = false;
    let socket: WebSocket | null = null;
    let reconnectTimer: number | undefined;
    let reconnects = 0;
    let historyLoaded = false;
    let catchUpInFlight: Promise<void> | null = null;
    const lastDataAt = { value: 0 };
    const controller = new AbortController();
    setStatus('connecting');
    const ingest = (items: TelemetrySample[]) => {
      if (cancelled || !items.length) return;
      lastDataAt.value = Date.now();
      setError(null);
      latestSeq.current = Math.max(latestSeq.current, ...items.map((v) => v.sequence));
      setSamples((old) => mergeSamples(old, items));
    };
    const catchUp = (): Promise<void> => {
      if (cancelled) return Promise.resolve();
      if (catchUpInFlight) return catchUpInFlight;
      catchUpInFlight = (async () => {
        try {
// On initial reads, capture the most recent window of the session.
          if (!historyLoaded) {
            const items = await getRecentSamples(session, MAX_SAMPLES_IN_MEMORY, controller.signal);
            ingest(items);
            reconciledSeq.current = items.at(-1)?.sequence ?? session.max_sequence;
            historyLoaded = true;
          } else {
// Reconcile from the last REST-confirmed sequence so lost WebSocket packets are recovered.
            for (let p = 0; p < 6 && !cancelled; p += 1) {
              const page = await getSamples(streamId, reconciledSeq.current, 500, controller.signal);
              const items = page.samples.map(normalizeFrame).filter((s): s is TelemetrySample => s !== null);
              ingest(items);
              if (items.length === 0) break;
              reconciledSeq.current = page.next_after ?? items.at(-1)!.sequence;
              if (!page.has_more) break;
            }
          }
        } catch (exc) {
          if (!cancelled) setError(exc instanceof Error ? exc.message : 'Falha ao recuperar telemetria.');
        }
      })().finally(() => { catchUpInFlight = null; });
      return catchUpInFlight;
    };
    const connect = () => {
      if (cancelled) return;
      socket = new WebSocket(liveSocketUrl(streamId));
      socket.onopen = () => {
        reconnects = 0;
        setStatus('connected');
        setError(null);
        void catchUp();
      };
      socket.onmessage = (event) => {
        try {
          const msg: unknown = JSON.parse(event.data as string);
          const data = msg as Partial<LiveMessage>;
          if (data?.type !== 'telemetry.samples' || data.stream_id !== streamId || !Array.isArray(data.samples)) return;
          ingest(data.samples.map(normalizeFrame).filter((s): s is TelemetrySample => s !== null));
        } catch { /* Ignore invalid messages. */ }
      };
      socket.onclose = (event) => {
        if (cancelled) return;
        setStatus('reconnecting');
        if ([4403, 4404].includes(event.code)) {
          setStatus('offline');
          setError('WebSocket não autorizado ou sessão indisponível. Faça login no Django.');
          return;
        }
        const delay = Math.min(10_000, 800 * Math.pow(2, Math.min(reconnects++, 4)));
        reconnectTimer = window.setTimeout(connect, delay);
      };
      socket.onerror = () => { setError('Conexão ao vivo indisponível. Os dados históricos continuam acessíveis.'); };
    };
    void catchUp().finally(() => { if (!cancelled) connect(); });
    const interval = window.setInterval(() => { void catchUp(); }, 12_000);
    const staleInterval = window.setInterval(() => {
      if (!cancelled && historyLoaded && lastDataAt.value > 0 && Date.now() - lastDataAt.value > 7_000) {
        setError('Conexão aberta, mas nenhuma amostra nova chegou nos últimos segundos.');
      }
    }, 5_000);
    return () => {
      cancelled = true;
      controller.abort();
      window.clearInterval(interval);
      window.clearInterval(staleInterval);
      if (reconnectTimer !== undefined) window.clearTimeout(reconnectTimer);
      if (socket) {
        socket.onclose = null;
        socket.close();
      }
    };
// Reopen only when the session changes; metadata refreshes do not require closing the socket.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streamId, demo]);

  return { samples, status, error };
}
