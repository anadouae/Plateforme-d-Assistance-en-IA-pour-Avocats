import { getTranslations } from "@/lib/i18n/translations";

/** Base API — same-origin on lexhub (Caddy /api), localhost only in vrai dev PC. */
export function getApiBase(): string {
  const env = (process.env.NEXT_PUBLIC_API_URL || "").trim().replace(/\/$/, "");
  if (typeof window !== "undefined") {
    const { hostname, origin } = window.location;
    if (hostname === "lexhub.space" || hostname === "www.lexhub.space") {
      return origin;
    }
    if (hostname === "localhost" || hostname === "127.0.0.1") {
      return env || "http://localhost:8001";
    }
    // Autre domaine déployé avec reverse-proxy /api
    if (!env || /localhost|127\.0\.0\.1/.test(env)) {
      return origin;
    }
    return env;
  }
  return env || "http://localhost:8001";
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public payload?: Record<string, unknown> | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiMsg(
  key: "timeout" | "unreachable" | "serverError" | "uploadTimeout" | "transcribeTimeout" | "joinPending",
): string {
  return getTranslations(getClientLocale()).app.api[key];
}

function isTimeoutError(e: unknown): boolean {
  if (!(e instanceof Error) && !(e instanceof DOMException)) return false;
  const name = (e as Error).name || "";
  const msg = (e as Error).message || "";
  return (
    name === "TimeoutError" ||
    name === "AbortError" ||
    /timeout|aborted|timed out/i.test(msg)
  );
}

function parseApiDetail(detail: unknown, fallback: string): { message: string; payload?: Record<string, unknown> } {
  if (detail && typeof detail === "object" && !Array.isArray(detail)) {
    const msg =
      typeof (detail as { message?: string }).message === "string"
        ? (detail as { message: string }).message
        : fallback;
    return { message: humanizeApiDetail(msg), payload: detail as Record<string, unknown> };
  }
  const raw =
    typeof detail === "string"
      ? detail
      : Array.isArray(detail)
        ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
        : fallback;
  return { message: humanizeApiDetail(raw || fallback) };
}

/** Retire jargon ops / stack pour affichage avocat. */
function humanizeApiDetail(raw: string): string {
  const t = (raw || "").trim();
  if (!t) return apiMsg("serverError");
  // Jamais afficher « Erreur serveur » / Internal Server Error / 500 brut
  if (
    /erreur\s*(de\s*)?serveur|error\s*server|internal\s*server\s*error|server\s*error|http\s*500|status\s*500/i.test(
      t,
    )
  ) {
    return apiMsg("serverError");
  }
  // Limite technique trop courte (ex. ancien brief_jurisdiction 80 car.)
  const maxLen = /(?:at most|max(?:imum)?(?: length)?(?: of)?|au plus)\s*(\d+)\s*characters?/i.exec(t)
    || /String should have at most (\d+) characters/i.exec(t);
  if (maxLen) {
    return `Un champ est trop long (max. ${maxLen[1]} caractères). Raccourcissez le texte ou rechargez la page (Ctrl+F5).`;
  }
  if (
    /traceback|sqlalchemy|psycopg|internal server error|exception:|at 0x|WHISPER_ENABLED|ffmpeg|celery\.|localhost:\d+|port\s*8001|TypeError|ValueError|KeyError|erreur\s*(de\s*)?serveur/i.test(
      t,
    )
  ) {
    return apiMsg("serverError");
  }
  // Anciens messages backend encore techniques
  if (/\bWhisper\b/i.test(t) && /désactiv|indispon|modèle|enabled|non install|غير محمّل/i.test(t)) {
    return apiMsg("serverError");
  }
  if (t === "JOIN_PENDING" || /قيد المراجعة/.test(t)) {
    return apiMsg("joinPending");
  }
  if (/BadZipFile|zipfile|not a zip/i.test(t)) {
    return "Fichier Word/PDF endommagé ou invalide — téléchargez l’original ou réuploadez une copie saine.";
  }
  if (/plafond ia journalier|limite ia du jour|ai daily|crédits aujourd’hui/i.test(t)) {
    // Texte legacy ; le flux normal utilise DAILY_CAP_CHOICE (popup choix).
    return (
      "Plafond IA du jour atteint. Vous pouvez attendre demain ou continuer " +
      "(crédits du mois toujours débités). Ce n’est pas un impayé."
    );
  }
  return t.length > 280 ? `${t.slice(0, 277)}…` : t;
}

/** Callback UI : popup « attendre demain / continuer » pour le plafond du jour. */
type DailyOverageHandler = (info: {
  message: string;
  dailyLimit: number | null;
  dailyUsed: number | null;
  isTrial?: boolean | null;
  planName?: string | null;
}) => Promise<boolean>;

let dailyOverageHandler: DailyOverageHandler | null = null;

export function setDailyOverageHandler(handler: DailyOverageHandler | null) {
  dailyOverageHandler = handler;
}

function dailyOverageStorageKey(): string {
  const d = new Date();
  const y = d.getUTCFullYear();
  const m = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  return `lexhub_daily_overage_ack_${y}${m}${day}`;
}

export function hasDailyOverageAck(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return sessionStorage.getItem(dailyOverageStorageKey()) === "1";
  } catch {
    return false;
  }
}

export function setDailyOverageAck(ack: boolean) {
  if (typeof window === "undefined") return;
  try {
    if (ack) sessionStorage.setItem(dailyOverageStorageKey(), "1");
    else sessionStorage.removeItem(dailyOverageStorageKey());
  } catch {
    /* ignore */
  }
}

function withDailyOverageHeader(headers: HeadersInit): HeadersInit {
  if (!hasDailyOverageAck()) return headers;
  const h = { ...(headers as Record<string, string>) };
  h["X-LexHub-Daily-Overage"] = "1";
  return h;
}

/** Quota mensuel / essai épuisé → modal de guidance (pas un retry). */
type QuotaExhaustedHandler = (info: {
  code: string;
  message: string;
  actions: string[];
  trial: boolean;
  trialEndsLabel?: string | null;
}) => void | Promise<void>;

let quotaExhaustedHandler: QuotaExhaustedHandler | null = null;

export function setQuotaExhaustedHandler(handler: QuotaExhaustedHandler | null) {
  quotaExhaustedHandler = handler;
}

const QUOTA_GUIDANCE_CODES = new Set([
  "trial_quota_reached",
  "credits_exhausted",
  "product_quota_reached",
]);

async function maybeShowQuotaGuidance(payload: Record<string, unknown> | undefined, message: string) {
  if (!payload || !quotaExhaustedHandler) return;
  const code = typeof payload.code === "string" ? payload.code : "";
  if (!QUOTA_GUIDANCE_CODES.has(code)) return;
  const actions = Array.isArray(payload.actions)
    ? payload.actions.filter((a): a is string => typeof a === "string")
    : [];
  await quotaExhaustedHandler({
    code,
    message,
    actions,
    trial: Boolean(payload.trial) || code === "trial_quota_reached",
    trialEndsLabel:
      typeof payload.trial_ends_label === "string" ? payload.trial_ends_label : null,
  });
}

function activeTokenStorage(): Storage {
  const remember =
    (localStorage.getItem("lexhub_remember") ?? localStorage.getItem("sanad_remember")) !== "0";
  return remember ? localStorage : sessionStorage;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    sessionStorage.getItem("lexhub_token") ||
    localStorage.getItem("lexhub_token") ||
    sessionStorage.getItem("sanad_token") ||
    localStorage.getItem("sanad_token")
  );
}

/** Token JWT courant (session ou local) — pour fetch hors `request()`. */
export function getAuthToken(): string | null {
  return getToken();
}

function getRefreshToken(): string | null {
  // Refresh = cookie HttpOnly uniquement (plus de stockage JS)
  return null;
}

function persistTokens(data: AuthResponse) {
  const storage = activeTokenStorage();
  for (const k of ["lexhub_token", "sanad_token", "lexhub_refresh_token", "sanad_refresh_token"]) {
    localStorage.removeItem(k);
    sessionStorage.removeItem(k);
  }
  storage.setItem("lexhub_token", data.access_token);
  window.dispatchEvent(new CustomEvent("lexhub-auth-updated", { detail: data }));
  window.dispatchEvent(new CustomEvent("sanad-auth-updated", { detail: data }));
}

