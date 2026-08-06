import { LegalPageLayout } from "@/components/layout/legal-page-layout";

export const metadata = {
  title: "Politique de confidentialité — Sanad",
  description: "Politique de confidentialité et protection des données de la plateforme Sanad.",
};

export default function ConfidentialitePage() {
  return (
    <LegalPageLayout
      title="Politique de confidentialité"
      subtitle="Protection de vos données et respect de la vie privée"
    >
      <section>
        <h2 className="text-xl font-semibold">Introduction</h2>
        <p className="mt-3 text-sanad-muted">
          WebVoice, éditeur de la plateforme Sanad, s&apos;engage à protéger la confidentialité
          des données personnelles et professionnelles des cabinets d&apos;avocats et de leurs
          collaborateurs utilisant le service.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Données collectées</h2>
        <p className="mt-3 text-sanad-muted">Nous collectons les données suivantes :</p>
        <ul className="mt-3 list-inside list-disc space-y-1 text-sanad-muted">
          <li>Identité et coordonnées (nom, prénom, email professionnel)</li>
          <li>Informations du cabinet (raison sociale, barreau, numéro d&apos;inscription)</li>
          <li>Documents juridiques uploadés dans le cadre de l&apos;utilisation du service</li>
          <li>Traces d&apos;usage IA métier (synthèse, correction de plaidoirie)</li>
          <li>Données techniques (logs de connexion, adresse IP, navigateur)</li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Finalités du traitement</h2>
        <p className="mt-3 text-sanad-muted">Vos données sont traitées pour :</p>
        <ul className="mt-3 list-inside list-disc space-y-1 text-sanad-muted">
          <li>Fournir et améliorer les fonctionnalités de la plateforme</li>
          <li>Assurer l&apos;authentification et la sécurité des comptes</li>
          <li>Indexer et rechercher dans vos documents via le moteur RAG</li>
          <li>Respecter nos obligations légales et réglementaires</li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Sécurité des données</h2>
        <p className="mt-3 text-sanad-muted">
          Les documents sont chiffrés au repos (AES-256) et en transit (TLS 1.3). L&apos;accès
          aux données est strictement limité par rôle (avocat, admin cabinet, admin WebVoice).
          Aucune donnée client n&apos;est utilisée pour entraîner des modèles d&apos;IA tiers.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Conservation</h2>
        <p className="mt-3 text-sanad-muted">
          Les données sont conservées pendant la durée du contrat et supprimées dans un délai
          de 30 jours après résiliation du compte, sauf obligation légale de conservation.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Vos droits</h2>
        <p className="mt-3 text-sanad-muted">
          Conformément à la loi marocaine n° 09-08 et au RGPD le cas échéant, vous disposez d&apos;un
          droit d&apos;accès, de rectification, de suppression et de portabilité de vos données.
          Pour exercer ces droits :{" "}
          <a href="mailto:contact@webvoice.ma" className="text-sanad-gold hover:underline">
            contact@webvoice.ma
          </a>
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Cookies</h2>
        <p className="mt-3 text-sanad-muted">
          Sanad utilise uniquement des cookies strictement nécessaires au fonctionnement
          (session d&apos;authentification JWT). Aucun cookie publicitaire ou de tracking tiers
          n&apos;est déployé.
        </p>
      </section>

      <p className="text-sm text-sanad-muted">
        Dernière mise à jour : juillet 2026
      </p>
    </LegalPageLayout>
  );
}
