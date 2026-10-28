import { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { PropsWithChildren } from 'react';
import { useLocation } from 'react-router-dom';
import { getSessions, getTrackMap } from '../lib/api';
import { demoSession } from '../lib/demo';
import type { DrivingSession, TrackMap } from '../lib/types';
import { useSessionStream } from '../modules/telemetry/useSessionStream';
import { nearestBySequence } from '../lib/telemetry';

interface AppState {
  demo: boolean;
  setDemo: (value: boolean) => void;
  sessions: DrivingSession[];
  activeSession: DrivingSession | null;
  trackMap: TrackMap | null;
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
  publicMode: boolean;
  routePath: (path: string) => string;
}

const Context = createContext<AppState | null>(null);

export function AppProvider({ children }: PropsWithChildren) {
  const location = useLocation();
  const publicMode = location.pathname === '/visao-publica'
    || location.pathname.startsWith('/visao-publica/');
  const routePath = (path: string) => publicMode
    ? path === '/' ? '/visao-publica' : `/visao-publica${path}`
    : path;
  const [demo, setDemo] = useState(false);
  const [realSessions, setRealSessions] = useState<DrivingSession[]>([]);
  const [selected, setSelected] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [trackMap, setTrackMap] = useState<TrackMap | null>(null);
  const [cursorSequence, setCursor] = useState<number | null>(null);
  const [isFollowing, setFollowing] = useState(true);
  const selectionLocked = useRef(false);

  useEffect(() => {
    if (demo) return;
    const controller = new AbortController();
    setLoading(true);
    getSessions(publicMode).then((data) => {
      if (controller.signal.aborted) return;
      setRealSessions(data);
      setSelected((id) => selectionLocked.current && data.some((s) => s.stream_id === id)
        ? id : data[0]?.stream_id || '');
      setError(null);
    }).catch((e: unknown) => {
      if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Falha ao buscar sessões.');
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [demo, reloadKey, publicMode]);

  useEffect(() => {
    if (demo) return;
    const timer = window.setInterval(() => setReloadKey((value) => value + 1), 15_000);
    return () => window.clearInterval(timer);
  }, [demo, publicMode]);

  const sessions = demo ? [demoSession] : realSessions;
  const activeSession = demo ? demoSession : sessions.find((s) => s.stream_id === selected) ?? null;
  const { samples, status, error: streamError } = useSessionStream(activeSession, demo, publicMode);

  useEffect(() => {
    if (demo || !activeSession) {
      setTrackMap(null);
      return undefined;
    }
    let valid = true;
    setTrackMap(null);
    getTrackMap(activeSession.stream_id, publicMode).then((value) => {
      if (valid) setTrackMap(
        value.track_map && (
          (Array.isArray(value.track_map.points) && value.track_map.points.length >= 2)
          || Boolean(value.track_map.image_url)
        )
          ? value.track_map
          : null,
      );
    }).catch(() => {
      if (valid) setTrackMap(null);
    });
    return () => { valid = false; };
  }, [activeSession?.stream_id, activeSession?.updated_at, demo, publicMode]);

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
    trackMap,
    selectSession: (id) => {
      selectionLocked.current = true;
      setSelected(id);
      setCursor(null);
      setFollowing(true);
    },
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
    publicMode,
    routePath,
  };
  return <Context.Provider value={state}>{children}</Context.Provider>;
}

export function useApp(): AppState {
  const value = useContext(Context);
  if (!value) throw new Error('useApp deve estar sob AppProvider');
  return value;
}
