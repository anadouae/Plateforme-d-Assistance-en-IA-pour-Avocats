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

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-sanad-cream px-4 text-center">
      <AlertTriangle className="mb-4 h-12 w-12 text-amber-600" />
      <h1 className="text-2xl font-bold text-sanad-slate">Une erreur est survenue</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        Le service a rencontré un problème inattendu. Réessayez ou retournez au tableau de bord.
      </p>
      <div className="mt-6 flex gap-3">
        <Button onClick={reset}>Réessayer</Button>
        <Link href="/dashboard">
          <Button variant="outline">Tableau de bord</Button>
        </Link>
      </div>
    </div>
  );
}
