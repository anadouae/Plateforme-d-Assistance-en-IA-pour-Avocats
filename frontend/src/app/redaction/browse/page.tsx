"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

/** Ancienne URL — le parcours modèles est sur /redaction. */
export default function RedactionBrowseRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/redaction");
  }, [router]);
  return null;
}
