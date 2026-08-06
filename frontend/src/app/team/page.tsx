"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Check, Copy, Link2, Mail, Shield, UserPlus } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { RoleGate } from "@/components/auth/role-gate";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api, type TeamMember } from "@/lib/api";
import { ROLE_LABELS } from "@/lib/roles";
import { cn } from "@/lib/utils";

type InviteChannel = "email" | "link";

function GoogleMeetIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <path fill="#00832D" d="M12 12.5V7h5.5l2.5 2.5V12.5z" />
      <path fill="#0066DA" d="M3 7.5V12h5.5V7H5.5z" />
      <path fill="#E37400" d="M8.5 12v4.5H3.5L1 14V12z" />
      <path fill="#2684FC" d="M12 12h5.5v4.5H14.5L12 19z" />
    </svg>
  );
}

function GmailIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden>
      <path fill="#EA4335" d="M3 5.5v13h4.5V12L12 15.5 16.5 12v6.5H21v-13L12 12z" />
      <path fill="#34A853" d="M21 5.5v3L16.5 12V5.5z" />
      <path fill="#4285F4" d="M3 5.5v3L7.5 12V5.5z" />
    </svg>
  );
}

export default function TeamPage() {
  return (
    <RoleGate allow={["admin_cabinet"]}>
      <TeamPageInner />
    </RoleGate>
  );
}

