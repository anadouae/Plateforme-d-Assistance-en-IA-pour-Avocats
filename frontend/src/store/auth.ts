import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AuthResponse } from "@/lib/api";

interface AuthState {
  user: AuthResponse["user"] | null;
  token: string | null;
  _hasHydrated: boolean;
  setHasHydrated: (v: boolean) => void;
  setAuth: (data: AuthResponse, options?: { remember?: boolean }) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

const ACCESS_KEYS = ["lexhub_token", "sanad_token"] as const;
const REFRESH_KEYS = ["lexhub_refresh_token", "sanad_refresh_token"] as const;
const REMEMBER_KEYS = ["lexhub_remember", "sanad_remember"] as const;

function clearTokenStorages() {
  if (typeof window === "undefined") return;
  for (const k of ACCESS_KEYS) {
    localStorage.removeItem(k);
    sessionStorage.removeItem(k);
  }
  // Ne plus stocker le refresh en JS (cookie HttpOnly) — nettoyer l’héritage
  for (const k of REFRESH_KEYS) {
    localStorage.removeItem(k);
    sessionStorage.removeItem(k);
  }
}

function writeTokens(data: AuthResponse, remember: boolean) {
  clearTokenStorages();
  const storage = remember ? localStorage : sessionStorage;
  // Access token seulement — le refresh passe par cookie HttpOnly
  storage.setItem("lexhub_token", data.access_token);
  localStorage.setItem("lexhub_remember", remember ? "1" : "0");
  localStorage.removeItem("sanad_remember");
}

function readFlatToken(): string | null {
  if (typeof window === "undefined") return null;
  return (
    sessionStorage.getItem("lexhub_token") ||
    localStorage.getItem("lexhub_token") ||
    sessionStorage.getItem("sanad_token") ||
    localStorage.getItem("sanad_token")
  );
}

function rememberPref(): boolean {
  const v =
    localStorage.getItem("lexhub_remember") ?? localStorage.getItem("sanad_remember");
  return v !== "0";
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      _hasHydrated: false,
      setHasHydrated: (v) => set({ _hasHydrated: v }),
      setAuth: (data, options) => {
        const remember = options?.remember ?? true;
        writeTokens(data, remember);
        set({ user: data.user, token: data.access_token });
      },
      logout: () => {
        // Appeler l’API AVANT de vider le token (rappel e-mail set-password)
        const doClear = () => {
          clearTokenStorages();
          for (const k of REMEMBER_KEYS) localStorage.removeItem(k);
          try {
            localStorage.removeItem("lexhub-auth");
            localStorage.removeItem("sanad-auth");
          } catch {
            /* ignore */
          }
          set({ user: null, token: null });
        };
        if (typeof window !== "undefined") {
          void import("@/lib/api")
            .then(({ api }) => api.logout())
            .catch(() => undefined)
            .finally(doClear);
        } else {
          doClear();
        }
      },
      isAuthenticated: () => {
        const token = get().token;
        if (typeof window === "undefined") return !!token;
        return !!(token || readFlatToken());
      },
    }),
    {
      name: "lexhub-auth",
      skipHydration: true,
      partialize: (s) => ({ user: s.user, token: s.token }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        if (typeof window === "undefined" || !state?.token) return;
        const storage = rememberPref() ? localStorage : sessionStorage;
        if (!storage.getItem("lexhub_token") && !storage.getItem("sanad_token")) {
          storage.setItem("lexhub_token", state.token);
        }
      },
    },
  ),
);

if (typeof window !== "undefined") {
  const schedule =
    typeof requestAnimationFrame === "function"
      ? (fn: () => void) => requestAnimationFrame(() => setTimeout(fn, 0))
      : (fn: () => void) => setTimeout(fn, 0);
  schedule(() => {
    void useAuthStore.persist.rehydrate();
    // Migration persist name sanad-auth → lexhub-auth
    try {
      const legacy = localStorage.getItem("sanad-auth");
      if (legacy && !localStorage.getItem("lexhub-auth")) {
        localStorage.setItem("lexhub-auth", legacy);
      }
    } catch {
      /* ignore */
    }
  });
  window.addEventListener("sanad-auth-updated", (event) => {
    const data = (event as CustomEvent<AuthResponse>).detail;
    useAuthStore.setState({ user: data.user, token: data.access_token });
  });
  window.addEventListener("lexhub-auth-updated", (event) => {
    const data = (event as CustomEvent<AuthResponse>).detail;
    useAuthStore.setState({ user: data.user, token: data.access_token });
  });
  window.addEventListener("sanad-auth-cleared", () => {
    useAuthStore.setState({ user: null, token: null });
  });
  window.addEventListener("lexhub-auth-cleared", () => {
    useAuthStore.setState({ user: null, token: null });
  });
}
