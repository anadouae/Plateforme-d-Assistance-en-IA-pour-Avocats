"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { CheckCircle, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuthLayout } from "@/components/auth/auth-layout";
import { api } from "@/lib/api";
import { useTranslations } from "@/store/locale";

function ConfirmEmailContent() {
  const auth = useTranslations().auth;
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      setMessage("Lien invalide.");
      return;
    }
    api
      .verifyEmail(token)
      .then((res) => {
        setStatus("success");
        setMessage(res.message);
      })
      .catch((err) => {
        setStatus("error");
        setMessage(err instanceof Error ? err.message : "Erreur");
      });
  }, [token]);

  return (
    <AuthLayout>
      <Card className="border-sanad-gold/15 bg-white/90 text-center shadow-xl shadow-sanad-gold/10 backdrop-blur-sm">
        <CardHeader>
          {status === "loading" && <p className="text-sanad-muted">{auth.loading}</p>}
          {status === "success" && (
            <>
              <CheckCircle className="mx-auto h-12 w-12 text-sanad-gold" />
              <CardTitle className="text-sanad-navy">{auth.verifyTitle}</CardTitle>
            </>
          )}
          {status === "error" && (
            <>
              <XCircle className="mx-auto h-12 w-12 text-red-500" />
              <CardTitle className="text-sanad-navy">Erreur</CardTitle>
            </>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-sanad-muted">{message}</p>
          <Link href="/login">
            <Button variant="default">{auth.continueLogin}</Button>
          </Link>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}

export default function ConfirmEmailPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center">Chargement...</div>}>
      <ConfirmEmailContent />
    </Suspense>
  );
}
