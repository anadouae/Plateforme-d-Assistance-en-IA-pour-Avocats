"use client";

import { Clock3, MessageCircle } from "lucide-react";

export function LandingPainSection({ ar }: { ar: boolean }) {
  const cards = [
    {
      icon: Clock3,
      qFr: "Trois heures pour une plaidoirie que vous avez déjà dictée dans la tête.",
      qAr: "ثلاث ساعات لمرافعة كنتم تمليها ذهنياً بالفعل.",
      aFr: "Dictez en arabe dialectal → LexHub structure en fusḥā juridique, prêt à relire — pas à tout retaper.",
      aAr: "أملوا بالدارجة → LexHub يصوغ فصحى قانونية جاهزة للمراجعة — لا لإعادة الكتابة من الصفر.",
    },
    {
      icon: MessageCircle,
      qFr: "Le dossier vit sur WhatsApp, Outlook et une clé USB.",
      qAr: "الملف موزّع بين واتساب وآوتلوك وUSB.",
      aFr: "Un seul espace : pièces, audiences, délais, commentaires assistant↔avocat — sans double saisie.",
      aAr: "فضاء واحد: قطع، جلسات، آجال، تعليقات المساعد↔المحامي — دون إدخال مزدوج.",
    },
  ];

  return (
    <section className="bg-[var(--lr-paper,#F7F8FC)] px-6 py-[88px] sm:px-8">
      <div className="mx-auto mb-12 max-w-[640px] text-center">
        <p className="font-mono text-[11.5px] uppercase tracking-[0.14em] text-[#1B3F9C]">
          {ar ? "واقع المكتب" : "Le quotidien du barreau"}
        </p>
        <h2 className="font-display mt-3.5 text-[clamp(26px,3.8vw,38px)] font-semibold tracking-tight text-[#0B1A4D]">
          {ar ? "أين يذهب يومكم فعلاً؟" : "Où part vraiment votre journée ?"}
        </h2>
      </div>
      <div className="mx-auto grid max-w-[960px] gap-5 md:grid-cols-2">
        {cards.map((c) => {
          const Icon = c.icon;
          return (
            <article
              key={c.qFr}
              className="rounded-2xl border border-[rgba(11,26,77,0.1)] bg-white p-6 shadow-[0_12px_32px_rgba(11,26,77,0.06)]"
            >
              <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#1B3F9C]/10 text-[#1B3F9C]">
                <Icon className="h-5 w-5" strokeWidth={1.7} />
              </span>
              <p className="mt-4 font-display text-[17px] font-semibold leading-snug text-[#0B1A4D]">
                « {ar ? c.qAr : c.qFr} »
              </p>
              <p className="mt-3 text-sm leading-relaxed text-[#3D4A66]">
                {ar ? c.aAr : c.aFr}
              </p>
            </article>
          );
        })}
      </div>
    </section>
  );
}