function clearSession() {
  for (const k of ["lexhub_token", "sanad_token", "lexhub_refresh_token", "sanad_refresh_token"]) {
    localStorage.removeItem(k);
    sessionStorage.removeItem(k);
  }
  void fetch(`${getApiBase()}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }).catch(() => {});
  window.dispatchEvent(new CustomEvent("lexhub-auth-cleared"));
  window.dispatchEvent(new CustomEvent("sanad-auth-cleared"));
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${getApiBase()}/api/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({}),
          signal: AbortSignal.timeout(20_000),
        });
        if (!res.ok) return null;
        const data = (await res.json()) as AuthResponse;
        persistTokens(data);
        return data.access_token;
      } catch {
        return null;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

async function handleUnauthorized(): Promise<string | null> {
  const newToken = await refreshAccessToken();
  if (newToken) return newToken;
  clearSession();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
    window.location.href = "/login?expired=1";
  }
  return null;
}

export type AppLocale = "fr" | "ar";

export function getClientLocale(): AppLocale {
  if (typeof window === "undefined") return "fr";
  try {
    const raw =
      localStorage.getItem("lexhub-locale-v1") ||
      localStorage.getItem("sanad-locale-v3") ||
      localStorage.getItem("sanad-locale-v2") ||
      localStorage.getItem("sanad-locale");
    if (!raw) return "fr";
    const parsed = JSON.parse(raw) as { state?: { locale?: string } };
    const locale = parsed.state?.locale;
    if (locale === "ar") return "ar";
    if (locale === "fr") return "fr";
  } catch {
    /* ignore */
  }
  return "fr";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retried = false,
  timeoutMs = 60_000,
  timeoutRetried = false,
  dailyRetried = false,
): Promise<T> {
  const token = getToken();
  const method = (options.method || "GET").toUpperCase();
  const headers: HeadersInit = withDailyOverageHeader({
    ...(options.headers || {}),
  });
  // Éviter Content-Type JSON sur DELETE/GET sans body (préflight / fetch fragiles)
  if (method !== "GET" && method !== "HEAD" && method !== "DELETE") {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  } else if (options.body) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }
  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  let res: Response;
  try {
    const signal = options.signal ?? AbortSignal.timeout(timeoutMs);
    res = await fetch(`${getApiBase()}${path}`, {
      ...options,
      headers,
      signal,
      credentials: "include",
    });
  } catch (e) {
    // Un seul nouvel essai automatique sur timeout (réseaux / cold start Docker)
    if (isTimeoutError(e) && !timeoutRetried && !options.signal) {
      return request<T>(path, options, retried, Math.min(timeoutMs + 20_000, 90_000), true, dailyRetried);
    }
    if (isTimeoutError(e)) {
      throw new ApiError(apiMsg("timeout"), 0);
    }
    throw new ApiError(apiMsg("unreachable"), 0);
  }

  if (res.status === 401 && !retried && path !== "/api/auth/refresh") {
    const newToken = await handleUnauthorized();
    if (newToken) {
      return request<T>(path, options, true, timeoutMs, timeoutRetried, dailyRetried);
    }
  }

  if (!res.ok) {
    // Un nouvel essai automatique sur 502/503/504 (redémarrage conteneur / surcharge)
    if (
      !retried &&
      !timeoutRetried &&
      (res.status === 502 || res.status === 503 || res.status === 504)
    ) {
      await new Promise((r) => setTimeout(r, 600));
      return request<T>(path, options, true, timeoutMs, timeoutRetried, dailyRetried);
    }
    const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
    const parsed = parseApiDetail(body.detail, apiMsg("serverError"));
    const code = parsed.payload && typeof parsed.payload.code === "string" ? parsed.payload.code : "";
    if (
      res.status === 429 &&
      code === "DAILY_CAP_CHOICE" &&
      !dailyRetried &&
      dailyOverageHandler
    ) {
      const ok = await dailyOverageHandler({
        message: parsed.message,
        dailyLimit:
          typeof parsed.payload?.daily_limit === "number" ? parsed.payload.daily_limit : null,
        dailyUsed:
          typeof parsed.payload?.daily_used === "number" ? parsed.payload.daily_used : null,
        isTrial:
          typeof parsed.payload?.is_trial === "boolean" ? parsed.payload.is_trial : null,
        planName:
          typeof parsed.payload?.plan_name === "string" ? parsed.payload.plan_name : null,
      });
      if (ok) {
        setDailyOverageAck(true);
        return request<T>(path, options, retried, timeoutMs, timeoutRetried, true);
      }
    }
    if (res.status === 402 && parsed.payload) {
      await maybeShowQuotaGuidance(parsed.payload, parsed.message);
    }
    throw new ApiError(parsed.message, res.status, parsed.payload ?? null);
  }
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  if (!text) return undefined as T;
  try {
    return JSON.parse(text) as T;
  } catch {
    return undefined as T;
  }
}

async function uploadRequest<T>(
  path: string,
  formData: FormData,
  retried = false,
  timeoutMs = 45_000,
  timeoutKey: "uploadTimeout" | "transcribeTimeout" = "uploadTimeout",
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  let res: Response;
  try {
    res = await fetch(`${getApiBase()}${path}`, {
      method: "POST",
      headers,
      body: formData,
      credentials: "include",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (e) {
    if (isTimeoutError(e)) {
      throw new ApiError(apiMsg(timeoutKey), 0);
    }
    throw new ApiError(apiMsg("unreachable"), 0);
  }

  if (res.status === 401 && !retried) {
    const newToken = await handleUnauthorized();
    if (newToken) {
      return uploadRequest<T>(path, formData, true, timeoutMs, timeoutKey);
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
    const detail = body.detail;
    const raw =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
          : apiMsg("serverError");
    throw new ApiError(humanizeApiDetail(raw || apiMsg("serverError")), res.status);
  }
  return res.json();
}

export const api = {
  /** JWT courant (sessionStorage prioritaire). */
  getAuthToken,
  requestRegisterOtp: (email: string) =>
    request<{ message: string }>("/api/auth/request-register-otp", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  verifyRegisterOtp: (email: string, code: string) =>
    request<{ message: string }>("/api/auth/verify-register-otp", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),

  register: (data: RegisterPayload) =>
    request<AuthResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginPayload) =>
    request<AuthResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  setPassword: (password: string) =>
    request<AuthUser>("/api/auth/set-password", {
      method: "POST",
      body: JSON.stringify({ password }),
    }),

  requestPasswordlessOtp: (email: string) =>
    request<{ message: string }>("/api/auth/request-passwordless-otp", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  loginPasswordless: (data: { email: string; code: string; captcha_token?: string }) =>
    request<AuthResponse>("/api/auth/login-passwordless", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  googleLogin: (id_token: string) =>
    request<AuthResponse>("/api/auth/google", {
      method: "POST",
      body: JSON.stringify({ id_token }),
    }),

  setup2fa: () => request<TwoFactorSetup>("/api/auth/2fa/setup"),

  enable2fa: (code: string) =>
    request<{ message: string; recovery_codes: string[] }>("/api/auth/2fa/enable", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),

  disable2fa: (code: string) =>
    request<{ message: string }>("/api/auth/2fa/disable", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),

  getMe: () => request<AuthUser>("/api/auth/me"),

  completeOnboardingTour: () =>
    request<AuthUser>("/api/auth/onboarding-tour/complete", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  getCaptchaConfig: () =>
    request<{ enabled: boolean; site_key: string; after_failures: number }>(
      "/api/auth/captcha-config",
    ),

  logout: () =>
    request<{ message: string }>("/api/auth/logout", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  /** Révoque toutes les sessions (tous appareils). */
  logoutAll: () =>
    request<{ message: string }>("/api/auth/logout-all", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  refreshToken: (refresh_token: string) =>
    request<AuthResponse>("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  forgotPassword: (email: string) =>
    request<{ message: string }>("/api/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, new_password: string) =>
    request<{ message: string }>("/api/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    }),

  updateCabinetStatus: (id: string, status: "active" | "suspended") =>
    request<{ message: string }>(`/api/admin/cabinets/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  deleteAdminCabinet: (id: string, confirmation = "SUPPRIMER") =>
    request<{ message: string }>(`/api/admin/cabinets/${id}/purge`, {
      method: "POST",
      body: JSON.stringify({ confirmation }),
    }),

  getAdminCabinetDetail: (id: string) =>
    request<AdminCabinetDetail>(`/api/admin/cabinets/${id}`),

  updateAdminUserStatus: (userId: string, is_active: boolean) =>
    request<{ message: string }>(`/api/admin/users/${userId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active }),
    }),

  getCases: () => request<CaseListItem[]>("/api/cases", {}, false, 20_000),

  createCase: (data: CreateCasePayload) =>
    request<CaseDetail>("/api/cases", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCase: (id: string) => request<CaseDetail>(`/api/cases/${id}`, {}, false, 20_000),

  updateCase: (
    id: string,
    data: Partial<{
      title: string;
      client_name: string;
      case_type: string;
      status: string;
      description: string;
      tags: string[];
      jurisdiction_degree: string;
      tribunal: string;
      court_city: string;
      court_file_number: string;
      judge_name: string;
      chamber: string;
      greffe: string;
      procedure_status: string;
      assistant_id: string | null;
      last_decision_type: string;
      last_decision_date: string | null;
      notification_date: string | null;
      appeal_deadline_at: string | null;
      appeal_deadline_days: number | null;
      client_role: string;
      client_quality: string;
      client_domicile: string;
      opposing_name: string;
      opposing_role: string;
      opposing_quality: string;
      opposing_domicile: string;
    }>,
  ) =>
    request<CaseDetail>(`/api/cases/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),


  deleteCase: (id: string) =>
    request<void>(`/api/cases/${id}`, { method: "DELETE" }),

  analyseCase: (id: string, language?: AppLocale) =>
    request<CaseAnalysisResult>(
      `/api/cases/${id}/analyse?lang=${language || getClientLocale()}`,
      { method: "POST" },
      false,
      90_000,
    ),

  getDocuments: (caseId?: string) =>
    request<DocumentItem[]>(
      caseId ? `/api/documents?case_id=${caseId}` : "/api/documents",
    ),

  getDocument: (id: string) => request<DocumentDetail>(`/api/documents/${id}`),

  uploadDocument: (caseId: string, file: File) => {
    const form = new FormData();
    form.append("case_id", caseId);
    form.append("file", file);
    return uploadRequest<DocumentItem>("/api/documents/upload", form);
  },

  deleteDocument: (id: string) =>
    request<void>(`/api/documents/${id}`, { method: "DELETE" }, false, 45_000),

  updateDocumentMeta: (
    docId: string,
    data: Partial<{
      inventory_number: number | null;
      exhibit_type: string | null;
      produced_by: string | null;
      exhibit_version: string | null;
      cited_in_plea: string | null;
    }>,
  ) =>
    request<DocumentItem>(`/api/documents/${docId}/meta`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  exportBordereau: async (caseId: string) => {
    const token = getToken();
    const res = await fetch(
      `${getApiBase()}/api/documents/bordereau/${encodeURIComponent(caseId)}`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include",
        signal: AbortSignal.timeout(60_000),
      },
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
      const raw = typeof body.detail === "string" ? body.detail : apiMsg("serverError");
      throw new ApiError(humanizeApiDetail(raw), res.status);
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/i.exec(cd);
    const name = match?.[1] || `bordereau-${caseId}.txt`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  },

  downloadDocument: async (
    id: string,
    filename = "document",
    onProgress?: (pct: number) => void,
  ) => {
    const token = getToken();
    const res = await fetch(`${getApiBase()}/api/documents/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
      signal: AbortSignal.timeout(120_000),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
      const detail = body.detail;
      const raw =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
            : apiMsg("serverError");
      throw new ApiError(humanizeApiDetail(raw || apiMsg("serverError")), res.status);
    }
    const total = Number(res.headers.get("Content-Length") || 0);
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename\*=UTF-8''([^;]+)|filename="?([^"]+)"?/i.exec(cd);
    let name = filename;
    try {
      name = decodeURIComponent(match?.[1] || match?.[2] || filename);
    } catch {
      name = match?.[2] || filename;
    }

    let blob: Blob;
    if (res.body && total > 0) {
      const reader = res.body.getReader();
      const chunks: Uint8Array[] = [];
      let received = 0;
      onProgress?.(0);
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        if (value) {
          chunks.push(value);
          received += value.length;
          onProgress?.(Math.min(99, Math.round((received / total) * 100)));
        }
      }
      blob = new Blob(chunks as BlobPart[]);
      onProgress?.(100);
    } else {
      onProgress?.(30);
      blob = await res.blob();
      onProgress?.(100);
    }

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    try {
      a.download = decodeURIComponent(name);
    } catch {
      a.download = name;
    }
    a.rel = "noopener";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  },

  fetchDocumentBlob: async (id: string, filename = "document") => {
    const token = getToken();
    const res = await fetch(`${getApiBase()}/api/documents/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
      signal: AbortSignal.timeout(120_000),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
      const detail = body.detail;
      const raw =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((d: { msg?: string }) => d.msg).filter(Boolean).join(", ")
            : apiMsg("serverError");
      throw new ApiError(humanizeApiDetail(raw || apiMsg("serverError")), res.status);
    }
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename\*=UTF-8''([^;]+)|filename="?([^"]+)"?/i.exec(cd);
    const name = decodeURIComponent(match?.[1] || match?.[2] || filename);
    const blob = await res.blob();
    return { blob, filename: name, mimeType: blob.type || "" };
  },

  reextractDocument: (id: string) =>
    request<DocumentDetail>(`/api/documents/${id}/reextract`, { method: "POST" }),

  getSynthesis: (id: string, language?: AppLocale) =>
    request<SynthesisResult>(
      `/api/documents/${id}/synthese?lang=${language || getClientLocale()}`,
      {},
      false,
      90_000,
    ),

  askDocument: (
    id: string,
    question: string,
    language?: AppLocale,
    history?: { role: string; content: string }[],
  ) =>
    request<AIResult>(`/api/documents/${id}/ask`, {
      method: "POST",
      body: JSON.stringify({
        question,
        language: language || getClientLocale(),
        ...(history && history.length ? { history } : {}),
      }),
    }),

  /** Résumé planning (agenda) pour le dashboard */
  getWorkspaceSummary: () =>
    request<WorkspaceSummary>("/api/workspace/summary"),


  getAgenda: (caseId?: string) => {
    const qs = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    return request<AgendaEventItem[]>(`/api/workspace/agenda${qs}`);
  },

  createAgendaEvent: (data: {
    title: string;
    description?: string;
    case_id?: string;
    event_type?: string;
    starts_at: string;
    ends_at?: string;
    meet_url?: string;
    city?: string;
    location?: string;
  }) =>
    request<AgendaEventItem>("/api/workspace/agenda", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateAgendaEvent: (
    id: string,
    data: Partial<{
      title: string;
      description: string;
      case_id: string | null;
      event_type: string;
      starts_at: string;
      ends_at: string | null;
      meet_url: string | null;
      city: string | null;
      location: string | null;
    }>,
  ) =>
    request<AgendaEventItem>(`/api/workspace/agenda/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteAgendaEvent: (id: string) =>
    request<void>(`/api/workspace/agenda/${id}`, { method: "DELETE" }),

  exportAgendaIcs: async (caseId?: string) => {
    const token = getToken();
    const qs = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    const res = await fetch(
      `${getApiBase()}/api/workspace/agenda/export.ics${qs}`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include",
        signal: AbortSignal.timeout(60_000),
      },
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
      const raw = typeof body.detail === "string" ? body.detail : apiMsg("serverError");
      throw new ApiError(humanizeApiDetail(raw), res.status);
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/i.exec(cd);
    const name = match?.[1] || "agenda-lexhub.ics";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    URL.revokeObjectURL(url);
  },

  polishDictation: (
    text: string,
    language: "ar" | "fr" = "ar",
    source: "dictation" | "audio" = "audio",
    caseId?: string | null,
  ) =>
    request<{
      polished: string;
      provider: string;
      pii_masked?: boolean;
      pii_summary?: {
        parties?: number;
        cin?: number;
        phone?: number;
        email?: number;
        other?: number;
      };
      contradictions?: {
        kind: string;
        values: string[];
        message_ar: string;
        message_fr: string;
      }[];
      guessed_words?: string[];
      edits?: {
        id: string;
        original: string;
        proposed: string;
        kind: string;
      }[];
      variables?: {
        kind: string;
        value: string;
        label_ar: string;
        label_fr: string;
      }[];
      structure_hints?: {
        section_ar: string;
        section_fr: string;
        excerpt: string;
        message_ar: string;
        message_fr: string;
      }[];
      law_suggestions?: {
        code_ar: string;
        code_fr: string;
        article: string;
        reason_ar: string;
        reason_fr: string;
        insert_ar: string;
      }[];
      degraded?: boolean;
      message?: string | null;
    }>("/api/dictation/polish", {
      method: "POST",
      body: JSON.stringify({
        text,
        language,
        source,
        ...(caseId ? { case_id: caseId } : {}),
      }),
    }),

  transcribeDictation: (
    file: File,
    language: string = "ar",
    timeoutMs = 1_800_000,
  ) => {
    const form = new FormData();
    form.append("file", file);
    const raw = language.toLowerCase();
    const lang = raw.startsWith("fr")
      ? "fr"
      : raw.startsWith("auto") || raw === "detect"
        ? "auto"
        : "ar";
    form.append("language", lang);
    return uploadRequest<{
      text: string;
      provider: string;
      language?: string | null;
      degraded?: boolean;
      confidence?: number;
      needs_review?: boolean;
      chunks?: number;
    }>("/api/dictation/transcribe", form, false, timeoutMs, "transcribeTimeout");
  },

  getDictationSttStatus: () =>
    request<{
      enabled: boolean;
      model: string;
      device: string;
      loaded: boolean;
      languages?: string[];
      local_only?: boolean;
      groq_fallback?: boolean;
      groq_primary?: boolean;
      ready?: boolean;
      universal?: boolean;
      pipeline?: string;
    }>("/api/dictation/stt-status"),

  composeDictation: (data: {
    text: string;
    doc_type?: "plaidoirie" | "general" | "petition" | "memo" | "letter" | "minutes";
    title?: string;
    polish_first?: boolean;
    plaidoirie_type?: string;
    language?: "ar" | "fr";
    case_id?: string;
    brief_posture?: string;
    brief_jurisdiction?: string;
    clarifications?: { id: string; choice?: string; other?: string; label?: string }[];
  }) =>
    request<{
      title: string;
      body: string;
      polished?: string | null;
      provider: string;
      checks?: string[];
      plaidoirie_type?: string | null;
      language?: string;
      header_ar: string;
      header_fr: string;
      motto_ar: string;
      degraded?: boolean;
      message?: string | null;
      pii_masked?: boolean;
      case_enriched?: boolean;
    }>("/api/dictation/compose", { method: "POST", body: JSON.stringify(data) }),

  reviseDictation: (data: {
    title?: string;
    body: string;
    instruction: string;
    case_id?: string;
    language?: "ar" | "fr";
  }) =>
    request<{ title: string; body: string; provider: string; reply?: string }>("/api/dictation/revise", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  clarifyDictation: (data: {
    text: string;
    case_id: string;
    plaidoirie_type?: string;
    language?: "ar" | "fr";
    brief_posture?: string;
    brief_jurisdiction?: string;
  }) =>
    request<ClarifyDictationResult>("/api/dictation/clarify", {
      method: "POST",
      body: JSON.stringify(data),
    }),


  /** Télécharge un .docx réel (Word) et déclenche l'enregistrement navigateur. */
  fetchPlaidoirieDocx: async (data: PlaidoirieExportPayload): Promise<{ blob: Blob; filename: string }> => {
    const doFetch = async (token: string | null) =>
      fetch(`${getApiBase()}/api/plaidoirie-templates/export-docx`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(60_000),
      });

    let token = getToken();
    let res = await doFetch(token);
    if (res.status === 401) {
      const refreshed = await handleUnauthorized();
      if (!refreshed) {
        throw new ApiError("Session expirée — reconnectez-vous.", 401);
      }
      token = refreshed;
      res = await doFetch(token);
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Export Word échoué" }));
      throw new ApiError(
        typeof body.detail === "string" ? body.detail : "Export Word échoué",
        res.status,
      );
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename\*?=(?:UTF-8''|")?([^\";]+)/i.exec(cd);
    const filename = decodeURIComponent((match?.[1] || "plaidoirie.docx").replace(/"/g, ""));
    return { blob, filename: filename.endsWith(".docx") ? filename : "plaidoirie.docx" };
  },

  downloadPlaidoirieDocx: async (data: PlaidoirieExportPayload) => {
    const { blob, filename } = await api.fetchPlaidoirieDocx(data);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename.endsWith(".docx") ? filename : "plaidoirie.docx";
    a.click();
    URL.revokeObjectURL(url);
    return filename;
  },

  /** Télécharge un vrai .pdf (binaire) — même mise en page que Word. */
  downloadPlaidoiriePdf: async (data: PlaidoirieExportPayload) => {
    const { blob, filename } = await api.fetchPlaidoiriePdf(data);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    return filename;
  },

  /** Récupère le PDF binaire (même moteur que Word). */
  fetchPlaidoiriePdf: async (data: PlaidoirieExportPayload): Promise<{ blob: Blob; filename: string }> => {
    const doFetch = async (token: string | null) =>
      fetch(`${getApiBase()}/api/plaidoirie-templates/export-pdf`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(data),
        signal: AbortSignal.timeout(90_000),
      });

    let token = getToken();
    let res = await doFetch(token);
    if (res.status === 401) {
      const refreshed = await handleUnauthorized();
      if (!refreshed) {
        throw new ApiError("Session expirée — reconnectez-vous.", 401);
      }
      token = refreshed;
      res = await doFetch(token);
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Export PDF échoué" }));
      throw new ApiError(
        typeof body.detail === "string" ? body.detail : "Export PDF échoué",
        res.status,
      );
    }
    const blob = await res.blob();
    if (!blob.type.includes("pdf") && blob.size < 100) {
      throw new ApiError("Export PDF invalide", 500);
    }
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename\*?=(?:UTF-8''|")?([^\";]+)/i.exec(cd);
    const rawName = decodeURIComponent((match?.[1] || "plaidoirie.pdf").replace(/"/g, ""));
    const filename = rawName.toLowerCase().endsWith(".pdf") ? rawName : "plaidoirie.pdf";
    return { blob, filename };
  },

  /** Ouvre le PDF officiel (comme Word) puis lance l'impression — plus de about:blank HTML. */
  printPlaidoiriePdf: async (data: {
    title: string;
    body: string;
    cabinet_name?: string;
    lawyer_name?: string;
    city?: string;
    include_esignature?: boolean;
  }) => {
    const { blob } = await api.fetchPlaidoiriePdf(data);
    const url = URL.createObjectURL(blob);
    const win = window.open(url, "_blank");
    if (!win) {
      // Pop-up bloquée → téléchargement
      const a = document.createElement("a");
      a.href = url;
      a.download = "plaidoirie.pdf";
      a.click();
      URL.revokeObjectURL(url);
      throw new ApiError(
        "Autorisez les pop-ups pour imprimer, ou ouvrez le PDF téléchargé.",
        0,
      );
    }
    // Laisser le PDF charger puis imprimer
    const tryPrint = () => {
      try {
        win.focus();
        win.print();
      } catch {
        /* ignore */
      }
    };
    setTimeout(tryPrint, 800);
    setTimeout(() => URL.revokeObjectURL(url), 120_000);
  },

  getDocumentDownloadUrl: (id: string) =>
    `${getApiBase()}/api/documents/${id}/download`,

  getTeam: () => request<TeamMember[]>("/api/team"),

  getJoinCode: () => request<JoinCodeInfo>("/api/team/join-code"),

  regenerateJoinCode: () =>
    request<JoinCodeInfo>("/api/team/join-code/regenerate", { method: "POST" }),

  validateJoinCode: (code: string) =>
    request<{ valid: boolean }>("/api/team/join/validate", {
      method: "POST",
      body: JSON.stringify({ code }),
    }),

  getInvitePreview: (code: string) =>
    request<InvitePreview>(`/api/team/join/invite-preview?code=${encodeURIComponent(code)}`),

  acceptInvite: (data: { code: string; full_name: string; password: string }) =>
    request<{ message: string }>("/api/team/join/accept-invite", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  submitJoinRequest: (data: {
    code: string;
    full_name: string;
    email: string;
    password: string;
  }) =>
    request<{ message: string }>("/api/team/join/request", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateTeamMember: (id: string, data: TeamUpdatePayload) =>
    request<TeamMember>(`/api/team/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getCabinetSettings: () => request<CabinetSettings>("/api/settings/cabinet"),

  updateCabinetSettings: (data: Partial<CabinetSettings>) =>
    request<CabinetSettings>("/api/settings/cabinet", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  requestPasswordOtp: () =>
    request<{ message: string }>("/api/settings/password/request-otp", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  changePassword: (new_password: string, email_otp: string, current_password?: string) =>
    request<{ message: string }>("/api/settings/password", {
      method: "POST",
      body: JSON.stringify({ new_password, email_otp, current_password }),
    }),

  requestAccountDeleteOtp: () =>
    request<{ message: string }>("/api/settings/account/delete-otp", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  deleteAccount: (password: string, email_otp: string, confirmation: string) =>
    request<{ message: string }>("/api/settings/account/delete", {
      method: "POST",
      body: JSON.stringify({ password, email_otp, confirmation }),
    }),

  getAdminCabinets: () => request<AdminCabinet[]>("/api/admin/cabinets"),

  getBillingPlans: () => request<BillingPlan[]>("/api/billing/plans"),

  getBillingEntitlements: () => request<BillingEntitlements>("/api/billing/entitlements"),

  updateOnDemandSettings: (enabled: boolean, mad_limit?: number | null) =>
    request<BillingEntitlements & { message?: string }>("/api/billing/on-demand", {
      method: "PATCH",
      body: JSON.stringify(
        mad_limit === undefined
          ? { enabled }
          : { enabled, mad_limit },
      ),
    }),

  getBillingAddons: () =>
    request<{
      prepaid_ai_credits: number;
      credit_packs_available: boolean;
      is_active_paying?: boolean;
      is_trial?: boolean;
      show_pack_banner?: boolean;
      nudge_upgrade_before_pack?: boolean;
      pack_lots?: {
        id: string;
        credits_remaining: number;
        expires_at?: string | null;
        credits?: number;
      }[];
      credit_packs: {
        id: string;
        credits: number;
        price_mad: number;
        label: string;
        label_ar?: string;
        unit_mad: number;
        expires_after_months?: number;
        expires_hint?: string;
      }[];
      seats_addon_available: boolean;
      extra_avocat_seats: number;
      extra_seat_mad_monthly: number;
      max_extra_avocat_seats: number;
      avocats_limit: number;
      avocats_included: number;
    }>("/api/billing/addons"),

  purchaseCreditPack: (pack_id: string) =>
    request<BillingEntitlements & { message?: string }>("/api/billing/credit-packs/purchase", {
      method: "POST",
      body: JSON.stringify({ pack_id }),
    }),

  checkoutCreditPack: (pack_id: string) =>
    request<{
      purchase_id: string;
      pack_id: string;
      credits: number;
      amount_mad: number;
      unit_mad: number;
      label: string;
      expires_after_months: number;
      expires_hint: string;
      status: string;
      payment_required: boolean;
    }>("/api/billing/credit-packs/checkout", {
      method: "POST",
      body: JSON.stringify({ pack_id }),
    }),

  confirmCreditPackPayment: (
    purchase_id: string,
    card: { name: string; number: string; exp: string; cvc: string },
  ) =>
    request<BillingEntitlements & { message?: string }>("/api/billing/credit-packs/confirm-payment", {
      method: "POST",
      body: JSON.stringify({
        purchase_id,
        card_name: card.name,
        card_number: card.number,
        card_exp: card.exp,
        card_cvc: card.cvc,
      }),
    }),

  updateExtraSeats: (quantity: number) =>
    request<BillingEntitlements & { message?: string }>("/api/billing/extra-seats", {
      method: "PATCH",
      body: JSON.stringify({ quantity }),
    }),

  getBillingInsights: () =>
    request<{
      insights: {
        id: string;
        priority: number;
        tone: string;
        title: string;
        body: string;
        cta: string;
        href: string;
      }[];
    }>("/api/billing/insights"),

  getReferral: () =>
    request<{
      available: boolean;
      code: string | null;
      share_path?: string;
      referee_bonus_days?: number;
      referrer_reward_days?: number;
      rules_fr?: string;
      rules_ar?: string;
      stats?: { invites: number; pending: number; rewarded: number };
      recent?: {
        status: string;
        code_used: string;
        referee_bonus_applied: boolean;
        referrer_reward_applied: boolean;
        created_at?: string | null;
      }[];
    }>("/api/billing/referral"),

  getPaymentMethods: () =>
    request<{ currency: string; note: string; methods: { id: string; name: string; name_ar?: string; status: string; blurb: string }[] }>(
      "/api/billing/payment-methods",
    ),

  getCancelReasons: () =>
    request<{ code: string; label: string }[]>("/api/billing/cancel-reasons"),

  getBillingHistory: () =>
    request<{
      events: { id: string; event_type: string; plan_slug?: string; detail?: string; created_at?: string }[];
      invoices: {
        id: string;
        number: string;
        plan_name: string;
        amount_mad: number;
        status: string;
        issued_at?: string;
        kind?: string;
      }[];
    }>("/api/billing/history"),

  sendPaymentReminder: () =>
    request<{ message: string }>("/api/billing/payment-reminder", { method: "POST" }),

  cancelSubscription: (reason_code: string, reason_text?: string) =>
    request<{ message: string }>("/api/billing/cancel", {
      method: "POST",
      body: JSON.stringify({ reason_code, reason_text }),
    }),

  undoCancelSubscription: () =>
    request<{ message: string }>("/api/billing/cancel/undo", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  simulatePaymentFailed: () =>
    request<{ message: string }>("/api/billing/payment-failed", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  generateInvoice: () =>
    request<{ id: string; number: string; amount_mad: number; html: string }>(
      "/api/billing/invoices/generate",
      { method: "POST", body: JSON.stringify({}) },
    ),

  getBillingInvoice: (invoiceId: string) =>
    request<{
      id: string;
      number: string;
      plan_name: string;
      amount_mad: number;
      status: string;
      html: string;
      issued_at?: string;
    }>(`/api/billing/invoices/${invoiceId}`),

  downloadBillingInvoicePdf: async (invoiceId: string, filename?: string) => {
    const token = getToken();
    const res = await fetch(
      `${getApiBase()}/api/billing/invoices/${encodeURIComponent(invoiceId)}/download`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        credentials: "include",
        signal: AbortSignal.timeout(60_000),
      },
    );
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
      const raw = typeof body.detail === "string" ? body.detail : apiMsg("serverError");
      throw new ApiError(humanizeApiDetail(raw), res.status);
    }
    const blob = await res.blob();
    if (!blob.type.includes("pdf") && blob.size < 80) {
      throw new ApiError("PDF facture invalide", res.status);
    }
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename\*?=(?:UTF-8''|")?([^\";]+)/i.exec(cd);
    const rawName = decodeURIComponent((match?.[1] || filename || "LexHub-facture.pdf").replace(/"/g, ""));
    const name = rawName.toLowerCase().endsWith(".pdf") ? rawName : `${rawName}.pdf`;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = name;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    return name;
  },

  getAdminCancelInsights: () =>
    request<{
      total: number;
      by_reason: { code: string; label: string; count: number }[];
      samples: { code: string; text: string }[];
      ai_suggestion?: string | null;
    }>("/api/admin/billing/cancel-insights"),

  selectBillingPlan: (
    plan_slug: string,
    billing_cycle: "monthly" | "yearly" = "monthly",
    card?: { name: string; number: string; exp: string; cvc: string },
  ) =>
    request<{
      message: string;
      invoice_id?: string;
      invoice_number?: string;
      invoice_html?: string;
    }>("/api/billing/select-plan", {
      method: "POST",
      body: JSON.stringify({
        plan_slug,
        billing_cycle,
        ...(card
          ? {
              card_name: card.name,
              card_number: card.number,
              card_exp: card.exp,
              card_cvc: card.cvc,
            }
          : {}),
      }),
    }),

  getPaymentEnv: () =>
    request<PaymentEnv>("/api/billing/payment-env"),

  generateCleDeBarre: (
    case_id: string,
    extra_instructions?: string,
    language?: AppLocale,
  ) =>
    request<{
      case_id: string;
      reference: string;
      cle_de_barre: string;
      pii_masked: boolean;
      provider: string;
    }>("/api/billing/cle-de-barre", {
      method: "POST",
      body: JSON.stringify({
        case_id,
        extra_instructions,
        language: language || getClientLocale(),
      }),
    }),

  getAdminBillingPlans: () => request<BillingPlan[]>("/api/admin/billing/plans"),

  updateAdminBillingPlan: (
    planId: string,
    data: Partial<{
      name: string;
      name_ar: string;
      description: string;
      price_mad_monthly: number;
      price_mad_yearly: number;
      max_avocats: number;
      max_assistants: number;
      max_cases: number;
      max_plaidoiries_month: number;
      max_ai_credits_month: number;
      features: string[];
      is_public: boolean;
      is_recommended: boolean;
      is_active: boolean;
      sort_order: number;
      trial_days: number;
    }>,
  ) =>
    request<BillingPlan>(`/api/admin/billing/plans/${planId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  assignAdminCabinetPlan: (
    cabinetId: string,
    data: { plan_slug: string; status?: string; billing_cycle?: string; notes?: string },
  ) =>
    request<{ message: string }>(`/api/admin/billing/cabinets/${cabinetId}/assign`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  uploadCabinetLogo: async (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    const token = getToken();
    const res = await fetch(`${getApiBase()}/api/settings/cabinet/logo`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: fd,
      credentials: "include",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const detail =
        typeof err.detail === "string" ? err.detail : "Upload logo échoué";
      throw new ApiError(detail, res.status);
    }
    return (await res.json()) as CabinetSettings;
  },
  getCabinetLogoDataUrl: async (): Promise<string | null> => {
    const token = getToken();
    const res = await fetch(`${getApiBase()}/api/settings/cabinet/logo`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
    });
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result || ""));
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(blob);
    });
  },
  deleteCabinetLogo: () =>
    request<{ message: string }>("/api/settings/cabinet/logo", { method: "DELETE" }),
  updateProfileNames: (data: { full_name?: string; full_name_ar?: string; phone?: string }) =>
    request<AuthUser>("/api/settings/profile", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  requestEmailChangeOtp: (new_email: string) =>
    request<{ message: string }>("/api/settings/email/request-otp", {
      method: "POST",
      body: JSON.stringify({ new_email }),
    }),
  confirmEmailChange: (new_email: string, email_otp: string, current_password: string) =>
    request<AuthUser>("/api/settings/email/confirm", {
      method: "POST",
      body: JSON.stringify({ new_email, email_otp, current_password }),
    }),
  listPlaidoirieDrafts: () =>
    request<PlaidoirieDraftItem[]>("/api/plaidoirie-templates/drafts"),
  getPlaidoirieDraft: (id: string) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}`),
  savePlaidoirieDraft: (data: {
    title: string;
    body: string;
    template_id?: string;
    case_id?: string;
    checks?: string[];
    status?: "draft" | "validated" | "finalized";
  }) =>
    request<PlaidoirieDraftItem>("/api/plaidoirie-templates/drafts", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  updatePlaidoirieDraft: (
    id: string,
    data: {
      case_id?: string | null;
      title?: string;
      body?: string;
      status?: "draft" | "validated" | "finalized";
      checks?: string[];
    },
  ) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  validatePlaidoirieDraft: (id: string) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}/validate`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  unvalidatePlaidoirieDraft: (id: string) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}/unvalidate`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  deletePlaidoirieDraft: (id: string) =>
    request<{ message: string }>(`/api/plaidoirie-templates/drafts/${id}`, {
      method: "DELETE",
    }),

  updatePlaidoirieDraftCase: (id: string, caseId: string | null) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ case_id: caseId ?? "" }),
    }),

  getAuditArchives: () =>
    request<
      {
        id: string;
        filename: string;
        period_start: string;
        period_end: string;
        row_count: number;
        created_at: string;
      }[]
    >("/api/admin/audit-archives"),

  runAuditArchive: () =>
    request<{ message: string; archived: boolean; id?: string; filename?: string }>(
      "/api/admin/audit-archives/run",
      { method: "POST" },
    ),

  downloadAuditArchive: async (id: string, filename: string) => {
    const token = getToken();
    const res = await fetch(`${getApiBase()}/api/admin/audit-archives/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
    });
    if (!res.ok) throw new ApiError("Téléchargement impossible", res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },

  getAdminMetrics: () => request<AdminMetrics>("/api/admin/metrics"),

  runPlatformAnalysis: () =>
    request<{
      generated_at: string;
      period_days: number;
      metrics: Record<string, unknown>;
      recommendations: string[];
      growth_recommendations?: unknown[];
      summary_fr: string;
      aligned_with?: string;
      ops_coach?: Record<string, unknown>;
      lifecycle_emails?: Array<{
        id: string;
        label: string;
        when: string;
        case: string;
        channel: string;
      }>;
      emails_sent_30j?: Record<string, number>;
      emails_total_30j?: number;
    }>("/api/admin/platform-analysis", { method: "POST", body: JSON.stringify({}) }),

  opsCoachDraftEmail: (body: {
    scenario: string;
    cabinet_id: string;
    extra?: Record<string, unknown>;
    use_ai?: boolean;
    tip_context?: string;
  }) =>
    request<{
      cabinet_id: string;
      cabinet_name: string;
      city?: string;
      contacts: Array<{ email: string; name: string; role: string }>;
      to_email?: string | null;
      to_name?: string | null;
      draft?: {
        subject: string;
        body_text: string;
        body_html?: string;
        cta_url?: string;
        ai_generated?: string;
      } | null;
      cc_emails?: string[];
    }>("/api/admin/ops-coach/draft-email", {
      method: "POST",
      body: JSON.stringify(body),
    }),

  opsCoachSendEmail: (body: {
    to: string;
    cc?: string[];
    subject: string;
    body_text: string;
    body_html?: string;
    tip_id?: string;
    cabinet_id?: string;
  }) =>
    request<{ message: string; to: string; cc: string[]; subject: string }>(
      "/api/admin/ops-coach/send-email",
      { method: "POST", body: JSON.stringify(body) },
    ),

  getAuditLogs: (params?: { limit?: number; q?: string; action?: string }) => {
    const qs = new URLSearchParams();
    if (params?.limit != null) qs.set("limit", String(params.limit));
    if (params?.q?.trim()) qs.set("q", params.q.trim());
    if (params?.action?.trim()) qs.set("action", params.action.trim());
    const q = qs.toString();
    return request<AuditLogItem[]>(`/api/admin/audit-logs${q ? `?${q}` : ""}`);
  },

  getCorpusStats: () => request<CorpusStats>("/api/corpus/stats"),

  getArticleGraph: (articleId?: string, instrument?: string) => {
    const params = new URLSearchParams();
    if (articleId) params.set("article_id", articleId);
    if (instrument) params.set("instrument", instrument);
    const q = params.toString();
    return request<ArticleGraph>(`/api/corpus/graph${q ? `?${q}` : ""}`);
  },

  getTemplates: () => request<{ templates: DocumentTemplate[] }>("/api/corpus/templates"),

  generateDocument: (templateId: string, fields: Record<string, string>) =>
    request<GeneratedDocument>("/api/corpus/templates/generate", {
      method: "POST",
      body: JSON.stringify({ template_id: templateId, fields }),
    }),

  getBenchmarkResults: () => request<BenchmarkSummary | { message: string; results: null }>(
    "/api/corpus/benchmark/results",
  ),

  runBenchmark: (limit?: number) =>
    request<BenchmarkSummary>("/api/corpus/benchmark/run", {
      method: "POST",
      body: JSON.stringify({ limit: limit ?? null }),
    }),

  getNotifications: (unreadOnly = false) =>
    request<CabinetNotificationItem[]>(
      `/api/notifications${unreadOnly ? "?unread_only=true" : ""}`,
    ),
  getNotificationsUnreadCount: () =>
    request<{ count: number }>("/api/notifications/unread-count"),
  markNotificationRead: (id: string) =>
    request<{ ok: boolean }>(`/api/notifications/${id}/read`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
  markAllNotificationsRead: () =>
    request<{ ok: boolean; count: number }>("/api/notifications/read-all", {
      method: "POST",
      body: JSON.stringify({}),
    }),
  deleteNotifications: (opts: { ids?: string[]; all?: boolean }) =>
    request<{ ok: boolean; count: number }>("/api/notifications/delete", {
      method: "POST",
      body: JSON.stringify({ ids: opts.ids || [], all: Boolean(opts.all) }),
    }),
  sendNotificationsDigest: (assistant_ids?: string[]) =>
    request<{ ok: boolean; sent: number; pending?: number; message?: string }>(
      "/api/notifications/digest-email",
      { method: "POST", body: JSON.stringify({ assistant_ids: assistant_ids || [] }) },
    ),
  workspaceSearch: (q: string) =>
    request<WorkspaceSearchHit[]>(`/api/workspace/search?q=${encodeURIComponent(q)}`),
  workspaceActivity: (limit = 40) =>
    request<WorkspaceActivityItem[]>(`/api/workspace/activity?limit=${limit}`),
  listActivityArchives: () =>
    request<ActivityArchiveItem[]>(`/api/workspace/activity/archives`),
  downloadActivityArchive: async (id: string, filename: string) => {
    const token = getToken();
    const res = await fetch(`${getApiBase()}/api/workspace/activity/archives/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      credentials: "include",
    });
    if (!res.ok) throw new ApiError("Téléchargement impossible", res.status);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
  sendTeamInviteEmail: (email: string, recipient_name?: string, role = "avocat") =>
    request<{ message: string }>("/api/team/invite-email", {
      method: "POST",
      body: JSON.stringify({ email, recipient_name: recipient_name || null, role }),
    }),
  listTeamInvites: () => request<CabinetInviteItem[]>("/api/team/invites"),
  listAssistants: () =>
    request<TeamMember[]>(`/api/team/assistants`),
  assignPlaidoirieDraft: (id: string, user_id: string | null) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}/assign`, {
      method: "POST",
      body: JSON.stringify({ user_id }),
    }),
  pinPlaidoirieDraft: (id: string) =>
    request<PlaidoirieDraftItem>(`/api/plaidoirie-templates/drafts/${id}/pin`, {
      method: "POST",
      body: JSON.stringify({}),
    }),
};

export interface RegisterPayload {
  email: string;
  email_otp: string;
  password?: string;
  cabinet_name?: string;
  city?: string;
  address?: string;
  barreau?: string;
  ice?: string;
  manager_name?: string;
  phone?: string | null;
  referral_code?: string;
}

export interface LoginPayload {
  email: string;
  password: string;
  totp_code?: string;
  recovery_code?: string;
  captcha_token?: string;
}

export interface TwoFactorSetup {
  secret: string;
  qr_code_base64: string;
  provisioning_uri: string;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  full_name_ar?: string | null;
  phone?: string | null;
  role: string;
  cabinet_id: string;
  cabinet_name: string;
  cabinet_name_ar?: string | null;
  cabinet_city?: string | null;
  cabinet_barreau?: string | null;
  cabinet_address?: string | null;
  cabinet_has_logo?: boolean;
  cabinet_profile_complete?: boolean;
  totp_enabled?: boolean;
  mfa_required?: boolean;
  has_seen_onboarding_tour?: boolean;
  must_set_password?: boolean;
  /** Compte lié Google — pas besoin de mot de passe LexHub. */
  auth_via_google?: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
  mfa_setup_required?: boolean;
  captcha_required?: boolean;
}

export interface PlaidoirieExportPayload {
  title: string;
  body: string;
  cabinet_name?: string;
  lawyer_name?: string;
  city?: string;
  case_reference?: string;
  client_name?: string;
  include_esignature?: boolean;
}

export interface ClarifyOption {
  id: string;
  label_ar: string;
  label_fr: string;
}

export interface ClarifyQuestion {
  id: string;
  prompt_ar: string;
  prompt_fr: string;
  options: ClarifyOption[];
  allow_other: boolean;
}

export interface ClarifyDictationResult {
  questions: ClarifyQuestion[];
  summary_fr: string;
  summary_ar: string;
  pieces_noted: number;
  pii_tokens: string[];
  provider: string;
}

export interface CaseListItem {
  id: string;
  reference: string;
  title?: string | null;
  client_name: string;
  case_type: string;
  status: string;
  responsible_name: string;
  responsible_id?: string | null;
  updated_at: string;
  tags?: string[];
  jurisdiction_degree?: string | null;
  tribunal?: string | null;
  court_city?: string | null;
  court_file_number?: string | null;
  judge_name?: string | null;
  chamber?: string | null;
  greffe?: string | null;
  procedure_status?: string | null;
  assistant_id?: string | null;
  last_decision_type?: string | null;
  last_decision_date?: string | null;
  notification_date?: string | null;
  appeal_deadline_at?: string | null;
  appeal_deadline_days?: number | null;
  client_role?: string | null;
  client_quality?: string | null;
  client_domicile?: string | null;
  opposing_name?: string | null;
  opposing_role?: string | null;
  opposing_quality?: string | null;
  opposing_domicile?: string | null;
}

export interface CaseDetail extends CaseListItem {
  description?: string;
  opened_at: string;
  tags: string[];
}

export interface CreateCasePayload {
  title?: string;
  client_name: string;
  case_type: string;
  status: string;
  description?: string;
  tags?: string[];
  responsible_id?: string;
  first_hearing_at?: string;
  jurisdiction_degree?: string;
  tribunal?: string;
  court_city?: string;
  court_file_number?: string;
  judge_name?: string;
  chamber?: string;
  greffe?: string;
  procedure_status?: string;
  assistant_id?: string;
  last_decision_type?: string;
  last_decision_date?: string;
  notification_date?: string;
  appeal_deadline_at?: string;
  appeal_deadline_days?: number;
  client_role?: string;
  client_quality?: string;
  client_domicile?: string;
  opposing_name?: string;
  opposing_role?: string;
  opposing_quality?: string;
  opposing_domicile?: string;
}

export interface DocumentItem {
  id: string;
  original_name: string;
  mime_type: string;
  file_size: number;
  ocr_score: number | null;
  ocr_alert?: boolean;
  status: string;
  case_id: string;
  case_reference: string | null;
  created_at: string;
  /** "audio" | "file" — déduit côté API */
  kind?: "audio" | "file" | string;
  error_message?: string | null;
  inventory_number?: number | null;
  exhibit_type?: string | null;
  produced_by?: string | null;
  exhibit_version?: string | null;
  cited_in_plea?: string | null;
  uploaded_by?: string | null;
}


export interface PaymentEnv {
  bank_rib?: string | null;
  bank_name?: string | null;
  beneficiary?: string | null;
  ice?: string | null;
  cmi_ready?: boolean;
  payzone_ready?: boolean;
  card_status?: string | null;
  note?: string | null;
  note_ar?: string | null;
}

export interface DocumentDetail extends DocumentItem {
  extracted_text_preview: string | null;
}

export interface Citation {
  label: string;
  excerpt: string;
  url?: string | null;
}

export interface AIResult {
  answer: string;
  source_type: string;
  sources: Citation[];
  confidence_score: number;
  summary?: string;
  disclaimer: string;
  session_id?: string;
}

export interface SynthesisResult {
  document_id: string;
  document_name: string;
  parties: string[];
  key_dates: string[];
  amounts: string[];
  risk_clauses: string[];
  attention_points: string[];
  summary: string;
  sources: Citation[];
  disclaimer: string;
}

export interface CaseAnalysisResult {
  case_id: string;
  case_reference: string;
  facts: string;
  key_documents: string[];
  legal_issues: string[];
  risks_and_deadlines: string[];
  checklist: string[];
  summary: string;
  parties: string[];
  key_dates: string[];
  amounts: string[];
  sources: Citation[];
  confidence_score: number;
  disclaimer: string;
}

export interface AgendaEventItem {
  id: string;
  title: string;
  description?: string | null;
  case_id?: string | null;
  case_reference?: string | null;
  event_type: "audience" | "deadline" | "rdv" | "other" | string;
  starts_at: string;
  ends_at?: string | null;
  meet_url?: string | null;
  city?: string | null;
  location?: string | null;
  created_at: string;
}

export interface WorkspaceSummary {
  upcoming_events: AgendaEventItem[];
}

export interface TeamMember {
  id: string;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
}

export interface TeamUpdatePayload {
  role?: string;
  is_active?: boolean;
}

export interface JoinCodeInfo {
  join_code: string;
  regenerated_at?: string | null;
  expires_at?: string | null;
  approved_count?: number;
  max_approvals?: number;
  remaining_approvals?: number;
  is_expired?: boolean;
  is_exhausted?: boolean;
  is_active?: boolean;
}

export interface CabinetSettings {
  id: string;
  name: string;
  name_ar?: string | null;
  city: string;
  address: string;
  barreau: string;
  ice?: string;
  ai_custom_prompt?: string | null;
  has_logo?: boolean;
  status: string;
}

export interface PlaidoirieDraftItem {
  id: string;
  title: string;
  body: string;
  template_id?: string | null;
  case_id?: string | null;
  case_reference?: string | null;
  checks: string[];
  status?: "draft" | "validated" | string;
  assigned_to_user_id?: string | null;
  assigned_to_name?: string | null;
  pinned?: boolean;
  created_at: string;
  updated_at: string;
}

export interface CabinetNotificationItem {
  id: string;
  type: string;
  title: string;
  body?: string | null;
  href?: string | null;
  read: boolean;
  created_at: string;
}

export interface WorkspaceSearchHit {
  kind: string;
  id: string;
  title: string;
  subtitle?: string | null;
  href: string;
}

export interface WorkspaceActivityItem {
  id: string;
  action: string;
  label: string;
  details?: string | null;
  actor_name?: string | null;
  created_at: string;
  href?: string | null;
}

export interface ActivityArchiveItem {
  id: string;
  filename: string;
  period_start: string;
  period_end: string;
  row_count: number;
  created_at: string;
}

export interface InvitePreview {
  valid: boolean;
  email: string;
  cabinet_name: string;
  recipient_name?: string | null;
  role: string;
  email_already_registered?: boolean;
  email_same_cabinet?: boolean;
}

export interface CabinetInviteItem {
  id: string;
  email: string;
  code: string;
  role?: string;
  expires_at: string;
  created_at: string;
  email_status?: string;
}

export interface AdminCabinet {
  id: string;
  name: string;
  city: string;
  address: string;
  barreau: string;
  ice?: string | null;
  status: string;
  user_count: number;
  document_count: number;
  case_count: number;
  created_at: string;
}

export interface AdminCabinetUser {
  id: string;
  email: string;
  full_name: string;
  role: string;
  phone?: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  is_deleted_account?: boolean;
}

export interface AdminCabinetDetail extends AdminCabinet {
  users: AdminCabinetUser[];
  deleted_accounts_count?: number;
  deleted_accounts?: AdminCabinetUser[];
  subscription?: {
    plan_slug?: string | null;
    plan_name?: string | null;
    status?: string | null;
    billing_cycle?: string | null;
    trial_ends_at?: string | null;
    current_period_end?: string | null;
    cancel_at_period_end?: boolean;
    cancel_reason_code?: string | null;
    cancel_reason_text?: string | null;
    cancel_requested_at?: string | null;
    payment_provider?: string | null;
  } | null;
  billing_history?: {
    event_type: string;
    plan_slug?: string | null;
    detail?: string | null;
    created_at?: string | null;
  }[];
  invoices?: {
    id: string;
    number: string;
    plan_name: string;
    amount_mad: number;
    status: string;
    billing_cycle?: string | null;
    issued_at?: string | null;
    kind?: string;
  }[];
}

export interface AdminMetrics {
  active_cabinets: number;
  suspended_cabinets: number;
  total_users: number;
  total_documents: number;
  deleted_accounts?: number;
  cancel_requests?: number;
}

export interface AuditLogItem {
  id: string;
  user_id: string | null;
  cabinet_id: string | null;
  action: string;
  ip_address: string | null;
  details: string | null;
  created_at: string;
  user_name?: string | null;
  user_email?: string | null;
  cabinet_name?: string | null;
}

export interface CorpusStats {
  version: string;
  total_entries: number;
  target_adala: number;
  progress_pct: number;
  collections: Record<string, { entries: number; chunks_indexed: number }>;
}

export interface ArticleGraphNode {
  id: string;
  label: string;
  instrument?: string;
}

export interface ArticleGraph {
  nodes?: ArticleGraphNode[];
  edges?: { from: string; to: string; relation?: string }[];
  center?: ArticleGraphNode;
  related?: ArticleGraphNode[];
  instrument?: string;
}

export interface DocumentTemplate {
  id: string;
  name: string;
  category: string;
  description: string;
  fields: string[];
}

export interface GeneratedDocument {
  template_id: string;
  template_name: string;
  category: string;
  content: string;
  disclaimer: string;
}

export interface BenchmarkResultItem {
  id: number;
  domain: string;
  question: string;
  expected_source: string;
  source_found: boolean;
  keywords_matched: number;
  keywords_total: number;
  confidence: number;
  source_type: string;
  score: number;
  passed: boolean;
}

export interface BenchmarkSummary {
  run_at: string;
  total: number;
  passed: number;
  failed: number;
  pass_rate_pct: number;
  avg_score: number;
  by_domain: Record<string, number>;
  kanoun_reference: string;
  results: BenchmarkResultItem[];
}

export interface BillingPlan {
  id: string;
  slug: string;
  name: string;
  name_ar?: string | null;
  description?: string | null;
  price_mad_monthly: number;
  price_mad_yearly: number;
  max_avocats: number;
  max_assistants: number;
  max_cases: number;
  max_plaidoiries_month: number;
  max_ai_credits_month?: number;
  features: string[];
  highlights?: string[];
  highlights_ar?: string[];
  is_public: boolean;
  is_recommended: boolean;
  is_active: boolean;
  sort_order: number;
  trial_days: number;
}

export interface BillingEntitlements {
  plan?: BillingPlan | { slug: string; name: string; name_ar?: string };
  status?: string;
  billing_cycle?: string;
  trial_ends_at?: string | null;
  trial_days_left?: number | null;
  trial_usage_capped?: boolean;
  current_period_end?: string | null;
  payment_provider?: string;
  payment_mock?: boolean;
  features?: string[];
  past_due_days?: number | null;
  access_restricted?: boolean;
  cancel_at_period_end?: boolean;
  cancel_reason_code?: string | null;
  cancel_requested_at?: string | null;
  on_demand_enabled?: boolean;
  on_demand_mad_limit?: number | null;
  on_demand_mad_per_credit?: number;
  on_demand_available?: boolean;
  prepaid_ai_credits?: number;
  extra_avocat_seats?: number;
  extra_seat_mad_monthly?: number;
  seats_addon_available?: boolean;
  credit_packs_available?: boolean;
  is_active_paying?: boolean;
  is_trial?: boolean;
  credit_packs?: {
    id: string;
    credits: number;
    price_mad: number;
    label: string;
    label_ar?: string;
    unit_mad: number;
  }[];
  usage?: {
    plaidoiries_used?: number;
    plaidoiries_limit?: number;
    avocats_used?: number;
    avocats_limit?: number;
    assistants_used?: number;
    assistants_limit?: number;
    cases_used?: number;
    cases_limit?: number;
    cle_de_barre_used?: number;
    cle_de_barre_limit?: number;
    synthesis_used?: number;
    synthesis_limit?: number;
    ai_credits_used?: number;
    ai_credits_limit?: number;
    analyse_used?: number;
    analyse_limit?: number;
    ask_used?: number;
    ask_limit?: number;
    revise_used?: number;
    revise_limit?: number;
    ai_overage_credits?: number;
    ai_overage_mad_estimate?: number;
    paid_ai_credits_limit?: number | null;
    paid_plaidoiries_limit?: number | null;
  };
  ai_credit_costs?: Record<string, number>;
  ai_daily_limit?: number;
  ai_daily_used?: number;
}
