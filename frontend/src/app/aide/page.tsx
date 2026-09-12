"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  BookOpen,
  ChevronDown,
  CreditCard,
  FileText,
  HelpCircle,
  Mic,
  MessageCircle,
  Search,
  Settings,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";
import { PublicNavbar } from "@/components/layout/public-navbar";
import { VisitorConvertNudge } from "@/components/billing/visitor-convert-nudge";
import { PublicFooter } from "@/components/layout/public-footer";
import { useAuthStore } from "@/store/auth";
import { useClientLocale } from "@/store/locale";
import { cn } from "@/lib/utils";

type Faq = {
  id: string;
  cat: string;
  qFr: string;
  qAr: string;
  aFr: string;
  aAr: string;
  href?: string;
  hrefLabelFr?: string;
  hrefLabelAr?: string;
  publicHref?: string;
  publicHrefLabelFr?: string;
  publicHrefLabelAr?: string;
};

const GUIDES = [
  {
    id: "g-plea",
    icon: Mic,
    color: "bg-[#1B3F9C]/10 text-[#1B3F9C]",
    titleFr: "Créer une plaidoirie",
    titleAr: "إنشاء مرافعة",
    stepsFr: [
      "Créer / ouvrir le dossier",
      "Joindre les pièces",
      "Dicter au micro",
      "L’IA rédige (noms masqués) puis export",
    ],
    stepsAr: ["إنشاء / فتح الملف", "إرفاق القطع", "الإملاء بالميكروفون", "الصياغة ثم التصدير"],
    cat: "plea",
  },
  {
    id: "g-trial",
    icon: CreditCard,
    color: "bg-emerald-50 text-emerald-800",
    titleFr: "Démarrer un essai",
    titleAr: "بدء تجربة",
    stepsFr: ["Choisir Solo / Cabinet", "Modal essai → connexion", "Page paiement (0 MAD)", "Carte pour activer"],
    stepsAr: ["اختيار Solo / Cabinet", "نافذة التجربة → دخول", "صفحة الدفع (0 درهم)", "البطاقة للتفعيل"],
    cat: "billing",
  },
  {
    id: "g-brand",
    icon: Sparkles,
    color: "bg-[#FF6A00]/10 text-[#FF6A00]",
    titleFr: "Image de marque cabinet",
    titleAr: "هوية المكتب",
    stepsFr: ["Paramètres → Logo + nom arabe", "Exporter une plaidoirie", "Word/PDF avec en-tête pro"],
    stepsAr: ["الإعدادات → الشعار + الاسم", "تصدير مرافعة", "Word/PDF بترويسة احترافية"],
    cat: "settings",
  },
  {
    id: "g-team",
    icon: Users,
    color: "bg-violet-50 text-violet-800",
    titleFr: "Inviter l'équipe",
    titleAr: "دعوة الفريق",
    stepsFr: ["Admin → Équipe", "Invitation par e-mail", "L'invité rejoint le cabinet isolé"],
    stepsAr: ["المدير → الفريق", "دعوة بالبريد", "المدعو ينضم للمكتب المعزول"],
    cat: "team",
  },
];

