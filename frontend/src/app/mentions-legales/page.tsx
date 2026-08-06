import { LegalPageLayout } from "@/components/layout/legal-page-layout";

export const metadata = {
  title: "Mentions légales — Sanad",
  description: "Mentions légales de la plateforme Sanad, éditée par WebVoice.",
};

export default function MentionsLegalesPage() {
  return (
    <LegalPageLayout
      title="Mentions légales"
      subtitle="Informations légales relatives à la plateforme Sanad"
    >
      <section>
        <h2 className="text-xl font-semibold">Éditeur du site</h2>
        <p className="mt-3 text-sanad-muted">
          La plateforme <strong>Sanad — Avocat AI Assistance</strong> est éditée par :
        </p>
        <ul className="mt-3 list-inside list-disc space-y-1 text-sanad-muted">
          <li><strong>WebVoice</strong></li>
          <li>Maroc</li>
          <li>Contact : <a href="mailto:contact@webvoice.ma" className="text-sanad-gold hover:underline">contact@webvoice.ma</a></li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Directeur de la publication</h2>
        <p className="mt-3 text-sanad-muted">
          Le directeur de la publication est le représentant légal de WebVoice.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Hébergement</h2>
        <p className="mt-3 text-sanad-muted">
          Les données de la plateforme Sanad sont hébergées sur une infrastructure cloud sécurisée,
          conforme aux exigences de disponibilité et de protection des données applicables au Maroc
          et au Règlement Général sur la Protection des Données (RGPD) pour les utilisateurs concernés.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Propriété intellectuelle</h2>
        <p className="mt-3 text-sanad-muted">
          L&apos;ensemble des éléments composant le site et la plateforme Sanad (textes, graphismes,
          logiciels, marques, logos, base de données) est protégé par le droit de la propriété
          intellectuelle. Toute reproduction, représentation ou exploitation non autorisée est interdite.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Responsabilité</h2>
        <p className="mt-3 text-sanad-muted">
          Sanad est un outil d&apos;assistance juridique à destination des cabinets d&apos;avocats.
          Les réponses générées par l&apos;assistant IA ne constituent pas un avis juridique et ne
          se substituent pas au jugement professionnel de l&apos;avocat. WebVoice s&apos;efforce de
          garantir l&apos;exactitude des informations mais ne saurait être tenue responsable des
          décisions prises sur la base des contenus produits par la plateforme.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Droit applicable</h2>
        <p className="mt-3 text-sanad-muted">
          Les présentes mentions légales sont régies par le droit marocain. En cas de litige,
          les tribunaux compétents du Royaume du Maroc seront seuls compétents.
        </p>
      </section>

      <p className="text-sm text-sanad-muted">
        Dernière mise à jour : juillet 2026
      </p>
    </LegalPageLayout>
  );
}
