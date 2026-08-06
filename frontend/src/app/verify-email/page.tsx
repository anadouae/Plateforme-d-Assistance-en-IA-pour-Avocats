import { Suspense } from "react";
import VerifyEmailContent from "./verify-email-content";

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-sanad-cream">
          <p className="text-sanad-muted">Chargement...</p>
        </div>
      }
    >
      <VerifyEmailContent />
    </Suspense>
  );
}
