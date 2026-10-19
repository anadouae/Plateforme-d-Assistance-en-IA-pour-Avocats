import type { AuthUser } from "@/lib/api";

/** Mot de passe LexHub requis (pas les comptes Google). */
export function needsLexhubPassword(user: AuthUser | null | undefined): boolean {
  if (!user) return false;
  if (user.auth_via_google) return false;
  return Boolean(user.must_set_password);
}
