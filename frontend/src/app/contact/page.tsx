import { Suspense } from "react";
import ContactPageInner from "./contact-content";

export default function ContactPage() {
  return (
    <Suspense
      fallback={
        <div className="flex min-h-screen items-center justify-center bg-[#F4F6FA] text-sm text-slate-600">
          …
        </div>
      }
    >
      <ContactPageInner />
    </Suspense>
  );
}
