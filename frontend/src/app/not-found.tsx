import Link from "next/link";
import { AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-sanad-cream px-4 text-center">
      <AlertCircle className="mb-4 h-12 w-12 text-sanad-blue" />
      <h1 className="text-2xl font-bold text-sanad-slate">Page introuvable</h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        La ressource demandée n&apos;existe pas ou a été déplacée.
      </p>
      <Link href="/dashboard" className="mt-6">
        <Button>Retour au tableau de bord</Button>
      </Link>
    </div>
  );
}
