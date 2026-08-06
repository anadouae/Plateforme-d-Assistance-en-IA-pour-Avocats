"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AuthLayout } from "@/components/auth/auth-layout";
import { api } from "@/lib/api";
import { useTranslations } from "@/store/locale";

export default function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const auth = useTranslations().auth;
  const [loading, setLoading] = useState(false);
  const email = searchParams.get("email") || auth.emailPlaceholder;

  return (
    <AuthLayout>
      <Card className="border-sanad-gold/15 bg-white/90 text-center shadow-xl shadow-sanad-gold/10 backdrop-blur-sm">
        <CardHeader>
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-full bg-sanad-gold/15">
            <Mail className="h-6 w-6 text-sanad-gold" />
          </div>
          <CardTitle className="text-sanad-navy">{auth.verifyTitle}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-sanad-muted">
            {auth.verifySent}{" "}
            <span className="font-medium text-sanad-navy">{email}</span>.
          </p>
          <p className="text-xs text-sanad-muted/80">{auth.verifyExpiry}</p>
          <Button
            variant="outline"
            className="w-full border-sanad-gold/20"
            disabled={loading}
            onClick={async () => {
              const addr = searchParams.get("email");
              if (addr) {
                setLoading(true);
                try {
                  await api.resendVerification(addr);
                } finally {
                  setLoading(false);
                }
              }
            }}
          >
            {auth.resend}
          </Button>
          <Link href="/login">
            <Button variant="ghost" className="w-full text-sanad-gold hover:text-sanad-gold">
              {auth.continueLogin}
            </Button>
          </Link>
        </CardContent>
      </Card>
    </AuthLayout>
  );
}
