"use client";

import Link from "next/link";
import { LegalPageLayout } from "@/components/layout/legal-page-layout";
import { useClientLocale } from "@/store/locale";

export default function RemboursementPage() {
  const ar = useClientLocale() === "ar";

  return (
    <LegalPageLayout
      title={ar ? "سياسة الاسترداد" : "Politique de remboursement"}
      subtitle={
        ar
          ? "شفافية حول التجربة المجانية والفوترة على LexHub."
          : "Transparence sur l’essai gratuit et la facturation LexHub."
      }
    >
      <div className="prose prose-slate max-w-none text-sm leading-relaxed" dir={ar ? "rtl" : "ltr"}>
        {ar ? (
          <>
            <h2>التجربة المجانية</h2>
            <p>
              خطط Solo وCabinet وEntreprise تبدأ بتجربة مجانية (مدتها حسب العرض، غالباً 30 يوماً)
              مع بطاقة مسجّلة. لن تُخصم البطاقة خلال التجربة إذا ألغيت الاشتراك قبل نهايتها.
            </p>
            <h2>بعد نهاية التجربة</h2>
            <p>
              إذا لم تُلغَ التجربة، يُفعَّل الاشتراك المدفوع تلقائياً حسب الدورة المختارة
              (شهرية أو سنوية). يمكنكم الإلغاء في أي وقت من الإعدادات ← الاشتراك؛ يبقى الوصول
              حتى نهاية الفترة المدفوعة.
            </p>
            <h2>خطة الاكتشاف</h2>
            <p>الاكتشاف مجانية دائماً بحصص محدودة — لا فوترة.</p>
            <h2>التواصل</h2>
            <p>
              للاستفسارات حول الفوترة:{" "}
              <a href="mailto:contact@lexhub.space">contact@lexhub.space</a> أو{" "}
              <Link href="/contact">نموذج الاتصال</Link>.
            </p>
          </>
        ) : (
          <>
            <h2>Essai gratuit</h2>
            <p>
              Les plans Solo, Cabinet et Entreprise démarrent par un essai gratuit (durée selon
              l’offre, souvent 30 jours) avec carte enregistrée. Aucun débit pendant l’essai si
              vous résiliez avant la fin.
            </p>
            <h2>Après l’essai</h2>
            <p>
              Sans résiliation, l’abonnement payant démarre automatiquement selon le cycle choisi
              (mensuel ou annuel). Vous pouvez résilier à tout moment dans Paramètres → Abonnement ;
              l’accès reste actif jusqu’à la fin de la période payée.
            </p>
            <h2>Plan Découverte</h2>
            <p>Découverte reste gratuit à vie, avec quotas limités — aucune facturation.</p>
            <h2>Contact</h2>
            <p>
              Questions facturation :{" "}
              <a href="mailto:contact@lexhub.space">contact@lexhub.space</a> ou{" "}
              <Link href="/contact">formulaire de contact</Link>.
            </p>
          </>
        )}
      </div>
    </LegalPageLayout>
  );
}
