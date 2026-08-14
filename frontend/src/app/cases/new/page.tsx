"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { NewCaseModal } from "@/components/cases/new-case-modal";

/** Conserve l’URL /cases/new — ouvre le modal de création. */
export default function NewCasePage() {
  const router = useRouter();
  const [open, setOpen] = useState(true);

  useEffect(() => {
    setOpen(true);
  }, []);

  return (
    <AppShell>
      <NewCaseModal
        open={open}
        onClose={() => {
          setOpen(false);
          router.replace("/cases");
        }}
      />
    </AppShell>
  );
}
