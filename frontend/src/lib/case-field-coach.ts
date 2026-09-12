/** Aide contextuelle à la création de dossier — texte métier, pas du jargon. */

export type CoachKey =
  | "client"
  | "domain"
  | "degree"
  | "city"
  | "tribunal"
  | "role"
  | "quality"
  | "domicile"
  | "opposing"
  | "opposingQuality"
  | "opposingDomicile"
  | "rg"
  | "chamber"
  | "greffe"
  | "judge"
  | "procedure"
  | "responsible"
  | "status"
  | "hearing";

export type CoachCopy = { title: string; why: string; example: string };

export const CASE_FIELD_COACH: Record<CoachKey, { fr: CoachCopy; ar: CoachCopy }> = {
  client: {
    fr: {
      title: "Nom du client (votre mandant)",
      why: "C’est la personne ou la société que vous défendez. L’IA s’en sert pour l’en-tête et pour ne pas inverser les parties.",
      example: "Fatima Alami — ou « Sté Atlas Textile SARL » si c’est une société.",
    },
    ar: {
      title: "اسم الموكل",
      why: "الشخص أو الشركة التي تنوبون عنها. يستعمله الذكاء للترويسة حتى لا تُعكس الأطراف.",
      example: "فاطمة العلمي — أو « شركة أطلس للنسيج ش.م.م » إن كانت شركة.",
    },
  },
  domain: {
    fr: {
      title: "Matière du dossier",
      why: "Famille, civil, commercial… Cela oriente le type de plaidoirie et les rôles (demandeur / époux, etc.).",
      example: "Pour une pension alimentaire + garde : choisissez Famille.",
    },
    ar: {
      title: "مادة الملف",
      why: "أسرة، مدني، تجاري… يوجّه نوع المرافعة وأدوار الأطراف.",
      example: "للنفقة والحضانة: اختاروا أسرة.",
    },
  },
  degree: {
    fr: {
      title: "Degré de juridiction",
      why: "Où en est l’affaire : première instance, appel ou cassation. Ça change le tribunal proposé.",
      example: "Première affaire au TPI → Première instance.",
    },
    ar: {
      title: "درجة التقاضي",
      why: "أين الملف: ابتدائي، استئناف أو نقض. يغيّر المحكمة المقترحة.",
      example: "أول عرض أمام الابتدائية → الدرجة الأولى.",
    },
  },
  city: {
    fr: {
      title: "Ville du tribunal",
      why: "Ville où siège la juridiction saisie — pas forcément la ville de votre cabinet.",
      example: "Cabinet à Casablanca, affaire à Rabat → choisissez Rabat.",
    },
    ar: {
      title: "مدينة المحكمة",
      why: "مدينة المحكمة المختصة — قد تختلف عن مدينة المكتب.",
      example: "المكتب بالدار البيضاء والملف بالرباط → اختاروا الرباط.",
    },
  },
  tribunal: {
    fr: {
      title: "Tribunal compétent",
      why: "Le siège exact (TPI, commerce, appel…). Liste indicative : vérifiez toujours la compétence.",
      example: "Affaire famille à Rabat → Tribunal de première instance de Rabat.",
    },
    ar: {
      title: "المحكمة المختصة",
      why: "المقر بالضبط (ابتدائية، تجارية، استئناف…). القائمة إرشادية: تحققوا من الاختصاص.",
      example: "ملف أسرة بالرباط → المحكمة الابتدائية بالرباط.",
    },
  },
  role: {
    fr: {
      title: "Rôle de votre client",
      why: "Demandeur = celui qui saisit. Défendeur = celui qui est assigné. En famille : souvent l’époux(se) demandeur(se).",
      example: "Vous déposez la requête en nafaka pour Fatima → Demandeur / طالبة.",
    },
    ar: {
      title: "دور موكلكم",
      why: "مدّع = من رفع الدعوى. مدعى عليه = من رُفعت عليه. في الأسرة غالباً الزوج(ة) المدّعي(ة).",
      example: "تودعون مقال النفقة لفاطمة → مدّعية.",
    },
  },
  quality: {
    fr: {
      title: "Nature du client",
      why: "Personne physique (un particulier) ou morale (société). Utile pour l’identité juridique et l’export.",
      example: "Fatima Alami = personne physique.",
    },
    ar: {
      title: "طبيعة الموكل",
      why: "شخص طبيعي أو شخص اعتباري (شركة). مفيد للهوية القانونية والتصدير.",
      example: "فاطمة العلمي = شخص طبيعي.",
    },
  },
  domicile: {
    fr: {
      title: "Domicile / siège du client",
      why: "Adresse pour les actes. Facultatif à l’ouverture, recommandé pour la plaidoirie.",
      example: "Hay Riad, avenue Annakhil, immeuble 12, Rabat.",
    },
    ar: {
      title: "موطن / مقر الموكل",
      why: "العنوان للتبليغ. اختياري عند الفتح، مستحسن للمرافعة.",
      example: "حي الرياض، شارع النخيل، عمارة 12، الرباط.",
    },
  },
  opposing: {
    fr: {
      title: "Partie adverse",
      why: "L’autre partie. L’IA ne l’invente pas : si vous le saisissez ici, il reste stable dans le dossier.",
      example: "Karim Bennani.",
    },
    ar: {
      title: "الطرف المقابل",
      why: "الخصم. الذكاء لا يختلقه: إن كتبتموه هنا يبقى ثابتاً في الملف.",
      example: "كريم بناني.",
    },
  },
  opposingQuality: {
    fr: {
      title: "Nature de l’adverse",
      why: "Particulier ou société, comme pour votre client.",
      example: "Karim Bennani = personne physique.",
    },
    ar: {
      title: "طبيعة الطرف المقابل",
      why: "شخص طبيعي أو شركة، كما للموكل.",
      example: "كريم بناني = شخص طبيعي.",
    },
  },
  opposingDomicile: {
    fr: {
      title: "Domicile de l’adverse",
      why: "Utile pour les notifications. Vous pouvez le laisser vide si vous ne l’avez pas encore.",
      example: "Boulevard Zerktouni, Casablanca.",
    },
    ar: {
      title: "موطن الطرف المقابل",
      why: "مفيد للتبليغ. يمكن تركه فارغاً إن لم يُعرف بعد.",
      example: "شارع الزرقطوني، الدار البيضاء.",
    },
  },
  rg: {
    fr: {
      title: "Numéro RG (رقم الرائج)",
      why: "Numéro donné par le greffe APRÈS dépôt. Pas obligatoire pour créer le dossier dans LexHub.",
      example: "2024/120 — seulement si le greffe l’a déjà attribué.",
    },
    ar: {
      title: "رقم الرائج / RG",
      why: "رقم تمنحه كتابة الضبط بعد الإيداع. ليس لازماً لفتح الملف في LexHub.",
      example: "2024/120 — فقط إن منحته كنابة الضبط.",
    },
  },
  chamber: {
    fr: {
      title: "Chambre",
      why: "Section du tribunal (famille, commerciale…). Optionnel tant que ce n’est pas fixé.",
      example: "قسم قضاء الأسرة.",
    },
    ar: {
      title: "الغرفة",
      why: "قسم المحكمة (أسرة، تجارية…). اختياري إلى أن يُحدد.",
      example: "قسم قضاء الأسرة.",
    },
  },
  greffe: {
    fr: {
      title: "Greffe / كتابة الضبط",
      why: "Service qui enregistre le dossier. Optionnel à la création.",
      example: "Greffe de la section famille.",
    },
    ar: {
      title: "كتابة الضبط",
      why: "المصلحة التي تسجّل الملف. اختياري عند الإنشاء.",
      example: "كتابة ضبط قسم قضاء الأسرة.",
    },
  },
  judge: {
    fr: {
      title: "Juge / conseiller rapporteur",
      why: "Nom du magistrat saisi, s’il est déjà connu. Sinon laissez vide.",
      example: "À remplir après la première ordonnance de désignation.",
    },
    ar: {
      title: "القاضي المقرر",
      why: "اسم القاضي إن عُرف. وإلا اتركوا الحقل فارغاً.",
      example: "يُملأ بعد أول تعيين.",
    },
  },
  procedure: {
    fr: {
      title: "État de la procédure",
      why: "Où en est le calendrier : dépôt, instruction, audience, jugement… Aide le planning et la clé de barre.",
      example: "Vous déposez maintenant → Ouverture / instruction.",
    },
    ar: {
      title: "حالة المسطرة",
      why: "مرحلة الملف: إيداع، تحقيق، جلسة، حكم… يفيد التخطيط ومذكرة الجلسة.",
      example: "تودعون الآن → افتتاح / تحقيق.",
    },
  },
  responsible: {
    fr: {
      title: "Avocat responsable",
      why: "Qui « possède » le dossier dans le cabinet. Lui seul pourra le supprimer.",
      example: "Vous-même, sauf si un associé mène l’affaire.",
    },
    ar: {
      title: "المحامي المسؤول",
      why: "من يملك الملف داخل المكتب. هو وحده من يمكنه حذفه.",
      example: "أنتم، إلا إن كان زميلاً يتولى القضية.",
    },
  },
  status: {
    fr: {
      title: "Statut interne du dossier",
      why: "Suivi cabinet (en cours / attente / clos). Ce n’est pas le statut judiciaire.",
      example: "Nouveau dossier → En cours.",
    },
    ar: {
      title: "حالة الملف داخل المكتب",
      why: "متابعة داخلية (جارٍ / انتظار / مغلق). ليست حالة الحكم القضائي.",
      example: "ملف جديد → جارٍ.",
    },
  },
  hearing: {
    fr: {
      title: "Première audience",
      why: "Date connue → elle apparaît au planning. Sinon laissez vide.",
      example: "15/10/2026 si le greffe a déjà fixé une date.",
    },
    ar: {
      title: "أول جلسة",
      why: "إن عُرف التاريخ يظهر في التخطيط. وإلا اتركوا فارغاً.",
      example: "15/10/2026 إن حددت كتابة الضبط موعداً.",
    },
  },
};

export function coachFor(key: CoachKey, fr: boolean): CoachCopy {
  return fr ? CASE_FIELD_COACH[key].fr : CASE_FIELD_COACH[key].ar;
}
