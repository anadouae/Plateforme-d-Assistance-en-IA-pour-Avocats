"use client";

import { useEffect, useState } from "react";
import { buildOfficialArabicHtml } from "@/lib/export-official-doc";
import { api } from "@/lib/api";
import { useLocaleStore } from "@/store/locale";

type Props = {
  title: string;
  body: string;
  cabinetName?: string;
  lawyerName?: string;
  city?: string;
};

/** Aperçu in-app — même mise en page que l’export Word / PDF. */
export function PlaidoirieDocumentPreview({
  title,
  body,
  cabinetName,
  lawyerName,
  city,
}: Props) {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const [html, setHtml] = useState("");
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api
      .getCabinetLogoDataUrl()
      .then((url) => {
        if (!cancelled) setLogoUrl(url);
      })
      .catch(() => {
        if (!cancelled) setLogoUrl(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void buildOfficialArabicHtml({
      title,
      body,
      cabinetName,
      lawyerName,
      city,
      cabinetLogoUrl: logoUrl || undefined,
    })
      .then((h) => {
        if (!cancelled) {
          setHtml(h);
          setLoading(false);
        }
      })
      .catch(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [title, body, cabinetName, lawyerName, city, logoUrl]);

  return (
    <div className="plea-doc-preview" dir="ltr">
      <p className="plea-doc-preview__label">
        {ar ? "معاينة الوثيقة — كما ستُصدَّر (Word / PDF)" : "Aperçu — tel que le document sera exporté (Word / PDF)"}
      </p>
      <div className="plea-doc-preview__stage">
        {loading ? (
          <div className="plea-doc-preview__loading">
            {ar ? "جاري تحضير المعاينة…" : "Préparation de l’aperçu…"}
          </div>
        ) : (
          <iframe
            title={title || "Plaidoirie"}
            className="plea-doc-preview__frame"
            srcDoc={html}
            sandbox="allow-same-origin"
          />
        )}
      </div>
    </div>
  );
}
