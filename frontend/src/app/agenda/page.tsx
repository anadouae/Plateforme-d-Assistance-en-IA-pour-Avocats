"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Briefcase,
  CalendarDays,
  CheckCircle2,
  Circle,
  Clock3,
  Plus,
  StickyNote,
  Trash2,
  Video,
} from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  api,
  type AgendaEventItem,
  type CaseListItem,
  type CaseNoteItem,
  type CaseTaskItem,
} from "@/lib/api";
import { FadeIn } from "@/components/motion/fade-in";
import { cn } from "@/lib/utils";

function fmtDate(iso?: string | null) {
  if (!iso) return "—";
  try {
    return new Date(iso).toLocaleString("fr-FR", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

const EVENT_LABELS: Record<string, string> = {
  audience: "Audience",
  deadline: "Délai",
  rdv: "RDV",
  other: "Autre",
};

export default function AgendaPage() {
  const [events, setEvents] = useState<AgendaEventItem[]>([]);
  const [tasks, setTasks] = useState<CaseTaskItem[]>([]);
  const [notes, setNotes] = useState<CaseNoteItem[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<"agenda" | "tasks" | "notes">("agenda");
  const [filterCaseId, setFilterCaseId] = useState("");

  const [eventTitle, setEventTitle] = useState("");
  const [eventType, setEventType] = useState("audience");
  const [eventWhen, setEventWhen] = useState("");
  const [eventCase, setEventCase] = useState("");
  const [eventMeet, setEventMeet] = useState("");

  const [taskTitle, setTaskTitle] = useState("");
  const [taskDue, setTaskDue] = useState("");
  const [taskCase, setTaskCase] = useState("");

  const [noteTitle, setNoteTitle] = useState("");
  const [noteBody, setNoteBody] = useState("");
  const [noteCase, setNoteCase] = useState("");
  const [activeNote, setActiveNote] = useState<CaseNoteItem | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [e, t, n, c] = await Promise.all([
        api.getAgenda(),
        api.getTasks(),
        api.getNotes(),
        api.getCases(),
      ]);
      setEvents(e);
      setTasks(t);
      setNotes(n);
      setCases(c);
    } catch {
      setEvents([]);
      setTasks([]);
      setNotes([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const upcoming = useMemo(() => {
    let list = [...events];
    if (filterCaseId) {
      list = list.filter((e) => e.case_id === filterCaseId);
    }
    return list.sort(
      (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
    );
  }, [events, filterCaseId]);

  const filteredTasks = useMemo(() => {
    if (!filterCaseId) return tasks;
    return tasks.filter((t) => t.case_id === filterCaseId);
  }, [tasks, filterCaseId]);

  const filteredNotes = useMemo(() => {
    if (!filterCaseId) return notes;
    return notes.filter((n) => n.case_id === filterCaseId);
  }, [notes, filterCaseId]);

  async function relinkEvent(eventId: string, caseId: string) {
    await api.updateAgendaEvent(eventId, {
      case_id: caseId || null,
    });
    await load();
  }

  async function addEvent() {
    if (!eventTitle.trim() || !eventWhen) return;
    await api.createAgendaEvent({
      title: eventTitle.trim(),
      event_type: eventType as "audience" | "deadline" | "rdv" | "other",
      starts_at: new Date(eventWhen).toISOString(),
      case_id: eventCase || undefined,
      meet_url: eventMeet.trim() || undefined,
    });
    setEventTitle("");
    setEventWhen("");
    setEventCase("");
    setEventMeet("");
    await load();
  }

  async function addTask() {
    if (!taskTitle.trim()) return;
    await api.createTask({
      title: taskTitle.trim(),
      due_at: taskDue ? new Date(taskDue).toISOString() : undefined,
      case_id: taskCase || undefined,
    });
    setTaskTitle("");
    setTaskDue("");
    setTaskCase("");
    await load();
  }

  async function addNote() {
    if (!noteTitle.trim()) return;
    const created = await api.createNote({
      title: noteTitle.trim(),
      body: noteBody,
      case_id: noteCase || undefined,
    });
    setNoteTitle("");
    setNoteBody("");
    setNoteCase("");
    setActiveNote(created);
    await load();
  }

  async function toggleTask(task: CaseTaskItem) {
    const next = task.status === "done" ? "todo" : "done";
    await api.updateTask(task.id, { status: next });
    await load();
  }

  async function saveActiveNote() {
    if (!activeNote) return;
    await api.updateNote(activeNote.id, {
      title: activeNote.title,
      body: activeNote.body,
    });
    await load();
  }

  return (
    <AppShell>
      <FadeIn className="space-y-5">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl font-semibold text-sanad-navy">
              Planning du cabinet
            </h1>
            <p className="text-sm text-slate-500">
              Synchronisé avec les dossiers — audiences et délais rattachés à chaque affaire.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-xl border border-sanad-border bg-white px-2 py-1">
              <Briefcase className="h-3.5 w-3.5 text-sanad-gold" />
              <select
                className="h-8 max-w-[220px] border-0 bg-transparent text-xs text-sanad-navy outline-none"
                value={filterCaseId}
                onChange={(e) => setFilterCaseId(e.target.value)}
                aria-label="Filtrer par dossier"
              >
                <option value="">Tous les dossiers</option>
                {cases.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.reference} — {c.client_name}
                  </option>
                ))}
              </select>
            </div>
          <div className="flex gap-1 rounded-xl border border-sanad-border bg-white p-1">
            {(
              [
                ["agenda", "Agenda", CalendarDays],
                ["tasks", "Tâches", Clock3],
                ["notes", "Notes", StickyNote],
              ] as const
            ).map(([id, label, Icon]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={cn(
                  "flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition",
                  tab === id
                    ? "bg-sanad-navy text-white shadow-sm"
                    : "text-sanad-navy/70 hover:bg-sanad-cream",
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>
          </div>
        </div>

        {loading ? (
          <p className="text-sm text-slate-400">Chargement…</p>
        ) : (
          <motion.div
            key={tab}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
          >
            {tab === "agenda" && (
              <div className="grid gap-4 lg:grid-cols-5">
                <Card className="lg:col-span-2 shadow-luxe">
                  <CardHeader>
                    <CardTitle className="text-base">Nouvel événement</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <input
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      placeholder="Titre (ex. Audience Tribunal)"
                      value={eventTitle}
                      onChange={(e) => setEventTitle(e.target.value)}
                    />
                    <select
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      value={eventType}
                      onChange={(e) => setEventType(e.target.value)}
                    >
                      <option value="audience">Audience</option>
                      <option value="deadline">Délai</option>
                      <option value="rdv">RDV</option>
                      <option value="other">Autre</option>
                    </select>
                    <input
                      type="datetime-local"
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      value={eventWhen}
                      onChange={(e) => setEventWhen(e.target.value)}
                    />
                    <select
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      value={eventCase}
                      onChange={(e) => setEventCase(e.target.value)}
                    >
                      <option value="">Sans dossier</option>
                      {cases.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.reference} — {c.client_name}
                        </option>
                      ))}
                    </select>
                    <div className="space-y-1">
                      <label className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                        <Video className="h-3.5 w-3.5 text-emerald-600" />
                        Lien Google Meet / visioconférence
                      </label>
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                        placeholder="https://meet.google.com/…"
                        value={eventMeet}
                        onChange={(e) => setEventMeet(e.target.value)}
                      />
                      <p className="text-[10px] text-slate-400">
                        Collez un lien Meet (ou Zoom/Teams). Ouvrez{" "}
                        <a
                          href="https://meet.google.com/new"
                          target="_blank"
                          rel="noreferrer"
                          className="underline"
                        >
                          meet.google.com/new
                        </a>{" "}
                        pour en créer un.
                      </p>
                    </div>
                    <Button className="w-full gap-2" onClick={() => void addEvent()}>
                      <Plus className="h-4 w-4" />
                      Ajouter
                    </Button>
                  </CardContent>
                </Card>
                <Card className="lg:col-span-3 shadow-luxe">
                  <CardHeader>
                    <CardTitle className="text-base">
                      À venir
                      {filterCaseId ? " · dossier filtré" : ""}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {upcoming.length === 0 && (
                      <p className="text-sm text-slate-400">Aucun événement pour l’instant.</p>
                    )}
                    {upcoming.map((e) => (
                      <motion.div
                        key={e.id}
                        layout
                        whileHover={{ scale: 1.01, x: 2 }}
                        className="flex items-start justify-between gap-3 rounded-xl border border-sanad-border/70 bg-white px-3 py-2.5 shadow-sm transition"
                      >
                        <div className="min-w-0 flex-1">
                          <p className="truncate text-sm font-medium text-sanad-slate">{e.title}</p>
                          <p className="text-[11px] text-slate-500">
                            {EVENT_LABELS[e.event_type] || e.event_type} · {fmtDate(e.starts_at)}
                          </p>
                          <div className="mt-1.5 flex flex-wrap items-center gap-2">
                            {e.case_id && e.case_reference ? (
                              <Link
                                href={`/cases/${e.case_id}`}
                                className="inline-flex items-center gap-1 rounded-md bg-sanad-gold/15 px-1.5 py-0.5 text-[11px] font-medium text-sanad-navy hover:bg-sanad-gold/25"
                              >
                                <Briefcase className="h-3 w-3" />
                                {e.case_reference}
                              </Link>
                            ) : (
                              <span className="text-[11px] text-slate-400">Sans dossier</span>
                            )}
                            <select
                              className="h-7 max-w-[160px] rounded border border-sanad-border bg-sanad-cream/40 px-1 text-[10px]"
                              value={e.case_id || ""}
                              onChange={(ev) => void relinkEvent(e.id, ev.target.value)}
                              aria-label="Lier à un dossier"
                            >
                              <option value="">Lier un dossier…</option>
                              {cases.map((c) => (
                                <option key={c.id} value={c.id}>
                                  {c.reference}
                                </option>
                              ))}
                            </select>
                          </div>
                          {e.meet_url && (
                            <a
                              href={e.meet_url}
                              target="_blank"
                              rel="noreferrer"
                              className="mt-1 inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 hover:underline"
                            >
                              <Video className="h-3 w-3" />
                              Rejoindre la réunion
                            </a>
                          )}
                        </div>
                        <button
                          type="button"
                          className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                          onClick={() => void api.deleteAgendaEvent(e.id).then(load)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </motion.div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            )}

            {tab === "tasks" && (
              <div className="grid gap-4 lg:grid-cols-5">
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-base">Nouvelle tâche</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <input
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      placeholder="Ex. Préparer conclusions"
                      value={taskTitle}
                      onChange={(e) => setTaskTitle(e.target.value)}
                    />
                    <input
                      type="datetime-local"
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      value={taskDue}
                      onChange={(e) => setTaskDue(e.target.value)}
                    />
                    <select
                      className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                      value={taskCase}
                      onChange={(e) => setTaskCase(e.target.value)}
                    >
                      <option value="">Sans dossier</option>
                      {cases.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.reference} — {c.client_name}
                        </option>
                      ))}
                    </select>
                    <Button className="w-full gap-2" onClick={() => void addTask()}>
                      <Plus className="h-4 w-4" />
                      Ajouter
                    </Button>
                  </CardContent>
                </Card>
                <Card className="lg:col-span-3">
                  <CardHeader>
                    <CardTitle className="text-base">Liste</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {filteredTasks.length === 0 && (
                      <p className="text-sm text-slate-400">Aucune tâche.</p>
                    )}
                    {filteredTasks.map((t) => (
                      <motion.div
                        key={t.id}
                        layout
                        whileHover={{ scale: 1.01 }}
                        className="flex items-center gap-2 rounded-xl border border-sanad-border/70 bg-white px-3 py-2.5"
                      >
                        <button type="button" onClick={() => void toggleTask(t)}>
                          {t.status === "done" ? (
                            <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                          ) : (
                            <Circle className="h-4 w-4 text-slate-400" />
                          )}
                        </button>
                        <div className="min-w-0 flex-1">
                          <p
                            className={cn(
                              "truncate text-sm font-medium",
                              t.status === "done" && "text-slate-400 line-through",
                            )}
                          >
                            {t.title}
                          </p>
                          <p className="text-[11px] text-slate-500">
                            Échéance {fmtDate(t.due_at)}
                            {t.case_id && t.case_reference ? (
                              <>
                                {" · "}
                                <Link
                                  href={`/cases/${t.case_id}`}
                                  className="font-medium text-sanad-navy hover:underline"
                                >
                                  {t.case_reference}
                                </Link>
                              </>
                            ) : null}
                          </p>
                        </div>
                        <button
                          type="button"
                          className="rounded p-1 text-slate-400 hover:bg-red-50 hover:text-red-600"
                          onClick={() => void api.deleteTask(t.id).then(load)}
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </motion.div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            )}

            {tab === "notes" && (
              <div className="grid gap-4 lg:grid-cols-5">
                <Card className="lg:col-span-2">
                  <CardHeader>
                    <CardTitle className="text-base">Notes</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="space-y-2 border-b border-sanad-border pb-3">
                      <input
                        className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                        placeholder="Titre de la note"
                        value={noteTitle}
                        onChange={(e) => setNoteTitle(e.target.value)}
                      />
                      <textarea
                        className="min-h-[72px] w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                        placeholder="Contenu…"
                        value={noteBody}
                        onChange={(e) => setNoteBody(e.target.value)}
                      />
                      <select
                        className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm"
                        value={noteCase}
                        onChange={(e) => setNoteCase(e.target.value)}
                      >
                        <option value="">Sans dossier</option>
                        {cases.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.reference}
                          </option>
                        ))}
                      </select>
                      <Button size="sm" className="w-full gap-1" onClick={() => void addNote()}>
                        <Plus className="h-3.5 w-3.5" />
                        Créer
                      </Button>
                    </div>
                    {filteredNotes.map((n) => (
                      <button
                        key={n.id}
                        type="button"
                        onClick={() => setActiveNote(n)}
                        onMouseEnter={() => setActiveNote(n)}
                        className={cn(
                          "w-full rounded-lg border px-3 py-2 text-left transition",
                          activeNote?.id === n.id
                            ? "border-sanad-blue/30 bg-sanad-blue/5"
                            : "border-transparent hover:border-sanad-border hover:bg-white",
                        )}
                      >
                        <p className="truncate text-sm font-medium">{n.title}</p>
                        <p className="truncate text-[11px] text-slate-400">
                          {n.body || "Vide"} · {fmtDate(n.updated_at)}
                          {n.case_reference ? ` · ${n.case_reference}` : ""}
                        </p>
                      </button>
                    ))}
                  </CardContent>
                </Card>
                <Card className="lg:col-span-3">
                  <CardHeader className="flex flex-row items-center justify-between">
                    <CardTitle className="text-base">
                      {activeNote ? activeNote.title : "Aperçu"}
                    </CardTitle>
                    {activeNote && (
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" onClick={() => void saveActiveNote()}>
                          Enregistrer
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() =>
                            void api.deleteNote(activeNote.id).then(() => {
                              setActiveNote(null);
                              return load();
                            })
                          }
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    )}
                  </CardHeader>
                  <CardContent>
                    {!activeNote ? (
                      <p className="text-sm text-slate-400">
                        Survole ou sélectionne une note pour voir le contenu.
                      </p>
                    ) : (
                      <div className="space-y-3">
                        <input
                          className="w-full rounded-lg border border-sanad-border px-3 py-2 text-sm font-medium"
                          value={activeNote.title}
                          onChange={(e) =>
                            setActiveNote({ ...activeNote, title: e.target.value })
                          }
                        />
                        <textarea
                          className="min-h-[280px] w-full rounded-xl border border-sanad-border bg-sanad-light/40 px-3 py-3 text-sm leading-relaxed"
                          value={activeNote.body}
                          onChange={(e) =>
                            setActiveNote({ ...activeNote, body: e.target.value })
                          }
                        />
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </motion.div>
        )}
      </FadeIn>
    </AppShell>
  );
}
