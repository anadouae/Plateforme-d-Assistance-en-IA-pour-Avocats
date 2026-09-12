import { redirect } from "next/navigation";

/** Vérification par lien supprimée — l'inscription utilise un code OTP par email. */
export default function VerifyEmailPage() {
  redirect("/login");
}
