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

function clearTokenStorages() {
  if (typeof window === "undefined") return;
  localStorage.removeItem("sanad_token");
  localStorage.removeItem("sanad_refresh_token");
  sessionStorage.removeItem("sanad_token");
  sessionStorage.removeItem("sanad_refresh_token");
}

function writeTokens(data: AuthResponse, remember: boolean) {
  clearTokenStorages();
  const storage = remember ? localStorage : sessionStorage;
  storage.setItem("sanad_token", data.access_token);
  storage.setItem("sanad_refresh_token", data.refresh_token);
  localStorage.setItem("sanad_remember", remember ? "1" : "0");
}

function readFlatToken(): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem("sanad_token") || localStorage.getItem("sanad_token");
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
        clearTokenStorages();
        localStorage.removeItem("sanad_remember");
        set({ user: null, token: null });
      },
      isAuthenticated: () => {
        const token = get().token;
        if (typeof window === "undefined") return !!token;
        return !!(token || readFlatToken());
      },
    }),
    {
      name: "sanad-auth",
      partialize: (s) => ({ user: s.user, token: s.token }),
      onRehydrateStorage: () => (state) => {
        state?.setHasHydrated(true);
        if (typeof window === "undefined" || !state?.token) return;
        const remember = localStorage.getItem("sanad_remember") !== "0";
        const storage = remember ? localStorage : sessionStorage;
        if (!storage.getItem("sanad_token")) {
          storage.setItem("sanad_token", state.token);
        }
      },
    },
  ),
);

if (typeof window !== "undefined") {
  window.addEventListener("sanad-auth-updated", (event) => {
    const data = (event as CustomEvent<AuthResponse>).detail;
    useAuthStore.setState({ user: data.user, token: data.access_token });
  });
  window.addEventListener("sanad-auth-cleared", () => {
    useAuthStore.setState({ user: null, token: null });
  });
}
