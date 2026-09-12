import { redirect } from "next/navigation";

/** Magic link désactivé — connexion par mot de passe uniquement. */
export default function MagicLoginPage() {
  redirect("/login");
}
