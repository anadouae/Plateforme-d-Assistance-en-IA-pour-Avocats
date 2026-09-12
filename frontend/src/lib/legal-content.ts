/** Textes légaux — aperçu + lecture intégrée à l'inscription. */

export type LegalDocId = "terms" | "privacy";

export type LegalSection = { title: string; paragraphs: string[] };

export type LegalDocContent = {
  title: string;
  preview: string;
  sections: LegalSection[];
};

const termsFr: LegalDocContent = {
  title: "Conditions d'utilisation",
  preview:
    "LexHub est un outil d'assistance juridique pour cabinets marocains. Les contenus IA ne remplacent pas le jugement de l'avocat. Cliquez pour lire l'intégralité.",
  sections: [
    {
      title: "Objet du service",
      paragraphs: [
        "LexHub — Avocat AI Assistance est une plateforme SaaS destinée aux cabinets d'avocats marocains : gestion de dossiers, synthèse documentaire, rédaction et dictée de plaidoiries.",
        "L'utilisation implique l'acceptation des présentes conditions et du secret professionnel applicable à votre activité.",
      ],
    },
    {
      title: "Responsabilité",
      paragraphs: [
        "LexHub est un outil d'assistance. Les réponses générées par l'IA ne constituent pas un avis juridique et ne se substituent pas au jugement professionnel de l'avocat.",
        "L'utilisateur reste seul responsable des actes, conclusions et pièces produits devant les juridictions.",
      ],
    },
    {
      title: "Propriété intellectuelle",
      paragraphs: [
        "Les éléments de la plateforme (logiciels, marques, interface) sont protégés. Les documents que vous déposez restent votre propriété ; vous accordez à LexHub une licence technique limitée pour les traiter dans votre espace cabinet.",
      ],
    },
    {
      title: "Hébergement",
      paragraphs: [
        "Les données sont hébergées sur une infrastructure cloud sécurisée (lexhub.space), avec chiffrement en transit et au repos.",
        "Pour toute question relative au service : contact@lexhub.space",
      ],
    },
  ],
};

const privacyFr: LegalDocContent = {
  title: "Politique de confidentialité",
  preview:
    "Vos dossiers et dictées restent dans votre espace cabinet. Chiffrement AES-256, accès par rôle, aucune revente de données. Cliquez pour le détail.",
  sections: [
    {
      title: "Données collectées",
      paragraphs: [
        "Identité et coordonnées professionnelles, informations du cabinet, documents juridiques uploadés, traces d'usage IA métier, logs techniques de connexion.",
      ],
    },
    {
      title: "Finalités",
      paragraphs: [
        "Fournir et améliorer les fonctionnalités, authentifier les comptes, indexer vos documents (RAG), respecter les obligations légales.",
        "Aucune donnée client n'est utilisée pour entraîner des modèles d'IA tiers.",
      ],
    },
    {
      title: "Sécurité",
      paragraphs: [
        "Chiffrement AES-256 au repos, TLS 1.3 en transit. Accès limité par rôle (avocat, admin cabinet, admin plateforme).",
      ],
    },
    {
      title: "Vos droits (loi 09-08)",
      paragraphs: [
        "La loi marocaine 09-08 vous permet de consulter, corriger, supprimer ou récupérer vos données. Écrivez à contact@lexhub.space. Le RGPD s’ajoute uniquement si des données de personnes dans l’UE sont concernées.",
      ],
    },
  ],
};

const termsAr: LegalDocContent = {
  title: "شروط الاستخدام",
  preview:
    "LexHub أداة مساعدة قانونية لمكاتب المحاماة المغربية. مخرجات الذكاء الاصطناعي لا تغني عن حكم المحامي. انقروا للقراءة الكاملة.",
  sections: termsFr.sections.map((s, i) => ({
    title: s.title,
    paragraphs: s.paragraphs,
  })),
};

const privacyAr: LegalDocContent = {
  title: "سياسة الخصوصية",
  preview:
    "ملفاتكم ومرافعاتكم تبقى في فضاء مكتبكم. تشفير AES-256، صلاحيات حسب الدور، لا بيع للبيانات. انقروا للتفاصيل.",
  sections: privacyFr.sections,
};

export function getLegalDoc(id: LegalDocId, locale: "fr" | "ar"): LegalDocContent {
  if (locale === "ar") {
    return id === "terms" ? termsAr : privacyAr;
  }
  return id === "terms" ? termsFr : privacyFr;
}
