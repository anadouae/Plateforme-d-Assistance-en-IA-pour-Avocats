"use client";

import { useState } from "react";
import Link from "next/link";
import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuthLayout } from "@/components/auth/auth-layout";
import { api } from "@/lib/api";
import { useTranslations } from "@/store/locale";

export default function ForgotPasswordPage() {
  const auth = useTranslations().auth;
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.forgotPassword(email);
      setSent(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthLayout>
      <Card className="border-sanad-gold/15 bg-white/90 shadow-xl shadow-sanad-gold/10 backdrop-blur-sm">
        <CardHeader className="text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-sanad-gold/15">
            <Mail className="h-6 w-6 text-sanad-gold" />
          </div>
          <CardTitle className="text-sanad-navy">{auth.forgot}</CardTitle>
        </CardHeader>
        <CardContent>
          {sent ? (
            <p className="text-center text-sm text-sanad-muted">
              Si un compte existe avec cette adresse, un email sera envoyé.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label={auth.email}
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={auth.emailPlaceholder}
                required
              />
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? "..." : "Envoyer le lien"}
              </Button>
            </form>
          )}
          <Link href="/login" className="mt-4 block text-center text-sm text-sanad-gold hover:underline">
            {auth.signIn}
          </Link>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}
