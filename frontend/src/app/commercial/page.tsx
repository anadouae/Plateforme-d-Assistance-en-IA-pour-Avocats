import { redirect } from "next/navigation";

/** Ancien formulaire Entreprise / Sur mesure — tout passe par /tarifs (essai self-serve). */
export default function CommercialRedirectPage() {
  redirect("/tarifs");
}
