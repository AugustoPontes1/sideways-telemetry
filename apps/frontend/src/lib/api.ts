import type {
  AnswerCheck, DrivingSession, Exercise, ExerciseValue, LearningTopic,
  SamplesPage, SessionAnalysis, TelemetrySample, TrajectoryComparison,
} from './types';

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

/** Django usa SessionAuthentication para as APIs. Nunca envie o Bearer do agente ao navegador. */
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
    } catch { /* resposta HTML de autenticação ou proxy */ }
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

export const getSessions = () => apiFetch<DrivingSession[]>('/api/sessions/');
export const getAnalysis = (id: string) =>
  apiFetch<SessionAnalysis>(`/api/sessions/${encodeURIComponent(id)}/analysis/`);
export const getTopics = () => apiFetch<{ topics: LearningTopic[] }>('/api/learning/topics/');

export const getSamples = (id: string, after = -1, limit = 500, signal?: AbortSignal) =>
  apiFetch<SamplesPage>(
    `/api/sessions/${encodeURIComponent(id)}/samples/?after=${after}&limit=${limit}`,
    { signal },
  );

export async function getRecentSamples(
  session: DrivingSession, maxCount = 2000, signal?: AbortSignal,
): Promise<TelemetrySample[]> {
  // O endpoint atual só permite after: inicie perto de max_sequence para obter a cauda.
  let after = Math.max(-1, session.max_sequence - maxCount);
  const all: TelemetrySample[] = [];
  for (let pageNum = 0; pageNum < Math.ceil(maxCount / 500) + 2; pageNum += 1) {
    const page = await getSamples(session.stream_id, after, Math.min(500, maxCount), signal);
    all.push(...page.samples);
    if (!page.has_more || page.next_after === null || all.length >= maxCount) break;
    after = page.next_after;
  }
  return all.slice(-maxCount);
}

export const compareSessions = (id: string, refId: string) =>
  apiFetch<TrajectoryComparison>(
    `/api/sessions/${encodeURIComponent(id)}/analysis/compare/?reference=${encodeURIComponent(refId)}`,
  );

export const getExercise = (
  id: string, topic: string, a: number, b: number, reveal = false,
) => apiFetch<Exercise>(
  `/api/sessions/${encodeURIComponent(id)}/exercise/?topic=${encodeURIComponent(topic)}` +
  `&a=${a}&b=${b}${reveal ? '&reveal=1' : ''}`,
);

export const checkExercise = (
  id: string, topic: string, a: number, b: number, answer: ExerciseValue,
) => apiFetch<AnswerCheck>(`/api/sessions/${encodeURIComponent(id)}/exercise/check/`, {
  method: 'POST',
  body: JSON.stringify({ topic, a, b, answer }),
});

export function liveSocketUrl(id: string): string {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${location.host}/ws/sessions/${encodeURIComponent(id)}/live/`;
}
