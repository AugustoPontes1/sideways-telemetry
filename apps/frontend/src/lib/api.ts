import type {
  AnswerCheck, DrivingSession, Exercise, ExerciseValue, LearningTopic,
  SamplesPage, SessionAnalysis, TelemetrySample, TrackMap, TrajectoryComparison,
} from './types';

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Django uses SessionAuthentication for APIs. Never send the agent's Bearer token to the browser. */
export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');
  if (options.body !== undefined) headers.set('Content-Type', 'application/json');
  const method = (options.method ?? 'GET').toUpperCase();
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const csrf = getCookie('csrftoken');
    if (csrf) headers.set('X-CSRFToken', csrf);
  }
  let response: Response;
  try {
    response = await fetch(path, {
      ...options,
      headers,
      credentials: 'same-origin',
    });
  } catch {
    throw new ApiError('Não foi possível conectar ao backend Django.', 0);
  }
  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const json = await response.json() as { detail?: string | object; error?: string };
      if (typeof json.detail === 'string') message = json.detail;
      else if (typeof json.error === 'string') message = json.error;
    } catch { /* HTML authentication or proxy response. */ }
    if ([401, 403].includes(response.status)) {
      message += ' — entre no /admin/login/ com um usuário staff.';
    }
    throw new ApiError(message, response.status);
  }
  return response.json() as Promise<T>;
}

function getCookie(name: string): string | null {
  const match = document.cookie.split('; ').find((p) => p.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : null;
}

function apiRoot(publicMode: boolean): string {
  return publicMode ? '/api/public' : '/api';
}

export const getSessions = (publicMode = false) =>
  apiFetch<DrivingSession[]>(`${apiRoot(publicMode)}/sessions/`);
export const getTrackMap = (id: string, publicMode = false) =>
  apiFetch<{ stream_id: string; track: string; track_map: TrackMap | null }>(
    `${apiRoot(publicMode)}/sessions/${encodeURIComponent(id)}/track-map/`,
  );
export const getAnalysis = (id: string, publicMode = false) =>
  apiFetch<SessionAnalysis>(`${apiRoot(publicMode)}/sessions/${encodeURIComponent(id)}/analysis/`);
export const getTopics = (publicMode = false) =>
  apiFetch<{ topics: LearningTopic[] }>(`${apiRoot(publicMode)}/learning/topics/`);

export const getSamples = (
  id: string, after = -1, limit = 500, signal?: AbortSignal, publicMode = false,
) =>
  apiFetch<SamplesPage>(
    `${apiRoot(publicMode)}/sessions/${encodeURIComponent(id)}/samples/?after=${after}&limit=${limit}`,
    { signal },
  );

export async function getRecentSamples(
  session: DrivingSession, maxCount = 2000, signal?: AbortSignal, publicMode = false,
): Promise<TelemetrySample[]> {
// The current endpoint only supports `after`; start near max_sequence to fetch the tail.
  let after = Math.max(-1, session.max_sequence - maxCount);
  const all: TelemetrySample[] = [];
  for (let pageNum = 0; pageNum < Math.ceil(maxCount / 500) + 2; pageNum += 1) {
    const page = await getSamples(session.stream_id, after, Math.min(500, maxCount), signal, publicMode);
    all.push(...page.samples);
    if (!page.has_more || page.next_after === null || all.length >= maxCount) break;
    after = page.next_after;
  }
  return all.slice(-maxCount);
}

export const compareSessions = (id: string, refId: string, publicMode = false) =>
  apiFetch<TrajectoryComparison>(
    `${apiRoot(publicMode)}/sessions/${encodeURIComponent(id)}/analysis/compare/?reference=${encodeURIComponent(refId)}`,
  );

export const getExercise = (
  id: string, topic: string, a: number, b: number, reveal = false, publicMode = false,
) => apiFetch<Exercise>(
  `${apiRoot(publicMode)}/sessions/${encodeURIComponent(id)}/exercise/?topic=${encodeURIComponent(topic)}` +
  `&a=${a}&b=${b}${reveal ? '&reveal=1' : ''}`,
);

export const checkExercise = (
  id: string, topic: string, a: number, b: number, answer: ExerciseValue, publicMode = false,
) => apiFetch<AnswerCheck>(`${apiRoot(publicMode)}/sessions/${encodeURIComponent(id)}/exercise/check/`, {
  method: 'POST',
  body: JSON.stringify({ topic, a, b, answer }),
});

export function liveSocketUrl(id: string, publicMode = false): string {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const prefix = publicMode ? '/ws/public/sessions/' : '/ws/sessions/';
  return `${proto}//${location.host}${prefix}${encodeURIComponent(id)}/live/`;
}
