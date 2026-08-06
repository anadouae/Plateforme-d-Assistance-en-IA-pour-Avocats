"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/auth";
import type { CabinetRole } from "@/lib/roles";

/** Redirige vers /dashboard si le rôle n'est pas autorisé. */
export function RoleGate({
  allow,
  children,
}: {
  allow: CabinetRole[];
  children: React.ReactNode;
}) {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const allowed = !!user && allow.includes(user.role as CabinetRole);

  useEffect(() => {
    if (user && !allowed) {
      router.replace("/dashboard");
    }
  }, [user, allowed, router]);

  if (!user || !allowed) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center text-sm text-slate-500">
        Redirection…
      </div>
    );
  }

  return <>{children}</>;
}
