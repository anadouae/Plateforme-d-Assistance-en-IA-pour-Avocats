"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { AuthLayout } from "@/components/auth/auth-layout";
import { api, ApiError } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

function MagicLoginInner() {
  const searchParams = useSearchParams();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");
  const [error, setError] = useState("");

  useEffect(() => {
    const token = searchParams.get("token");
    if (!token) {
      setStatus("error");
      setError("Lien invalide.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api.magicLogin(token);
        if (cancelled) return;
        setAuth(data, { remember: true });
        setStatus("ok");
        const dest = data.user.role === "admin_webvoice" ? "/admin" : "/dashboard";
        window.location.assign(dest);
      } catch (err) {
        if (cancelled) return;
        setStatus("error");
        setError(err instanceof ApiError ? err.message : "Lien invalide ou expiré.");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [searchParams, setAuth]);

  return (
    <AuthLayout>
      <div className="rounded-3xl border border-white/50 bg-white/90 p-8 text-center shadow-royal">
        {status === "loading" && (
          <p className="font-serif text-sanad-navy">Connexion en cours…</p>
        )}
        {status === "ok" && (
          <p className="font-serif text-sanad-navy">Redirection vers votre espace…</p>
        )}
        {status === "error" && (
          <div className="space-y-4">
            <p className="text-sm text-red-600">{error}</p>
            <Link href="/login" className="text-sm font-medium text-sanad-navy underline">
              Demander un nouveau lien
            </Link>
          </div>
        )}
      </div>
    </AuthLayout>
  );
}

export default function MagicLoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-sanad-cream">
          <p className="text-sanad-muted">Chargement…</p>
        </div>
      }
    >
      <MagicLoginInner />
    </Suspense>
  );
}
