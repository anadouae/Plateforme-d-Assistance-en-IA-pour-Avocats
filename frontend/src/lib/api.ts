import { getTranslations } from "@/lib/i18n/translations";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function apiMsg(
  key: "timeout" | "unreachable" | "serverError" | "uploadTimeout",
): string {
  return getTranslations(getClientLocale()).app.api[key];
}

function isTimeoutError(e: unknown): boolean {
  return (
    (e instanceof DOMException && e.name === "TimeoutError") ||
    (e instanceof Error && e.name === "TimeoutError")
  );
}

function activeTokenStorage(): Storage {
  const remember = localStorage.getItem("sanad_remember") !== "0";
  return remember ? localStorage : sessionStorage;
}

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("sanad_token") || localStorage.getItem("sanad_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    sessionStorage.getItem("sanad_refresh_token") ||
    localStorage.getItem("sanad_refresh_token")
  );
}

function persistTokens(data: AuthResponse) {
  const storage = activeTokenStorage();
  localStorage.removeItem("sanad_token");
  localStorage.removeItem("sanad_refresh_token");
  sessionStorage.removeItem("sanad_token");
  sessionStorage.removeItem("sanad_refresh_token");
  storage.setItem("sanad_token", data.access_token);
  storage.setItem("sanad_refresh_token", data.refresh_token);
  window.dispatchEvent(
    new CustomEvent("sanad-auth-updated", { detail: data }),
  );
}

function clearSession() {
  localStorage.removeItem("sanad_token");
  localStorage.removeItem("sanad_refresh_token");
  sessionStorage.removeItem("sanad_token");
  sessionStorage.removeItem("sanad_refresh_token");
  // Révoque aussi le cookie httpOnly côté API (best-effort)
  void fetch(`${API_URL}/api/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  }).catch(() => {});
  window.dispatchEvent(new CustomEvent("sanad-auth-cleared"));
}

let refreshInFlight: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken();
  if (!refresh) return null;

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/auth/refresh`, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: refresh }),
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
  if (typeof window === "undefined") return "ar";
  try {
    const raw =
      localStorage.getItem("sanad-locale-v3") ||
      localStorage.getItem("sanad-locale-v2") ||
      localStorage.getItem("sanad-locale");
    if (!raw) return "ar";
    const parsed = JSON.parse(raw) as { state?: { locale?: string } };
    const locale = parsed.state?.locale;
    if (locale === "fr") return "fr";
  } catch {
    /* ignore */
  }
  return "ar";
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  retried = false,
  timeoutMs = 60_000,
  timeoutRetried = false,
): Promise<T> {
  const token = getToken();
  const method = (options.method || "GET").toUpperCase();
  const headers: HeadersInit = {
    ...(options.headers || {}),
  };
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
    res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      signal,
      credentials: "include",
    });
  } catch (e) {
    // Un seul nouvel essai automatique sur timeout (réseaux / cold start Docker)
    if (isTimeoutError(e) && !timeoutRetried && !options.signal) {
      return request<T>(path, options, retried, Math.min(timeoutMs + 20_000, 90_000), true);
    }
    if (isTimeoutError(e)) {
      throw new ApiError(apiMsg("timeout"), 0);
    }
    throw new ApiError(apiMsg("unreachable"), 0);
  }

  if (res.status === 401 && !retried && path !== "/api/auth/refresh") {
    const newToken = await handleUnauthorized();
    if (newToken) {
      return request<T>(path, options, true, timeoutMs, timeoutRetried);
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: apiMsg("serverError") }));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(", ")
          : apiMsg("serverError");
    throw new ApiError(message, res.status);
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
  timeoutMs = 120_000,
): Promise<T> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  let res: Response;
  try {
    res = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers,
      body: formData,
      credentials: "include",
      signal: AbortSignal.timeout(timeoutMs),
    });
  } catch (e) {
    if (isTimeoutError(e)) {
      throw new ApiError(apiMsg("uploadTimeout"), 0);
    }
    throw new ApiError(apiMsg("unreachable"), 0);
  }

  if (res.status === 401 && !retried) {
    const newToken = await handleUnauthorized();
    if (newToken) {
      return uploadRequest<T>(path, formData, true, timeoutMs);
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Erreur serveur" }));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg).join(", ")
          : "Erreur serveur";
    throw new ApiError(message, res.status);
  }
  return res.json();
}