const FAQS: Faq[] = [
  {
    id: "trial-card",
    cat: "billing",
    qFr: "Comment démarrer un essai avec carte ?",
    qAr: "كيف أبدأ تجربة ببطاقة؟",
    aFr:
      "1) Choisissez Solo, Cabinet ou Entreprise sur Tarifs. 2) Une fenêtre vous explique l'essai (0 MAD aujourd'hui). 3) Connectez-vous ou inscrivez-vous. 4) Sur la page Paiement, saisissez votre carte. Sans résiliation avant la fin de l'essai, le plan est facturé automatiquement.",
    aAr:
      "1) اختاروا Solo أو Cabinet من الأسعار. 2) نافذة تشرح التجربة (0 درهم اليوم). 3) سجّلوا الدخول أو أنشئوا حساباً. 4) في صفحة الدفع أدخلوا البطاقة. دون إلغاء قبل نهاية التجربة يُفوتر الاشتراك تلقائياً.",
    href: "/settings#abonnement",
    hrefLabelFr: "Gérer mon abonnement",
    hrefLabelAr: "إدارة اشتراكي",
    publicHref: "/tarifs",
    publicHrefLabelFr: "Voir les tarifs",
    publicHrefLabelAr: "عرض الأسعار",
  },
  {
    id: "who-pays",
    cat: "billing",
    qFr: "Qui peut payer ou changer l'abonnement ?",
    qAr: "من يمكنه الدفع أو تغيير الاشتراك؟",
    aFr:
      "Uniquement le responsable du cabinet (celui qui a créé l'espace, rôle admin). L'assistant et l'avocat voient les quotas, mais ne peuvent ni saisir une carte ni changer de plan. Demandez à l'admin d'ouvrir Paramètres → Abonnement.",
    aAr:
      "فقط مسؤول المكتب (من أنشأ المساحة). المساعد والمحامي يريان الحصص دون إدخال بطاقة أو تغيير الخطة. اطلبوا من المسؤول فتح الإعدادات ← الاشتراك.",
    href: "/settings#abonnement",
    hrefLabelFr: "Abonnement",
    hrefLabelAr: "الاشتراك",
    publicHref: "/tarifs",
    publicHrefLabelFr: "Voir les tarifs",
    publicHrefLabelAr: "عرض الأسعار",
  },
  {
    id: "change-email",
    cat: "settings",
    qFr: "Comment changer l'email du compte ?",
    qAr: "كيف أغيّر بريد الحساب؟",
    aFr:
      "Paramètres → Compte → Changer l'email. Saisissez la nouvelle adresse, recevez un code à 6 chiffres sur ce nouvel email, confirmez avec votre mot de passe actuel. L'ancienne adresse est aussi notifiée.",
    aAr:
      "الإعدادات ← الحساب ← تغيير البريد. أدخلوا العنوان الجديد، يصل رمز من 6 أرقام إليه، ثم أكّدوا بكلمة المرور الحالية. يُخطَر العنوان القديم أيضًا.",
    href: "/settings",
    hrefLabelFr: "Ouvrir les paramètres",
    hrefLabelAr: "فتح الإعدادات",
  },
  {
    id: "trial-duration",
    cat: "billing",
    qFr: "Combien de temps dure l'essai ?",
    qAr: "كم مدة التجربة؟",
    aFr:
      "Solo : 14 jours. Cabinet et Entreprise : 30 jours. C'est le standard des SaaS pro : assez long pour tester en conditions réelles, assez court pour décider. Vous recevez des rappels par e-mail avant la fin.",
    aAr:
      "Solo: 14 يوماً. Cabinet وEntreprise: 30 يوماً. معيار SaaS احترافي: وقت كافٍ للاختبار مع تذكيرات بريدية قبل النهاية.",
    publicHref: "/tarifs",
    publicHrefLabelFr: "Comparer les plans",
    publicHrefLabelAr: "مقارنة الخطط",
  },
  {
    id: "cancel-trial",
    cat: "billing",
    qFr: "Comment résilier avant la fin de l'essai ?",
    qAr: "كيف ألغي قبل نهاية التجربة؟",
    aFr:
      "Admin cabinet → Paramètres → Abonnement → Demander la résiliation. Si vous résiliez avant la fin de l'essai, la carte n'est pas débitée et vous revenez sur Découverte.",
    aAr:
      "مدير المكتب → الإعدادات → الاشتراك → طلب الإلغاء. إن ألغيتم قبل نهاية التجربة لن تُخصم البطاقة.",
    href: "/settings#abonnement",
    hrefLabelFr: "Ouvrir l'abonnement",
    hrefLabelAr: "فتح الاشتراك",
    publicHref: "/contact",
    publicHrefLabelFr: "Contacter le support",
    publicHrefLabelAr: "اتصل بالدعم",
  },
  {
    id: "decouverte",
    cat: "billing",
    qFr: "Qu'est-ce que le plan Découverte ?",
    qAr: "ما هي خطة الاكتشاف؟",
    aFr:
      "Découverte est gratuit pour toujours, avec quotas limités (5 dossiers, 10 plaidoiries/mois, IA limitée). Idéal pour tester LexHub sans carte. Passez à Solo / Cabinet pour plus de volume, équipe et image de marque.",
    aAr:
      "الاكتشاف مجاني دائماً بحصص محدودة. مثالي لتجربة LexHub بدون بطاقة. انتقلوا إلى Solo / Cabinet لمزيد من الحجم والفريق.",
    publicHref: "/tarifs",
    publicHrefLabelFr: "Comparer les plans",
    publicHrefLabelAr: "مقارنة الخطط",
  },
  {
    id: "branding",
    cat: "settings",
    qFr: "Qu'est-ce que l'image de marque cabinet ?",
    qAr: "ما هي هوية المكتب؟",
    aFr:
      "Ce n'est pas qu'un logo : c'est votre identité sur chaque plaidoirie exportée. Uploadez votre logo + nom du cabinet en arabe dans Paramètres. Vos Word/PDF portent l'en-tête professionnel du cabinet — pas la marque LexHub.",
    aAr:
      "ليس مجرد شعار: هوية مكتبكم على كل مرافعة مُصدَّرة. ارفعوا الشعار + الاسم بالعربية من الإعدادات. Word/PDF يحملان ترويسة المكتب — وليس علامة LexHub.",
    href: "/settings",
    hrefLabelFr: "Configurer mon cabinet",
    hrefLabelAr: "إعداد مكتبي",
    publicHref: "/tarifs",
    publicHrefLabelFr: "Plans avec image de marque",
    publicHrefLabelAr: "خطط مع هوية المكتب",
  },
  {
    id: "dictation-mic",
    cat: "plea",
    qFr: "Le micro navigateur ne démarre pas",
    qAr: "الميكروفون لا يعمل",
    aFr:
      "Utilisez Chrome ou Edge. Autorisez le micro (icône cadenas à gauche de l'URL). LexHub utilise uniquement le micro du navigateur. Parcours : Plaidoirie → Nouvelle → Dictée → Commencer.",
    aAr:
      "استخدموا Chrome أو Edge. اسمحوا بالميكروفون. الإملاء يعتمد على ميكروفون المتصفح فقط. المسار: مرافعة → جديدة → إملاء → ابدأ.",
    href: "/redaction/new",
    hrefLabelFr: "Ouvrir une plaidoirie",
    hrefLabelAr: "فتح مرافعة",
    publicHref: "/login?tab=register",
    publicHrefLabelFr: "Créer un compte pour tester",
    publicHrefLabelAr: "إنشاء حساب للتجربة",
  },
  {
    id: "plea-path",
    cat: "plea",
    qFr: "Quel est le parcours plaidoirie ?",
    qAr: "ما مسار المرافعة؟",
    aFr:
      "Dossier d’abord (référence + pièces) → dictée de l’avocat → transcription corrigée → les noms des parties sont remplacés (PARTIE_A…) avant l’IA, puis restaurés → plaidoirie professionnelle Word/PDF. Sans dossier, la rédaction IA est bloquée.",
    aAr:
      "النوع → قطع الملف → إملاء → تفريغ → كتابة → تصدير Word/PDF. المسار كامل داخل ورشة LexHub.",
    href: "/redaction",
    hrefLabelFr: "Espace plaidoirie",
    hrefLabelAr: "فضاء المرافعة",
    publicHref: "/fonctionnalites",
    publicHrefLabelFr: "Découvrir les fonctionnalités",
    publicHrefLabelAr: "اكتشاف الميزات",
  },
  {
    id: "cases",
    cat: "docs",
    qFr: "Comment centraliser un dossier ?",
    qAr: "كيف أركّز ملفاً؟",
    aFr:
      "Menu Dossiers → Nouveau dossier → ajoutez pièces, notes et plaidoiries liées. Chaque cabinet ne voit que ses propres dossiers (isolation multi-tenant).",
    aAr:
      "الملفات → ملف جديد → أضيفوا القطع والمرافعات. كل مكتب يرى ملفاته فقط.",
    href: "/cases",
    hrefLabelFr: "Mes dossiers",
    hrefLabelAr: "ملفاتي",
    publicHref: "/login?tab=register",
    publicHrefLabelFr: "S'inscrire pour commencer",
    publicHrefLabelAr: "التسجيل للبدء",
  },
  {
    id: "invite",
    cat: "team",
    qFr: "Comment inviter un avocat ou un assistant ?",
    qAr: "كيف أدعو محامياً أو مساعداً؟",
    aFr:
      "Admin cabinet : menu Équipe → invitation par e-mail (dans la limite du plan). L'invité reçoit un lien pour rejoindre votre cabinet isolé.",
    aAr:
      "مدير المكتب: الفريق → دعوة بالبريد (ضمن حد الخطة).",
    href: "/team",
    hrefLabelFr: "Ouvrir l'équipe",
    hrefLabelAr: "فتح الفريق",
    publicHref: "/tarifs",
    publicHrefLabelFr: "Plans avec équipe",
    publicHrefLabelAr: "خطط مع فريق",
  },
  {
    id: "security",
    cat: "security",
    qFr: "Comment LexHub protège-t-il nos dossiers ?",
    qAr: "كيف يحمي LexHub ملفاتنا؟",
    aFr:
      "Isolation par cabinet, HTTPS, mots de passe hachés, vérification e-mail, captcha anti-bots (Cloudflare Turnstile), 2FA optionnelle. Données chiffrées en transit.",
    aAr:
      "عزل لكل مكتب، HTTPS، كلمات مرور مشفّرة، تحقق بريد، حماية ضد الروبوتات، 2FA اختيارية.",
    publicHref: "/securite",
    publicHrefLabelFr: "Page Sécurité",
    publicHrefLabelAr: "صفحة الأمان",
  },
  {
    id: "2fa",
    cat: "security",
    qFr: "Comment activer la 2FA ?",
    qAr: "كيف أفعّل التحقق الثنائي؟",
    aFr:
      "Paramètres → Sécurité / 2FA → scannez le QR avec Google Authenticator ou Microsoft Authenticator.",
    aAr:
      "الإعدادات → الأمان / 2FA → امسحوا رمز QR بتطبيق مصادقة.",
    href: "/settings",
    hrefLabelFr: "Activer la 2FA",
    hrefLabelAr: "تفعيل 2FA",
    publicHref: "/login?tab=login",
    publicHrefLabelFr: "Se connecter d'abord",
    publicHrefLabelAr: "سجّل الدخول أولاً",
  },
  {
    id: "contact",
    cat: "support",
    qFr: "Comment contacter le support ?",
    qAr: "كيف أتواصل مع الدعم؟",
    aFr:
      "Formulaire Contact ou contact@lexhub.space — indiquez le nom du cabinet et une description courte.",
    aAr:
      "نموذج الاتصال أو contact@lexhub.space مع اسم المكتب ووصف مختصر.",
    publicHref: "/contact",
    publicHrefLabelFr: "Formulaire contact",
    publicHrefLabelAr: "نموذج الاتصال",
  },
];