function TeamPageInner() {
  const [members, setMembers] = useState<TeamMember[]>([]);
  const [showInvite, setShowInvite] = useState(false);
  const [channel, setChannel] = useState<InviteChannel>("email");
  const [invite, setInvite] = useState({ email: "", full_name: "", role: "avocat" });
  const [message, setMessage] = useState("");
  const [inviteLink, setInviteLink] = useState("");
  const [inviteMeta, setInviteMeta] = useState<{
    email_sent?: boolean;
    dev_mail_url?: string | null;
  } | null>(null);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  function load() {
    api.getTeam().then(setMembers).catch(() => setMembers([]));
  }

  useEffect(() => {
    load();
  }, []);

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setCopied(false);
    try {
      const res = await api.inviteTeamMember(invite);
      setMessage(res.message);
      setInviteLink(res.invite_url);
      setInviteMeta(res);
      setShowInvite(false);
      setInvite({ email: "", full_name: "", role: "avocat" });
      load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur");
    }
  }

  async function copyLink() {
    if (!inviteLink) return;
    await navigator.clipboard.writeText(inviteLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  const channels: {
    id: InviteChannel;
    label: string;
    hint: string;
    icon: React.ReactNode;
  }[] = [
    {
      id: "email",
      label: "Email professionnel",
      hint: "Invitation envoyée par mail",
      icon: <GmailIcon className="h-5 w-5" />,
    },
    {
      id: "link",
      label: "Lien sécurisé",
      hint: "Créer puis copier le lien",
      icon: <Link2 className="h-5 w-5 text-sanad-navy" />,
    },
  ];

  return (
    <AppShell>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-sanad-slate">Équipe</h1>
            <p className="text-sm text-slate-500">
              Avocat et assistant collaborent sur les mêmes dossiers, avec des droits distincts
            </p>
          </div>
          <Button onClick={() => setShowInvite(!showInvite)}>
            <UserPlus className="h-4 w-4" />
            Inviter
          </Button>
        </div>

        {message && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3 rounded-2xl border border-emerald-200 bg-emerald-50/80 px-4 py-3 text-sm text-emerald-800 shadow-sm"
          >
            <p className="font-medium">{message}</p>
            {inviteLink && (
              <div className="space-y-2">
                <p className="text-xs text-emerald-700/80">
                  Lien d&apos;invitation (à partager si besoin) :
                </p>
                <div className="flex flex-wrap items-center gap-2">
                  <code className="max-w-full flex-1 truncate rounded-lg bg-white px-3 py-2 text-xs text-sanad-slate shadow-inner">
                    {inviteLink}
                  </code>
                  <Button type="button" size="sm" variant="outline" onClick={() => void copyLink()}>
                    {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
                    {copied ? "Copié" : "Copier"}
                  </Button>
                </div>
                {inviteMeta?.dev_mail_url && (
                  <a
                    href={inviteMeta.dev_mail_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs underline"
                  >
                    <Mail className="h-3 w-3" />
                    Voir l&apos;email (MailHog)
                  </a>
                )}
              </div>
            )}
          </motion.div>
        )}

        {showInvite && (
          <motion.div
            initial={{ opacity: 0, rotateX: -8 }}
            animate={{ opacity: 1, rotateX: 0 }}
            style={{ transformPerspective: 800 }}
          >
            <Card className="overflow-hidden border-sanad-stone/80 shadow-[0_12px_40px_-20px_rgba(15,23,42,0.35)]">
              <CardHeader>
                <CardTitle>Inviter un collaborateur</CardTitle>
                <p className="text-sm text-slate-500">
                  Choisissez comment envoyer l&apos;invitation
                </p>
              </CardHeader>
              <CardContent className="space-y-5">
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {channels.map((c) => (
                    <button
                      key={c.id}
                      type="button"
                      onClick={() => setChannel(c.id)}
                      className={cn(
                        "flex w-full flex-col items-stretch gap-2 rounded-xl border px-3 py-3 text-start transition",
                        "hover:-translate-y-0.5 hover:shadow-md",
                        channel === c.id
                          ? "border-sanad-gold bg-sanad-gold/10 shadow-sm"
                          : "border-sanad-border bg-white",
                      )}
                    >
                      <span className="flex items-center gap-2 text-sm font-semibold text-sanad-navy">
                        {c.icon}
                        {c.label}
                      </span>
                      <span className="text-[11px] text-slate-500">{c.hint}</span>
                    </button>
                  ))}
                </div>

                <form onSubmit={handleInvite} className="mx-auto grid w-full max-w-xl gap-4">
                  <Input
                    label="Nom complet"
                    value={invite.full_name}
                    onChange={(e) => setInvite({ ...invite, full_name: e.target.value })}
                    required
                    className="text-start"
                  />
                  <Input
                    label="Email professionnel"
                    type="email"
                    dir="ltr"
                    value={invite.email}
                    onChange={(e) => setInvite({ ...invite, email: e.target.value })}
                    required
                    className="text-start"
                  />
                  <div className="space-y-1.5">
                    <label className="block text-start text-sm font-medium text-sanad-slate">
                      Rôle
                    </label>
                    <select
                      value={invite.role}
                      onChange={(e) => setInvite({ ...invite, role: e.target.value })}
                      className="flex h-10 w-full rounded-lg border border-sanad-border bg-white px-3 text-start text-sm"
                    >
                      <option value="avocat">Avocat — dossiers + IA</option>
                      <option value="assistant_juridique">
                        Assistant juridique — dossiers, docs, planning (sans IA)
                      </option>
                      <option value="admin_cabinet">Administrateur cabinet — tout + équipe</option>
                    </select>
                  </div>
                  {error && <p className="text-sm text-red-600">{error}</p>}
                  <div className="flex flex-wrap items-center justify-end gap-2">
                    <Button type="button" variant="ghost" onClick={() => setShowInvite(false)}>
                      Annuler
                    </Button>
                    <Button type="submit">
                      {channel === "email" ? "Envoyer par email" : "Créer et afficher le lien"}
                    </Button>
                  </div>
                </form>

                <p className="flex items-center gap-2 text-[11px] text-slate-400">
                  <GoogleMeetIcon className="h-4 w-4" />
                  Les réunions Google Meet se joignent depuis le Planning (lien sur chaque RDV).
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="font-serif text-sanad-navy">Membres du cabinet</CardTitle>
            <p className="text-sm font-normal text-slate-500">
              Avatars, rôles et droits — l’avocat produit la plaidoirie ; l’assistant prépare dossiers et pièces.
            </p>
          </CardHeader>
          <CardContent>
            <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {members.map((m) => {
                const initials = (m.full_name || "?")
                  .split(" ")
                  .map((p) => p[0])
                  .slice(0, 2)
                  .join("")
                  .toUpperCase();
                return (
                  <div
                    key={`avatar-${m.id}`}
                    className="flex flex-col items-center rounded-2xl border border-sanad-stone bg-sanad-cream/30 px-4 py-5 text-center"
                  >
                    <div className="flex h-16 w-16 items-center justify-center rounded-full bg-sanad-navy font-serif text-lg font-semibold text-sanad-gold shadow-md">
                      {initials}
                    </div>
                    <p className="mt-3 font-semibold text-sanad-navy">{m.full_name}</p>
                    <p className="text-xs text-slate-500">{ROLE_LABELS[m.role] || m.role}</p>
                    <span
                      className={`mt-2 rounded-full px-2 py-0.5 text-[10px] font-medium ${
                        m.is_active
                          ? "bg-sanad-gold/20 text-sanad-navy"
                          : "bg-sanad-stone text-sanad-navy/60"
                      }`}
                    >
                      {m.is_active ? "Actif" : "Suspendu"}
                    </span>
                  </div>
                );
              })}
            </div>

            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-sanad-border bg-sanad-light text-left text-slate-500">
                  <th className="px-6 py-3 font-medium">Membre</th>
                  <th className="px-6 py-3 font-medium">Email</th>
                  <th className="px-6 py-3 font-medium">Rôle</th>
                  <th className="px-6 py-3 font-medium">Statut</th>
                  <th className="px-6 py-3 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {members.map((m) => {
                  const initials = (m.full_name || "?")
                    .split(" ")
                    .map((p) => p[0])
                    .slice(0, 2)
                    .join("")
                    .toUpperCase();
                  return (
                  <tr key={m.id} className="border-b border-sanad-border">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-sanad-navy text-xs font-semibold text-sanad-gold">
                          {initials}
                        </div>
                        <span className="font-medium text-sanad-slate">{m.full_name}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600">{m.email}</td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1 text-slate-600">
                        {m.role === "admin_cabinet" && (
                          <Shield className="h-3.5 w-3.5 text-sanad-gold" />
                        )}
                        {ROLE_LABELS[m.role] || m.role}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                          m.is_active
                            ? "bg-sanad-gold/20 text-sanad-navy"
                            : "bg-sanad-stone text-sanad-navy/60"
                        }`}
                      >
                        {m.is_active ? "Actif" : "Suspendu"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex gap-2">
                        <select
                          value={m.role}
                          onChange={async (e) => {
                            await api.updateTeamMember(m.id, { role: e.target.value });
                            load();
                          }}
                          className="rounded border border-sanad-border px-2 py-1 text-xs"
                        >
                          <option value="avocat">Avocat</option>
                          <option value="assistant_juridique">Assistant</option>
                          <option value="admin_cabinet">Admin</option>
                        </select>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={async () => {
                            if (
                              confirm(
                                `${m.is_active ? "Suspendre" : "Réactiver"} ${m.full_name} ?`,
                              )
                            ) {
                              await api.updateTeamMember(m.id, { is_active: !m.is_active });
                              load();
                            }
                          }}
                        >
                          {m.is_active ? "Suspendre" : "Réactiver"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