export const api = {
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

  requestMagicLink: (email: string) =>
    request<{ message: string }>("/api/auth/magic-link", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  magicLogin: (token: string) =>
    request<AuthResponse>("/api/auth/magic-login", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),

  register: (data: RegisterPayload) =>
    request<{ message: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  login: (data: LoginPayload) =>
    request<AuthResponse>("/api/auth/login", {
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

  getCaptchaConfig: () =>
    request<{ enabled: boolean; site_key: string; after_failures: number }>(
      "/api/auth/captcha-config",
    ),

  logout: () =>
    request<{ message: string }>("/api/auth/logout", {
      method: "POST",
      body: JSON.stringify({}),
    }),

  refreshToken: (refresh_token: string) =>
    request<AuthResponse>("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token }),
    }),

  verifyEmail: (token: string) =>
    request<{ message: string }>(`/api/auth/verify-email?token=${encodeURIComponent(token)}`),

  resendVerification: (email: string) =>
    request<{ message: string }>("/api/auth/resend-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
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

  approveCabinet: (id: string) =>
    request<{ message: string }>(`/api/admin/cabinets/${id}/approve`, { method: "PATCH" }),

  getCases: () => request<CaseListItem[]>("/api/cases"),

  createCase: (data: CreateCasePayload) =>
    request<CaseDetail>("/api/cases", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getCase: (id: string) => request<CaseDetail>(`/api/cases/${id}`),

  analyseCase: (id: string, language?: AppLocale) =>
    request<CaseAnalysisResult>(
      `/api/cases/${id}/analyse?lang=${language || getClientLocale()}`,
      { method: "POST", signal: AbortSignal.timeout(300_000) },
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
    request<void>(`/api/documents/${id}`, { method: "DELETE" }),

  reextractDocument: (id: string) =>
    request<DocumentDetail>(`/api/documents/${id}/reextract`, { method: "POST" }),

  getSynthesis: (id: string, language?: AppLocale) =>
    request<SynthesisResult>(
      `/api/documents/${id}/synthese?lang=${language || getClientLocale()}`,
      {},
      false,
      180_000,
    ),

  askDocument: (id: string, question: string, language?: AppLocale) =>
    request<AIResult>(`/api/documents/${id}/ask`, {
      method: "POST",
      body: JSON.stringify({
        question,
        language: language || getClientLocale(),
      }),
    }),

  /** Résumé planning (agenda / tâches / notes) pour le dashboard */
  getWorkspaceSummary: () =>
    request<WorkspaceSummary>("/api/workspace/summary"),

  getNotes: (caseId?: string) => {
    const qs = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    return request<CaseNoteItem[]>(`/api/workspace/notes${qs}`);
  },

  createNote: (data: { title: string; body?: string; case_id?: string }) =>
    request<CaseNoteItem>("/api/workspace/notes", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateNote: (id: string, data: { title?: string; body?: string; case_id?: string | null }) =>
    request<CaseNoteItem>(`/api/workspace/notes/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteNote: (id: string) =>
    request<void>(`/api/workspace/notes/${id}`, { method: "DELETE" }),

  getTasks: (caseId?: string) => {
    const qs = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    return request<CaseTaskItem[]>(`/api/workspace/tasks${qs}`);
  },

  createTask: (data: {
    title: string;
    description?: string;
    case_id?: string;
    status?: "todo" | "doing" | "done";
    due_at?: string;
  }) =>
    request<CaseTaskItem>("/api/workspace/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateTask: (
    id: string,
    data: {
      title?: string;
      description?: string;
      case_id?: string | null;
      status?: "todo" | "doing" | "done";
      due_at?: string | null;
    },
  ) =>
    request<CaseTaskItem>(`/api/workspace/tasks/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteTask: (id: string) =>
    request<void>(`/api/workspace/tasks/${id}`, { method: "DELETE" }),

  getAgenda: (caseId?: string) => {
    const qs = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
    return request<AgendaEventItem[]>(`/api/workspace/agenda${qs}`);
  },

  createAgendaEvent: (data: {
    title: string;
    description?: string;
    case_id?: string;
    event_type?: "audience" | "deadline" | "rdv" | "other";
    starts_at: string;
    ends_at?: string;
    meet_url?: string;
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
      event_type: "audience" | "deadline" | "rdv" | "other";
      starts_at: string;
      ends_at: string | null;
      meet_url: string | null;
    }>,
  ) =>
    request<AgendaEventItem>(`/api/workspace/agenda/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteAgendaEvent: (id: string) =>
    request<void>(`/api/workspace/agenda/${id}`, { method: "DELETE" }),

  polishDictation: (text: string, language: "ar" | "fr" = "ar") =>
    request<{ polished: string; provider: string }>("/api/dictation/polish", {
      method: "POST",
      body: JSON.stringify({ text, language }),
    }),

  transcribeDictation: (
    file: File,
    language: string = "ar",
    timeoutMs = 600_000,
  ) => {
    const form = new FormData();
    form.append("file", file);
    const lang = language.toLowerCase().startsWith("fr") ? "fr" : "ar";
    form.append("language", lang);
    return uploadRequest<{
      text: string;
      provider: string;
      language?: string | null;
      degraded?: boolean;
    }>("/api/dictation/transcribe", form, false, timeoutMs);
  },

  getDictationSttStatus: () =>
    request<{
      enabled: boolean;
      model: string;
      device: string;
      loaded: boolean;
      languages?: string[];
      local_only?: boolean;
    }>("/api/dictation/stt-status"),

  composeDictation: (data: {
    text: string;
    doc_type?: "plaidoirie" | "general" | "petition" | "memo" | "letter" | "minutes";
    title?: string;
    polish_first?: boolean;
    plaidoirie_type?: string;
    language?: "ar" | "fr";
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
    }>("/api/dictation/compose", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  listCabinetPlaidoirieTemplates: () =>
    request<CabinetPlaidoirieTemplate[]>("/api/plaidoirie-templates"),

  createCabinetPlaidoirieTemplate: (data: {
    name: string;
    body: string;
    base_type?: string;
  }) =>
    request<CabinetPlaidoirieTemplate>("/api/plaidoirie-templates", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateCabinetPlaidoirieTemplate: (
    id: string,
    data: { name?: string; body?: string; base_type?: string },
  ) =>
    request<CabinetPlaidoirieTemplate>(`/api/plaidoirie-templates/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  deleteCabinetPlaidoirieTemplate: (id: string) =>
    request<void>(`/api/plaidoirie-templates/${id}`, { method: "DELETE" }),

  /** Télécharge un .docx réel (Word) et déclenche l'enregistrement navigateur. */
  downloadPlaidoirieDocx: async (data: {
    title: string;
    body: string;
    cabinet_name?: string;
    lawyer_name?: string;
    city?: string;
  }) => {
    const token = getToken();
    const res = await fetch(`${API_URL}/api/plaidoirie-templates/export-docx`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(60_000),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({ detail: "Export Word échoué" }));
      throw new ApiError(
        typeof body.detail === "string" ? body.detail : "Export Word échoué",
        res.status,
      );
    }
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    const match = /filename="?([^"]+)"?/i.exec(cd);
    const filename = match?.[1] || "plaidoirie.docx";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    return filename;
  },

  getDocumentDownloadUrl: (id: string) =>
    `${API_URL}/api/documents/${id}/download`,

  getTeam: () => request<TeamMember[]>("/api/team"),

  getJoinCode: () => request<JoinCodeInfo>("/api/team/join-code"),

  regenerateJoinCode: () =>
    request<JoinCodeInfo>("/api/team/join-code/regenerate", { method: "POST" }),

  validateJoinCode: (code: string) =>
    request<{ valid: boolean }>("/api/team/join/validate", {
      method: "POST",
      body: JSON.stringify({ code }),
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

  getJoinRequests: () => request<MembershipRequestItem[]>("/api/team/requests"),

  approveJoinRequest: (id: string, role: string) =>
    request<TeamMember>(`/api/team/requests/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ role }),
    }),

  rejectJoinRequest: (id: string) =>
    request<{ message: string }>(`/api/team/requests/${id}/reject`, {
      method: "POST",
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

  getAdminCabinets: () => request<AdminCabinet[]>("/api/admin/cabinets"),

  updateCabinetStatus: (id: string, status: "active" | "suspended") =>
    request<{ message: string }>(`/api/admin/cabinets/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  getAdminMetrics: () => request<AdminMetrics>("/api/admin/metrics"),

  getAuditLogs: () => request<AuditLogItem[]>("/api/admin/audit-logs"),

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
};

export interface RegisterPayload {
  cabinet_name: string;
  city: string;
  address: string;
  barreau: string;
  ice?: string;
  manager_name: string;
  email: string;
  phone: string;
  password: string;
  email_otp: string;
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
  role: string;
  cabinet_id: string;
  cabinet_name: string;
  totp_enabled?: boolean;
  mfa_required?: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: AuthUser;
  mfa_setup_required?: boolean;
  captcha_required?: boolean;
}

export interface CaseListItem {
  id: string;
  reference: string;
  client_name: string;
  case_type: string;
  status: string;
  responsible_name: string;
  updated_at: string;
}

export interface CaseDetail extends CaseListItem {
  description?: string;
  opened_at: string;
  tags: string[];
}

export interface CreateCasePayload {
  client_name: string;
  case_type: string;
  status: string;
  description?: string;
  tags?: string[];
  responsible_id?: string;
  first_hearing_at?: string;
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

export interface CaseNoteItem {
  id: string;
  title: string;
  body: string;
  case_id?: string | null;
  case_reference?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CabinetPlaidoirieTemplate {
  id: string;
  name: string;
  body: string;
  base_type?: string | null;
  created_at: string;
  updated_at: string;
}

export interface CaseTaskItem {
  id: string;
  title: string;
  description?: string | null;
  case_id?: string | null;
  case_reference?: string | null;
  status: "todo" | "doing" | "done" | string;
  due_at?: string | null;
  created_at: string;
  updated_at: string;
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
  created_at: string;
}

export interface WorkspaceSummary {
  upcoming_events: AgendaEventItem[];
  open_tasks: CaseTaskItem[];
  recent_notes: CaseNoteItem[];
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
}

export interface MembershipRequestItem {
  id: string;
  full_name: string;
  email: string;
  status: string;
  requested_at: string;
  resolved_at?: string | null;
}

export interface CabinetSettings {
  id: string;
  name: string;
  city: string;
  address: string;
  barreau: string;
  ice?: string;
  ai_custom_prompt?: string | null;
  status: string;
}

export interface AdminCabinet {
  id: string;
  name: string;
  city: string;
  barreau: string;
  status: string;
  user_count: number;
  document_count: number;
  case_count: number;
  summarize_count: number;
  created_at: string;
}

export interface AdminMetrics {
  active_cabinets: number;
  suspended_cabinets: number;
  total_users: number;
  total_documents: number;
  ai_actions_today: number;
  avg_ocr_score: number;
}

export interface AuditLogItem {
  id: string;
  user_id: string | null;
  cabinet_id: string | null;
  action: string;
  ip_address: string | null;
  details: string | null;
  created_at: string;
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
