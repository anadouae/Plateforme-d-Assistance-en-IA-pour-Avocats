/** Localise les insights billing (API FR) selon la locale UI. */
export type InsightLike = {
  id: string;
  title: string;
  body: string;
  cta: string;
  href: string;
  tone?: string;
  priority?: number;
};

/** Remplace titres/corps/CTA FR par AR quand locale = ar. */
export function localizeInsight(tip: InsightLike, ar: boolean): InsightLike {
  if (!ar) return tip;

  const id = tip.id;
  // Extraire nombres éventuels du titre FR
  const nums = tip.title.match(/\d+/g) || [];

  switch (id) {
    case "trial_countdown":
      return {
        ...tip,
        title: nums.length >= 2
          ? `تجربة — ${nums[1]} يومًا متبقية`
          : nums.length === 1
            ? `تجربة — ${nums[0]} يومًا متبقية`
            : "التجربة جارية",
        body: "اختاروا Solo أو Cabinet قبل الانتقال إلى الاكتشاف.",
        cta: "اختيار خطتي",
      };
    case "free_upgrade":
      return {
        ...tip,
        title: "أنتم على الاكتشاف",
        body: "Solo بـ 299 درهم أو Cabinet بـ 699 درهم لاستعادة الحجم والفريق.",
        cta: "عرض الخطط",
      };
    case "first_plea":
      return {
        ...tip,
        title: "أمْلوا مرافعتكم الأولى",
        body: "٢–٥ دقائق إملاء عربي: فصحى، هيكل، تصدير Word.",
        cta: "فتح الورشة",
      };
    case "quota_plea":
      return {
        ...tip,
        title: nums.length >= 2 ? `حصة المرافعات ${nums[0]}/${nums[1]}` : "حصة المرافعات",
        body: "ارفعوا الخطة لتجنب انقطاع قبل الجلسة.",
        cta: "زيادة",
      };
    case "seats_avocat":
      return {
        ...tip,
        title: nums.length >= 2 ? `مقاعد المحامين ${nums[0]}/${nums[1]}` : "مقاعد المحامين",
        body: "شبه ممتلئ — رقّوا قبل دعوة عاجلة.",
        cta: "إدارة الاشتراك",
      };
    case "seats_assistant":
      return {
        ...tip,
        title: nums.length >= 2 ? `مقاعد المساعدين ${nums[0]}/${nums[1]}` : "مقاعد المساعدين",
        body: "انتقلوا لخطة أعلى لتوسيع الفريق.",
        cta: "عرض الخطط",
      };
    case "invite_assistant":
      return {
        ...tip,
        title: "ادعوا مساعدًا",
        body: "فوّضوا التنسيق والتصدير — مشمول في خطتكم.",
        cta: "دعوة",
      };
    case "nudge_2fa":
      return {
        ...tip,
        title: "فعّلوا المصادقة الثنائية",
        body: "دقيقتان لحماية الملفات والمرافعات.",
        cta: "تأمين",
      };
    case "renewal_soon":
      return {
        ...tip,
        title: nums[0] ? `التجديد خلال ${nums[0]} يومًا` : "التجديد قريبًا",
        body: "تحققوا من وسيلة الدفع.",
        cta: "عرض الاشتراك",
      };
    case "past_due":
      return {
        ...tip,
        title: "فشل الدفع",
        body: "سوّوا الدفع لتجنب تقييد الوصول.",
        cta: "تسوية",
      };
    default:
      return tip;
  }
}
