import { HomePageContent } from "@/components/home/home-page-content";

/** Évite le cache RSC / soft-nav qui affiche parfois une ancienne vue d’onglet. */
export const dynamic = "force-dynamic";
export const revalidate = 0;

export default function HomePage() {
  return <HomePageContent />;
}
