"use client";

import { Suspense, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuthLayout } from "@/components/auth/auth-layout";
import { api } from "@/lib/api";

function ActivateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    if (password.length < 8) {
      setError("Le mot de passe doit contenir au moins 8 caractères.");
      return;
    }
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas.");
      return;
    }
    setLoading(true);
    try {
      await api.resetPassword(token, password);
      router.push("/login?activated=1");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lien invalide ou expiré.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <Card className="border-sanad-gold/15 bg-white/90 shadow-xl shadow-sanad-gold/10 backdrop-blur-sm">
        <CardHeader className="text-center">
          <CardTitle className="text-sanad-navy">Activer mon compte</CardTitle>
          <p className="mt-2 text-sm text-slate-500">
            Choisissez votre mot de passe pour rejoindre le cabinet sur Sanad.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Mot de passe"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
            />
            <Input
              label="Confirmer le mot de passe"
              type="password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              required
              autoComplete="new-password"
            />
            {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading || !token}>
              {loading ? "Activation…" : "Activer mon compte"}
            </Button>
          </form>
          <Link href="/login" className="mt-4 block text-center text-sm text-sanad-gold hover:underline">
            Déjà un compte ? Se connecter
          </Link>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}

export default function ActivatePage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Chargement...</div>}>
      <ActivateForm />
    </Suspense>
  );
}
