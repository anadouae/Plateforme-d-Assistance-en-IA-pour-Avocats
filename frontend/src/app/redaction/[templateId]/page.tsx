"use client";

import { use } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { PlaidoirieWorkspace } from "@/components/redaction/plaidoirie-workspace";
import { useAuthStore } from "@/store/auth";
import { isAssistant } from "@/lib/roles";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function PlaidoirieWorkspacePage({
  params,
}: {
  params: Promise<{ templateId: string }>;
}) {
  const { templateId } = use(params);
  const user = useAuthStore((s) => s.user);
  const router = useRouter();
  const assistantMode = isAssistant(user?.role);

  useEffect(() => {
    if (assistantMode) router.replace("/redaction");
  }, [assistantMode, router]);

  if (assistantMode) return null;

  return (
    <AppShell>
      <PlaidoirieWorkspace templateId={decodeURIComponent(templateId)} />
    </AppShell>
  );
}
