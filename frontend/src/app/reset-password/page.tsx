"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuthLayout } from "@/components/auth/auth-layout";
import { api } from "@/lib/api";
import { useTranslations } from "@/store/locale";

function ResetPasswordForm() {
  const auth = useTranslations().auth;
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const isInvite = searchParams.get("invite") === "1";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Anciens liens d'invitation → page d'activation dédiée
  useEffect(() => {
    if (isInvite && token) {
      router.replace(`/activate?token=${encodeURIComponent(token)}`);
    }
  }, [isInvite, token, router]);

  if (isInvite) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">
        Redirection vers l&apos;activation…
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password !== confirm) {
      setError(auth.pwdMismatch);
      return;
    }
    setLoading(true);
    try {
      await api.resetPassword(token, password);
      router.push("/login");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <Card className="border-sanad-gold/15 bg-white/90 shadow-xl shadow-sanad-gold/10 backdrop-blur-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-sanad-navy">Réinitialiser le mot de passe</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label={auth.password}
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            <Input
              label={auth.confirmPassword}
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
            />
            {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading || !token}>
              {loading ? "..." : "Réinitialiser"}
            </Button>
          </form>
          <Link href="/login" className="mt-4 block text-center text-sm text-sanad-gold hover:underline">
            {auth.signIn}
          </Link>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Chargement...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
