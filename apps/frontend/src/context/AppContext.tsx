import { createContext, useContext, useEffect, useMemo, useState } from 'react';
import type { PropsWithChildren } from 'react';
import { getSessions } from '../lib/api';
import { demoSession } from '../lib/demo';
import type { DrivingSession } from '../lib/types';
import { useSessionStream } from '../modules/telemetry/useSessionStream';
import { nearestBySequence } from '../lib/telemetry';

interface AppState {
  demo: boolean;
  setDemo: (value: boolean) => void;
  sessions: DrivingSession[];
  activeSession: DrivingSession | null;
  selectSession: (id: string) => void;
  error: string | null;
  loading: boolean;
  reloadSessions: () => void;
  samples: ReturnType<typeof useSessionStream>['samples'];
  liveStatus: ReturnType<typeof useSessionStream>['status'];
  streamError: string | null;
  cursorSequence: number | null;
  cursorSample: ReturnType<typeof useSessionStream>['samples'][number] | null;
  isFollowing: boolean;
  setCursorSequence: (seq: number) => void;
  resumeLive: () => void;
}

const Context = createContext<AppState | null>(null);

export function AppProvider({ children }: PropsWithChildren) {
  const [demo, setDemo] = useState(true);
  const [realSessions, setRealSessions] = useState<DrivingSession[]>([]);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [cursorSequence, setCursor] = useState<number | null>(null);
  const [isFollowing, setFollowing] = useState(true);

  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    setLoading(true);
    getSessions().then((data) => {
      if (controller.signal.aborted) return;
      setRealSessions(data);
      setSelected((id) => data.some((s) => s.stream_id === id) ? id : data[0]?.stream_id || '');
      setError(null);
    }).catch((e: unknown) => {
      if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Falha ao buscar sessões.');
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [demo, reloadKey]);

  useEffect(() => {
    if (demo) return;
    const timer = window.setInterval(() => setReloadKey((value) => value + 1), 15_000);
    return () => window.clearInterval(timer);
  }, [demo]);

  const sessions = demo ? [demoSession] : realSessions;
  const activeSession = demo ? demoSession : sessions.find((s) => s.stream_id === selected) ?? null;
  const { samples, status, error: streamError } = useSessionStream(activeSession, demo);

  useEffect(() => { setCursor(null); setFollowing(true); }, [activeSession?.stream_id, demo]);
  const cursorSample = useMemo(
    () => nearestBySequence(samples, isFollowing ? null : cursorSequence),
    [samples, cursorSequence, isFollowing],
  );

  const state: AppState = {
    demo,
    setDemo,
    sessions,
    activeSession,
    selectSession: (id) => { setSelected(id); setCursor(null); setFollowing(true); },
    error,
    loading,
    reloadSessions: () => setReloadKey((v) => v + 1),
    samples,
    liveStatus: status,
    streamError,
    cursorSequence,
    cursorSample,
    isFollowing,
    setCursorSequence: (seq) => { setCursor(seq); setFollowing(false); },
    resumeLive: () => { setCursor(null); setFollowing(true); },
  };
  return <Context.Provider value={state}>{children}</Context.Provider>;
}

export function useApp(): AppState {
  const value = useContext(Context);
  if (!value) throw new Error('useApp deve estar sob AppProvider');
  return value;
}
