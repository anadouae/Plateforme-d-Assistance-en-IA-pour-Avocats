"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Eye,
  Mail,
  Phone,
  Send,
  Settings2,
  Sparkles,
  X,
} from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type OpsContact = { email: string; name: string; role: string };
export type OpsDraft = {
  subject: string;
  body_text: string;
  body_html?: string;
  cta_url?: string;
  ai_generated?: string;
};
export type OpsTarget = {
  cabinet_id: string;
  cabinet_name: string;
  city?: string;
  contacts: OpsContact[];
  to_email?: string | null;
  to_name?: string | null;
  draft?: OpsDraft | null;
  cc_emails?: string[];
};

export type OpsTip = {
  id: string;
  scenario: string;
  priority: "high" | "medium" | "low" | string;
  action_type: "email" | "ops" | "billing" | "call" | "watch" | string;
  titre: string;
  en_clair: string;
  action: string;
  why?: string[];
  sequence?: string[];
  targets?: OpsTarget[];
  internal_href?: string | null;
  cta_label?: string;
};

const PRIORITY_FR: Record<string, string> = {
  high: "Urgent",
  medium: "Utile",
  low: "Veille",
};

const TYPE_FR: Record<string, string> = {
  email: "Email",
  ops: "Technique",
  billing: "Facturation",
  call: "Appel",
  watch: "Suivi",
};

const WHY_EMAIL: Record<string, string> = {
  trial_convert:
    "Le cabinet est en essai gratuit. On l’accompagne pour qu’il teste LexHub, puis qu’il passe à un plan payant s’il est convaincu — sinon l’essai finit sans revenu pour vous.",
  trial_ending:
    "L’essai gratuit se termine bientôt. Sans abonnement, l’accès risque de s’arrêter : on le prévient à temps.",
  past_due:
    "Le cabinet a un abonnement mais n’a pas payé. On rappelle le règlement pour ne pas perdre ce revenu.",
  cancel_retain:
    "Le cabinet a demandé à résilier. On tente de le garder avec une offre adaptée avant qu’il parte.",
  upsell_solo:
    "Le cabinet paie déjà le petit plan Solo. On propose un plan plus grand pour augmenter le revenu mensuel.",
  heavy_usage:
    "Il consomme beaucoup d’IA sur un petit plan : bon moment pour proposer plus de crédits ou un plan supérieur.",
  activate_billing:
    "Le cabinet est actif mais ne paie pas encore (souvent encore en essai) : on l’aide à activer un plan.",
  first_plea:
    "Peu d’usage de la plaidoirie : on l’invite à essayer la fonction clé pour qu’il voie la valeur de LexHub.",
};

function PriorityBadge({ p }: { p: string }) {
  const tone =
    p === "high"
      ? "bg-red-100 text-red-800"
      : p === "medium"
        ? "bg-amber-100 text-amber-900"
        : "bg-slate-100 text-slate-600";
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide", tone)}>
      {PRIORITY_FR[p] || p}
    </span>
  );
}

type EmailModalState = {
  tip: OpsTip;
  target: OpsTarget;
  to: string;
  cc: string;
  subject: string;
  body_text: string;
  body_html?: string;
};

