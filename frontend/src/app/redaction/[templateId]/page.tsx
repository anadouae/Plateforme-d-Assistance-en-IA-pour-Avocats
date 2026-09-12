"use client";

import { Suspense, useEffect } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PlaidoirieWorkspace } from "@/components/redaction/plaidoirie-workspace";
import { useAuthStore } from "@/store/auth";
import { isAssistant } from "@/lib/roles";

function PlaidoirieWorkspaceInner() {
  const params = useParams<{ templateId: string }>();
  const searchParams = useSearchParams();
  const templateId = decodeURIComponent(String(params?.templateId || "libre"));
  const draftId = (searchParams.get("draft") || "").trim() || undefined;
  const initialCaseId =
    (searchParams.get("caseId") || searchParams.get("case_id") || "").trim() || undefined;
  const resume = searchParams.get("resume") === "1" && searchParams.get("fresh") !== "1";
  const fresh = searchParams.get("fresh") === "1";
  const user = useAuthStore((s) => s.user);
  const router = useRouter();
  const assistantMode = isAssistant(user?.role);

  useEffect(() => {
    if (assistantMode) router.replace("/redaction");
  }, [assistantMode, router]);

  if (assistantMode) return null;

  return (
    <AppShell>
      <PlaidoirieWorkspace
        key={
          draftId
            ? `draft-${draftId}`
            : fresh
              ? `fresh-${templateId}`
              : resume
                ? `resume-${templateId}`
                : `tpl-${templateId}-${initialCaseId || ""}`
        }
        templateId={templateId}
        draftId={draftId}
        initialCaseId={initialCaseId}
        resume={resume}
        fresh={fresh}
      />
    </AppShell>
  );
}

export default function PlaidoirieWorkspacePage() {
  return (
    <Suspense fallback={<div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">…</div>}>
      <PlaidoirieWorkspaceInner />
    </Suspense>
  );
}
