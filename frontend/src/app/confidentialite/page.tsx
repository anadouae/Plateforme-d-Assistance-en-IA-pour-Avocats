import { LegalPageLayout } from "@/components/layout/legal-page-layout";

export const metadata = {
  title: "Politique de confidentialité — LexHub",
  description: "Politique de confidentialité et protection des données de la plateforme LexHub.",
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
          L&apos;éditeur de la plateforme LexHub s&apos;engage à protéger la confidentialité
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
          aux données est strictement limité par rôle (avocat, admin cabinet, admin plateforme).
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
        <h2 className="text-xl font-semibold">Vos droits (loi 09-08)</h2>
        <p className="mt-3 text-sanad-muted">
          La loi marocaine n° 09-08 protège vos données personnelles (comme le RGPD en Europe).
          Concrètement, vous pouvez : <strong>voir</strong> quelles données LexHub détient sur vous,
          les <strong>corriger</strong>, demander leur <strong>suppression</strong>, ou en recevoir
          une copie (<strong>portabilité</strong>). Écrivez à{" "}
          <a href="mailto:contact@lexhub.space" className="text-sanad-gold hover:underline">
            contact@lexhub.space
          </a>{" "}
          — nous répondons dans un délai raisonnable. Le RGPD s’applique en plus si vous
          traitez des données de personnes dans l’UE ; sinon, la 09-08 suffit au Maroc.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Cookies et stockage local</h2>
        <p className="mt-3 text-sanad-muted">
          LexHub n’utilise <strong>aucun cookie publicitaire</strong>, ni Google Analytics, ni
          pixel de tracking. Pour rester connecté, le jeton d’authentification (JWT) est stocké
          dans le navigateur (<code>localStorage</code> / <code>sessionStorage</code>) — ce n’est
          pas un cookie marketing. Langue, densité d’affichage et thème sont aussi mémorisés
          localement, uniquement sur votre machine. Aucun bandeau « Accepter les cookies » n’est
          requis : il n’y a pas de traceurs optionnels.
        </p>
      </section>

      <p className="text-sm text-sanad-muted">
        Dernière mise à jour : juillet 2026
      </p>
    </LegalPageLayout>
  );
}
