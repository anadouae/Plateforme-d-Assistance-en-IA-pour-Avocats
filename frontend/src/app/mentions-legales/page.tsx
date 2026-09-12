import { LegalPageLayout } from "@/components/layout/legal-page-layout";

export const metadata = {
  title: "Mentions légales — LexHub",
  description: "Mentions légales de la plateforme LexHub (lexhub.space).",
};

export default function MentionsLegalesPage() {
  return (
    <LegalPageLayout
      title="Mentions légales"
      subtitle="Informations légales relatives à la plateforme LexHub"
    >
      <section>
        <h2 className="text-xl font-semibold">Éditeur</h2>
        <p className="mt-3 text-sanad-muted">
          La plateforme <strong>LexHub</strong> (marque commerciale « LexHub — Avocat AI Assistance »)
          est éditée et exploitée sous le nom LexHub, accessible à l’adresse{" "}
          <strong>https://lexhub.space</strong>.
        </p>
        <ul className="mt-3 list-inside list-disc space-y-1 text-sanad-muted">
          <li>Pays d’exploitation : Maroc</li>
          <li>
            Contact :{" "}
            <a href="mailto:contact@lexhub.space" className="text-sanad-gold hover:underline">
              contact@lexhub.space
            </a>
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Directeur de la publication</h2>
        <p className="mt-3 text-sanad-muted">
          Le directeur de la publication est le responsable légal de LexHub, joignable à l’adresse
          de contact ci-dessus.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Hébergement</h2>
        <p className="mt-3 text-sanad-muted">
          Les services et données de LexHub sont hébergés sur une infrastructure cloud sécurisée
          (serveur virtuel dédié), avec chiffrement des communications (HTTPS/TLS) et mesures de
          protection adaptées aux données professionnelles sensibles. L’hébergeur de l’infrastructure
          est OVH SAS — 2 rue Kellermann, 59100 Roubaix, France — pour le serveur d’application
          accessible via lexhub.space.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Propriété intellectuelle</h2>
        <p className="mt-3 text-sanad-muted">
          L’ensemble des éléments composant le site et la plateforme LexHub (textes, graphismes,
          logiciels, marques, logos, bases de données) est protégé par le droit de la propriété
          intellectuelle. Toute reproduction, représentation ou exploitation non autorisée est
          interdite.
        </p>
        <p className="mt-3 text-sanad-muted">
          Les documents, dossiers et contenus déposés par les utilisateurs demeurent la propriété
          des cabinets concernés ; LexHub n’acquiert qu’une licence technique limitée nécessaire
          au fonctionnement du service.
        </p>
      </section>

      <section>
        <h2 className="text-xl font-semibold">Responsabilité</h2>
        <p className="mt-3 text-sanad-muted">
          LexHub est un outil d’assistance juridique destiné aux cabinets d’avocats. Les contenus
          générés par l’intelligence artificielle ne constituent pas un avis juridique et ne se
          substituent pas au jugement professionnel de l’avocat. LexHub s’efforce d’assurer la
          disponibilité et la sécurité du service, sans garantir l’absence d’erreur dans les
          contenus produits par l’IA. L’utilisateur demeure seul responsable des actes, écritures
          et décisions prises dans le cadre de son activité professionnelle.
        </p>
      </section>
    </LegalPageLayout>
  );
}