export function OpsCoachSection({ tips }: { tips: OpsTip[] }) {
  const [openWhy, setOpenWhy] = useState<Record<string, boolean>>({});
  const [emailModal, setEmailModal] = useState<EmailModalState | null>(null);
  const [sending, setSending] = useState(false);
  const [sendMsg, setSendMsg] = useState("");
  const [sendErr, setSendErr] = useState("");

  const sorted = useMemo(
    () =>
      [...tips].sort((a, b) => {
        const o = { high: 0, medium: 1, low: 2 } as Record<string, number>;
        return (o[a.priority] ?? 9) - (o[b.priority] ?? 9);
      }),
    [tips],
  );

  const [draftBusy, setDraftBusy] = useState(false);

  async function openDraft(tip: OpsTip, target: OpsTarget) {
    const d = target.draft;
    setSendMsg("");
    setSendErr("");
    setEmailModal({
      tip,
      target,
      to: target.to_email || "",
      cc: (target.cc_emails || []).join(", "),
      subject: d?.subject || "",
      body_text: d?.body_text || "",
      body_html: d?.body_html,
    });
    // Personnalisation IA live dès l’ouverture (template → brouillon ciblé)
    if (d?.ai_generated === "true") return;
    setDraftBusy(true);
    try {
      const t = await api.opsCoachDraftEmail({
        scenario: tip.scenario,
        cabinet_id: target.cabinet_id,
        use_ai: true,
        tip_context: tip.en_clair,
      });
      setEmailModal((prev) =>
        prev
          ? {
              ...prev,
              to: t.to_email || prev.to,
              cc: (t.cc_emails || []).join(", "),
              subject: t.draft?.subject || prev.subject,
              body_text: t.draft?.body_text || prev.body_text,
              body_html: t.draft?.body_html,
              target: { ...prev.target, ...t },
            }
          : prev,
      );
    } catch {
      /* garde le brouillon template */
    } finally {
      setDraftBusy(false);
    }
  }

  async function regenerate() {
    if (!emailModal) return;
    setSendErr("");
    setDraftBusy(true);
    try {
      const t = await api.opsCoachDraftEmail({
        scenario: emailModal.tip.scenario,
        cabinet_id: emailModal.target.cabinet_id,
        use_ai: true,
        tip_context: emailModal.tip.en_clair,
      });
      setEmailModal({
        ...emailModal,
        to: t.to_email || emailModal.to,
        cc: (t.cc_emails || []).join(", "),
        subject: t.draft?.subject || emailModal.subject,
        body_text: t.draft?.body_text || emailModal.body_text,
        body_html: t.draft?.body_html,
        target: { ...emailModal.target, ...t },
      });
    } catch (e) {
      setSendErr(e instanceof ApiError ? e.message : "Erreur brouillon IA");
    } finally {
      setDraftBusy(false);
    }
  }

  async function sendEmail() {
    if (!emailModal) return;
    setSending(true);
    setSendErr("");
    setSendMsg("");
    try {
      const cc = emailModal.cc
        .split(/[,;]/)
        .map((s) => s.trim())
        .filter(Boolean);
      const r = await api.opsCoachSendEmail({
        to: emailModal.to,
        cc,
        subject: emailModal.subject,
        body_text: emailModal.body_text,
        body_html: emailModal.body_html,
        tip_id: emailModal.tip.id,
        cabinet_id: emailModal.target.cabinet_id,
      });
      setSendMsg(r.message);
    } catch (e) {
      setSendErr(e instanceof ApiError ? e.message : "Échec envoi");
    } finally {
      setSending(false);
    }
  }

  if (!sorted.length) {
    return <p className="text-sm text-slate-500">Aucune recommandation pour le moment.</p>;
  }

  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-amber-900">
          Cartes d’action — détectées live, priorisées avec l’IA
        </p>
        <p className="mt-1 text-xs text-amber-900/80">
          Signaux SQL (essai, fin d’essai, impayé, usage IA…) + analyse LLM. Chaque carte propose un
          brouillon e-mail à relire puis envoyer.
        </p>
      </div>

      {sorted.map((tip) => {
        const whyOpen = !!openWhy[tip.id];
        return (
          <div
            key={tip.id}
            className="rounded-xl border border-amber-200/80 bg-white/80 px-3.5 py-3 shadow-sm"
          >
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-1.5">
                  <PriorityBadge p={tip.priority} />
                  <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                    {TYPE_FR[tip.action_type] || tip.action_type}
                  </span>
                </div>
                <p className="mt-1.5 text-sm font-semibold text-sanad-navy">{tip.titre}</p>
                <p className="mt-1 text-sm text-slate-700">
                  <span className="font-medium text-slate-500">En clair : </span>
                  {tip.en_clair}
                </p>
                <p className="mt-1 text-sm text-amber-950/90">
                  <span className="font-medium text-amber-800">À faire : </span>
                  {tip.action}
                </p>
              </div>
            </div>

            <div className="mt-2 flex flex-wrap gap-2">
              <button
                type="button"
                className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
                onClick={() => setOpenWhy((s) => ({ ...s, [tip.id]: !whyOpen }))}
              >
                {whyOpen ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                Pourquoi cette reco
              </button>
              {tip.internal_href ? (
                <Link
                  href={tip.internal_href}
                  className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1 text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
                >
                  <Settings2 className="h-3.5 w-3.5" />
                  {tip.action_type === "ops" ? "Ouvrir" : "Lien admin"}
                </Link>
              ) : null}
            </div>

            {whyOpen ? (
              <div className="mt-2 rounded-lg border border-slate-100 bg-slate-50 px-3 py-2 text-xs text-slate-700">
                <p className="font-semibold text-slate-600">Détails</p>
                <ul className="mt-1 list-disc space-y-0.5 ps-4">
                  {(tip.why || []).map((w) => (
                    <li key={w}>{w}</li>
                  ))}
                </ul>
                {(tip.sequence || []).length ? (
                  <>
                    <p className="mt-2 font-semibold text-slate-600">Séquence suggérée</p>
                    <ol className="mt-1 list-decimal space-y-0.5 ps-4">
                      {tip.sequence!.map((s) => (
                        <li key={s}>{s}</li>
                      ))}
                    </ol>
                  </>
                ) : null}
              </div>
            ) : null}

            {(tip.targets || []).length ? (
              <div className="mt-3 space-y-2 border-t border-amber-100 pt-2">
                <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                  Cabinets concernés
                </p>
                {tip.targets!.map((t) => (
                  <div
                    key={t.cabinet_id}
                    className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-slate-150 bg-slate-50/80 px-2.5 py-2"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-sanad-navy">{t.cabinet_name}</p>
                      <p className="truncate text-[11px] text-slate-500">
                        {t.city || "—"}
                        {t.to_email ? ` · ${t.to_name || ""} <${t.to_email}>` : " · aucun contact email"}
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {tip.action_type === "email" && t.draft ? (
                        <Button
                          type="button"
                          size="sm"
                          variant="outline"
                          className="h-8 gap-1 text-xs"
                          onClick={() => openDraft(tip, t)}
                        >
                          <Eye className="h-3.5 w-3.5" />
                          Aperçu email
                        </Button>
                      ) : null}
                      {tip.action_type === "email" && !t.draft ? (
                        <span className="text-[11px] text-slate-500">Ajoutez un contact au cabinet</span>
                      ) : null}
                      {tip.action_type === "call" && t.to_email ? (
                        <span className="inline-flex items-center gap-1 text-[11px] text-slate-600">
                          <Phone className="h-3.5 w-3.5" /> Contacter {t.to_name}
                        </span>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            ) : tip.action_type === "ops" || tip.action_type === "watch" ? (
              <p className="mt-2 flex items-start gap-1.5 text-xs text-slate-500">
                {tip.action_type === "watch" ? (
                  <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                ) : (
                  <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                )}
                Pas d’email client pour cette recommandation — action interne LexHub.
              </p>
            ) : null}
          </div>
        );
      })}

      {emailModal ? (
        <div
          className="fixed inset-0 z-[90] grid place-items-center bg-black/45 p-3 backdrop-blur-[2px]"
          role="dialog"
          aria-modal="true"
          onClick={(e) => {
            if (e.target === e.currentTarget) setEmailModal(null);
          }}
        >
          <div className="flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-sanad-stone bg-white shadow-2xl">
            <div className="flex items-start justify-between gap-3 border-b border-sanad-stone px-5 py-4">
              <div>
                <p className="flex items-center gap-1.5 text-sm font-bold text-sanad-navy">
                  <Mail className="h-4 w-4 text-sanad-gold" />
                  Aperçu email — {emailModal.target.cabinet_name}
                </p>
                <p className="mt-0.5 text-xs text-slate-500">
                  {draftBusy
                    ? "Personnalisation IA en cours…"
                    : "Brouillon IA · vous pouvez tout modifier avant envoi"}
                </p>
              </div>
              <button
                type="button"
                className="rounded-lg p-1.5 text-slate-500 hover:bg-slate-100"
                onClick={() => setEmailModal(null)}
                aria-label="Fermer"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="grid flex-1 gap-0 overflow-y-auto lg:grid-cols-2">
              <div className="space-y-3 border-b border-sanad-stone p-4 lg:border-b-0 lg:border-e">
                <label className="block text-xs font-semibold text-slate-600">
                  Destinataire
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={emailModal.to}
                    onChange={(e) => setEmailModal({ ...emailModal, to: e.target.value })}
                  />
                </label>
                <label className="block text-xs font-semibold text-slate-600">
                  Copie (cc, optionnel)
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={emailModal.cc}
                    onChange={(e) => setEmailModal({ ...emailModal, cc: e.target.value })}
                    placeholder="email2@cabinet.ma"
                  />
                </label>
                <label className="block text-xs font-semibold text-slate-600">
                  Objet
                  <input
                    className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                    value={emailModal.subject}
                    onChange={(e) => setEmailModal({ ...emailModal, subject: e.target.value })}
                  />
                </label>
                <label className="block text-xs font-semibold text-slate-600">
                  Corps (modifiable)
                  <textarea
                    className="mt-1 min-h-[220px] w-full rounded-lg border border-slate-200 px-3 py-2 text-sm leading-relaxed"
                    value={emailModal.body_text}
                    onChange={(e) =>
                      setEmailModal({
                        ...emailModal,
                        body_text: e.target.value,
                        body_html: undefined,
                      })
                    }
                  />
                </label>
              </div>
              <div className="bg-slate-50 p-4">
                <p className="mb-2 flex items-center gap-1 text-xs font-semibold text-slate-600">
                  <Sparkles className="h-3.5 w-3.5" /> Aperçu
                </p>
                <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm shadow-sm">
                  <p className="mb-2 rounded-lg bg-amber-50 px-2.5 py-1.5 text-[11px] leading-snug text-amber-900">
                    <strong>Pourquoi cet email ? </strong>
                    {WHY_EMAIL[emailModal.tip.scenario] ||
                      "Action commerciale LexHub, basée sur le statut réel du cabinet."}
                  </p>
                  <p className="text-xs text-slate-500">Objet</p>
                  <p className="font-semibold text-sanad-navy">{emailModal.subject || "—"}</p>
                  <div className="mt-3 whitespace-pre-wrap text-slate-700">{emailModal.body_text || "—"}</div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-sanad-stone px-4 py-3">
              <div className="text-xs">
                {sendMsg ? <p className="font-medium text-emerald-700">{sendMsg}</p> : null}
                {sendErr ? <p className="font-medium text-red-600">{sendErr}</p> : null}
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="gap-1"
                  disabled={draftBusy}
                  onClick={() => void regenerate()}
                >
                  <Sparkles className="h-3.5 w-3.5" />
                  {draftBusy ? "IA…" : "Régénérer avec l’IA"}
                </Button>
                <Button
                  type="button"
                  size="sm"
                  className="gap-1.5"
                  disabled={sending || !emailModal.to || !emailModal.subject || !emailModal.body_text}
                  onClick={() => void sendEmail()}
                >
                  <Send className="h-3.5 w-3.5" />
                  {sending ? "Envoi…" : "Envoyer"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}

export function normalizeOpsTips(raw: unknown): OpsTip[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item, i) => {
    if (typeof item === "string") {
      return {
        id: `legacy-${i}`,
        scenario: "legacy",
        priority: "low",
        action_type: "watch",
        titre: "Recommandation",
        en_clair: item,
        action: "Voir les détails",
        why: [],
        sequence: [],
        targets: [],
      };
    }
    const o = item as Record<string, unknown>;
    return {
      id: String(o.id || `tip-${i}`),
      scenario: String(o.scenario || o.id || "generic"),
      priority: String(o.priority || "medium"),
      action_type: String(o.action_type || "watch"),
      titre: String(o.titre || "Recommandation"),
      en_clair: String(o.en_clair || ""),
      action: String(o.action || ""),
      why: Array.isArray(o.why) ? (o.why as string[]) : [],
      sequence: Array.isArray(o.sequence) ? (o.sequence as string[]) : [],
      targets: Array.isArray(o.targets) ? (o.targets as OpsTarget[]) : [],
      internal_href: (o.internal_href as string) || null,
      cta_label: (o.cta_label as string) || undefined,
    };
  });
}