const TOPICS = [
  { id: "billing", icon: CreditCard, titleFr: "Paiements", titleAr: "الدفع", filter: "billing" },
  { id: "plea", icon: Mic, titleFr: "Plaidoirie", titleAr: "المرافعة", filter: "plea" },
  { id: "settings", icon: Settings, titleFr: "Paramètres", titleAr: "الإعدادات", filter: "settings" },
  { id: "docs", icon: FileText, titleFr: "Dossiers", titleAr: "الملفات", filter: "docs" },
  { id: "team", icon: Users, titleFr: "Équipe", titleAr: "الفريق", filter: "team" },
  { id: "security", icon: Shield, titleFr: "Sécurité", titleAr: "الأمان", filter: "security" },
];

function normalize(s: string) {
  return s
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function faqLink(f: Faq, loggedIn: boolean, ar: boolean): { href: string; label: string } | null {
  if (loggedIn && f.href) {
    return { href: f.href, label: ar ? f.hrefLabelAr || "" : f.hrefLabelFr || "" };
  }
  if (f.publicHref) {
    return {
      href: f.publicHref,
      label: ar ? f.publicHrefLabelAr || "" : f.publicHrefLabelFr || "",
    };
  }
  if (f.href && loggedIn) {
    return { href: f.href, label: ar ? f.hrefLabelAr || "" : f.hrefLabelFr || "" };
  }
  return null;
}

export default function AidePage() {
  const ar = useClientLocale() === "ar";
  const user = useAuthStore((s) => s.user);
  const loggedIn = !!user;
  const [query, setQuery] = useState("");
  const [cat, setCat] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = normalize(query.trim());
    const tokens = q ? q.split(/\s+/).filter(Boolean) : [];
    return FAQS.filter((f) => {
      if (cat && f.cat !== cat) return false;
      if (!tokens.length) return true;
      const blob = normalize(`${f.qFr} ${f.qAr} ${f.aFr} ${f.aAr}`);
      return tokens.every((t) => blob.includes(t));
    });
  }, [query, cat]);

  useEffect(() => {
    if (query.trim() && filtered.length > 0) {
      setOpenId(filtered[0]!.id);
      document.getElementById("faq")?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [query, filtered]);

  function topicClick(filter: string) {
    setCat(filter);
    setOpenId(null);
    document.getElementById("faq")?.scrollIntoView({ behavior: "smooth" });
  }

  function guideClick(guideCat: string) {
    setCat(guideCat);
    setQuery("");
    const first = FAQS.find((f) => f.cat === guideCat);
    if (first) setOpenId(first.id);
    document.getElementById("faq")?.scrollIntoView({ behavior: "smooth" });
  }

  return (
    <div className="min-h-screen bg-white" dir={ar ? "rtl" : "ltr"}>
      <PublicNavbar />
      <VisitorConvertNudge />

      <section className="bg-[#1B3F9C] px-4 py-14 text-white sm:px-8">
        <div className="mx-auto max-w-3xl text-center">
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-[#A8C0FF]">
            LexHub · {ar ? "مركز المساعدة" : "Centre d'aide"}
          </p>
          <h1 className="mt-3 font-display text-3xl font-semibold sm:text-4xl">
            {ar ? "كيف يمكننا مساعدتكم ؟" : "Comment pouvons-nous vous aider ?"}
          </h1>
          <form
            className="relative mx-auto mt-8 max-w-xl"
            onSubmit={(e) => {
              e.preventDefault();
              if (filtered.length > 0) setOpenId(filtered[0]!.id);
            }}
          >
            <Search className="pointer-events-none absolute start-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="search"
              className="w-full rounded-xl border-0 py-3 pe-4 ps-10 text-sm text-slate-800 outline-none ring-2 ring-transparent focus:ring-[#FF6A00]/40"
              placeholder={ar ? "مثال: تجربة، ميكروفون، شعار، إلغاء…" : "Ex. : essai, micro, logo, résiliation…"}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              aria-label={ar ? "بحث" : "Recherche"}
            />
          </form>
          {query.trim() ? (
            <p className="mt-2 text-xs text-[#C9D6FF]">
              {filtered.length
                ? ar
                  ? `${filtered.length} نتيجة`
                  : `${filtered.length} résultat${filtered.length > 1 ? "s" : ""}`
                : ar
                  ? "لا نتائج — جرّبوا كلمات أخرى"
                  : "Aucun résultat — essayez d'autres mots"}
            </p>
          ) : null}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 py-12 sm:px-8">
        <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-slate-500">
          {ar ? "أدلة سريعة" : "Guides rapides"}
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {GUIDES.map((g) => {
            const Icon = g.icon;
            return (
              <button
                key={g.id}
                type="button"
                onClick={() => guideClick(g.cat)}
                className="rounded-2xl border border-slate-200 bg-white p-5 text-start shadow-sm transition hover:-translate-y-0.5 hover:border-[#1B3F9C]/30 hover:shadow-md"
              >
                <div className={cn("inline-flex rounded-xl p-2.5", g.color)}>
                  <Icon className="h-5 w-5" strokeWidth={1.6} />
                </div>
                <p className="mt-3 font-semibold text-[#0A1228]">{ar ? g.titleAr : g.titleFr}</p>
                <ol className="mt-3 space-y-1.5">
                  {(ar ? g.stepsAr : g.stepsFr).map((step, i) => (
                    <li key={step} className="flex gap-2 text-xs text-slate-600">
                      <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[#F4F6FA] text-[10px] font-bold text-[#1B3F9C]">
                        {i + 1}
                      </span>
                      {step}
                    </li>
                  ))}
                </ol>
              </button>
            );
          })}
        </div>
      </section>

      <section className="mx-auto max-w-5xl px-4 pb-8 sm:px-8">
        <div className="flex flex-wrap gap-2">
          {TOPICS.map((t) => {
            const Icon = t.icon;
            const active = cat === t.filter;
            return (
              <button
                key={t.id}
                type="button"
                onClick={() => topicClick(t.filter)}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition",
                  active
                    ? "border-[#1B3F9C] bg-[#1B3F9C] text-white"
                    : "border-slate-200 bg-white text-slate-700 hover:border-[#1B3F9C]/30",
                )}
              >
                <Icon className="h-4 w-4" strokeWidth={1.6} />
                {ar ? t.titleAr : t.titleFr}
              </button>
            );
          })}
        </div>
      </section>

      <section id="faq" className="border-t border-slate-100 bg-[#F7F8FC] px-4 py-12 sm:px-8">
        <div className="mx-auto max-w-3xl">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-semibold text-[#0A1228]">
              {ar ? "أسئلة شائعة" : "Questions fréquentes"}
            </h2>
            {cat || query ? (
              <button
                type="button"
                className="text-sm font-semibold text-[#1B3F9C]"
                onClick={() => {
                  setCat(null);
                  setQuery("");
                  setOpenId("trial-card");
                }}
              >
                {ar ? "إعادة الكل" : "Tout afficher"}
              </button>
            ) : null}
          </div>

          {filtered.length === 0 ? (
            <p className="rounded-xl border border-dashed border-slate-300 bg-white p-6 text-sm text-slate-500">
              {ar ? "لا نتائج — جرّبوا «تجربة» أو «ميكروفون» أو اتصلوا بنا." : "Aucun résultat — essayez « essai », « micro » ou contactez-nous."}
            </p>
          ) : (
            <ul className="space-y-3">
              {filtered.map((f) => {
                const open = query.trim() ? openId === f.id || filtered.length <= 3 : openId === f.id;
                const link = faqLink(f, loggedIn, ar);
                return (
                  <li key={f.id} id={f.id} className="rounded-2xl border border-slate-200 bg-white">
                    <button
                      type="button"
                      className="flex w-full items-center justify-between gap-3 px-5 py-4 text-start"
                      onClick={() => setOpenId(open ? null : f.id)}
                      aria-expanded={open}
                    >
                      <span className="text-sm font-semibold text-[#0A1228]">
                        {ar ? f.qAr : f.qFr}
                      </span>
                      <ChevronDown
                        className={cn(
                          "h-4 w-4 shrink-0 text-slate-400 transition",
                          open && "rotate-180",
                        )}
                      />
                    </button>
                    {open ? (
                      <div className="border-t border-slate-100 px-5 py-4 text-sm leading-relaxed text-slate-600">
                        <p>{ar ? f.aAr : f.aFr}</p>
                        {link?.href ? (
                          <Link
                            href={link.href}
                            className="mt-3 inline-flex text-sm font-semibold text-[#1B3F9C] hover:underline"
                          >
                            {link.label} →
                          </Link>
                        ) : null}
                      </div>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </section>

      <section className="mx-auto max-w-3xl px-4 py-14 text-center sm:px-8">
        <HelpCircle className="mx-auto h-10 w-10 text-[#1B3F9C]" strokeWidth={1.5} />
        <h2 className="mt-4 font-display text-2xl font-semibold text-[#0A1228]">
          {ar ? "ما زلتم بحاجة لمساعدة ؟" : "Toujours besoin d'aide ?"}
        </h2>
        <div className="mt-6 flex flex-wrap justify-center gap-3">
          <Link
            href="/contact"
            className="inline-flex items-center gap-2 rounded-xl border border-[#1B3F9C] px-5 py-2.5 text-sm font-semibold text-[#1B3F9C] hover:bg-[#1B3F9C]/5"
          >
            <MessageCircle className="h-4 w-4" />
            {ar ? "تواصلوا معنا" : "Nous contacter"}
          </Link>
          <a
            href="mailto:contact@lexhub.space"
            className="inline-flex items-center gap-2 rounded-xl bg-[#1B3F9C] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#152f75]"
          >
            <BookOpen className="h-4 w-4" />
            contact@lexhub.space
          </a>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
}
