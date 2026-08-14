"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PlaidoirieWorkspace } from "@/components/redaction/plaidoirie-workspace";
import { useAuthStore } from "@/store/auth";
import { isAssistant } from "@/lib/roles";

export default function PlaidoirieWorkspacePage() {
  const params = useParams<{ templateId: string }>();
  const templateId = decodeURIComponent(String(params?.templateId || "libre"));
  const user = useAuthStore((s) => s.user);
  const router = useRouter();
  const assistantMode = isAssistant(user?.role);

  useEffect(() => {
    if (assistantMode) router.replace("/redaction");
  }, [assistantMode, router]);

  if (assistantMode) return null;

  return (
    <AppShell>
      <PlaidoirieWorkspace templateId={templateId} />
    </AppShell>
  );
}
