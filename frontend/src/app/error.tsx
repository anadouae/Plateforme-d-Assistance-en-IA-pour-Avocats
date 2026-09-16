"use client";

import { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  const detail = error?.message || error?.digest || "";

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-sanad-cream px-4 text-center">
      <AlertTriangle className="mb-4 h-12 w-12 text-amber-600" />
      <h1 className="text-2xl font-bold text-sanad-slate">Une erreur est survenue</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        Le service a rencontré un problème inattendu. Réessayez ou retournez au tableau de bord.
      </p>
      {detail ? (
        <p className="mt-3 max-w-lg break-words rounded-lg bg-white/80 px-3 py-2 font-mono text-[11px] text-red-700">
          {detail}
        </p>
      ) : null}
      <div className="mt-6 flex gap-3">
        <Button onClick={reset}>Réessayer</Button>
        <Link href="/dashboard">
          <Button variant="outline">Tableau de bord</Button>
        </Link>
        <Link href="/admin">
          <Button variant="outline">Admin</Button>
        </Link>
      </div>
    </div>
  );
}
