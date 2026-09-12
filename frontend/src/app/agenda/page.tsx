"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown, ChevronLeft, ChevronRight, Search, X } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { api, type AgendaEventItem, type CaseListItem } from "@/lib/api";
import { AGENDA_EVENT_TYPES } from "@/lib/case-judicial";
import { useLocaleStore } from "@/store/locale";

const START_HOUR = 7;
const END_HOUR = 20;
const HOUR_PX = 56;
const HOURS = Array.from({ length: END_HOUR - START_HOUR }, (_, i) => START_HOUR + i);

type CalView = "year" | "month" | "week" | "day";
type TypeFilter = "all" | (typeof AGENDA_EVENT_TYPES)[number]["value"];

type EventFormMode = "create" | "edit";

type EventFormState = {
  mode: EventFormMode;
  editingId?: string;
  title: string;
  eventType: string;
  when: string;
  caseId: string;
  city: string;
  location: string;
};

function startOfDay(d: Date) {
  const x = new Date(d);
  x.setHours(0, 0, 0, 0);
  return x;
}

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function eventRange(ev: AgendaEventItem) {
  const start = new Date(ev.starts_at).getTime();
  const end = ev.ends_at
    ? new Date(ev.ends_at).getTime()
    : start + 60 * 60 * 1000;
  return { start, end };
}

function eventsOverlap(a: AgendaEventItem, b: AgendaEventItem) {
  const ra = eventRange(a);
  const rb = eventRange(b);
  return ra.start < rb.end && rb.start < ra.end;
}

function buildWeek(anchor: Date) {
  const start = startOfDay(anchor);
  const day = start.getDay();
  const mondayOffset = day === 0 ? -6 : 1 - day;
  start.setDate(start.getDate() + mondayOffset);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

/** Monday-start month grid (6 weeks × 7 days). */
function buildMonthGrid(anchor: Date) {
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const mondayOffset = first.getDay() === 0 ? -6 : 1 - first.getDay();
  const start = new Date(first);
  start.setDate(first.getDate() + mondayOffset);
  return Array.from({ length: 42 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

function toLocalInputValue(iso: string) {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function dateAtHour(day: Date, hour: number) {
  const d = new Date(day);
  d.setHours(hour, 0, 0, 0);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function eventLayout(ev: AgendaEventItem) {
  const start = new Date(ev.starts_at);
  const end = ev.ends_at
    ? new Date(ev.ends_at)
    : new Date(start.getTime() + 60 * 60 * 1000);
  const startMin = start.getHours() * 60 + start.getMinutes();
  const endMin = end.getHours() * 60 + end.getMinutes();
  const gridStart = START_HOUR * 60;
  const gridEnd = END_HOUR * 60;
  const clampedStart = Math.max(startMin, gridStart);
  const clampedEnd = Math.min(Math.max(endMin, clampedStart + 30), gridEnd);
  const top = ((clampedStart - gridStart) / 60) * HOUR_PX;
  const height = Math.max(((clampedEnd - clampedStart) / 60) * HOUR_PX, 28);
  const visible = endMin > gridStart && startMin < gridEnd;
  return { top, height, visible };
}

function eventTypeClass(t: string) {
  if (t === "rdv" || t === "mediation") return "is-rdv";
  if (t === "deadline" || t === "recours" || t === "notification") return "is-deadline";
  if (t === "other" || t === "expertise") return "is-other";
  return "is-audience";
}

function nowLineTop(now: Date): number | null {
  const mins = now.getHours() * 60 + now.getMinutes();
  const gridStart = START_HOUR * 60;
  const gridEnd = END_HOUR * 60;
  if (mins < gridStart || mins > gridEnd) return null;
  return ((mins - gridStart) / 60) * HOUR_PX;
}

export default function AgendaPage() {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const confirm = useConfirm();
  const datePickerRef = useRef<HTMLDivElement>(null);

  const [events, setEvents] = useState<AgendaEventItem[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<CalView>("week");
  const [anchor, setAnchor] = useState(() => startOfDay(new Date()));
  const [miniMonth, setMiniMonth] = useState(() => startOfDay(new Date()));
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [caseFilter, setCaseFilter] = useState("");
  const [search, setSearch] = useState("");
  const [form, setForm] = useState<EventFormState | null>(null);
  const [formHint, setFormHint] = useState("");
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const [now, setNow] = useState(() => new Date());
  const [icsBusy, setIcsBusy] = useState(false);

  const today = useMemo(() => startOfDay(new Date()), []);
  const week = useMemo(() => buildWeek(anchor), [anchor]);
  const monthCells = useMemo(() => buildMonthGrid(anchor), [anchor]);
  const miniCells = useMemo(() => buildMonthGrid(miniMonth), [miniMonth]);

  const filteredEvents = useMemo(() => {
    const q = search.trim().toLowerCase();
    return events.filter((e) => {
      if (typeFilter !== "all" && e.event_type !== typeFilter) return false;
      if (caseFilter) {
        if (e.case_id !== caseFilter) {
          const ref = cases.find((c) => c.id === caseFilter)?.reference;
          if (!ref || e.case_reference !== ref) return false;
        }
      }
      if (q) {
        const hay = `${e.title} ${e.case_reference ?? ""}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
  }, [events, typeFilter, caseFilter, search, cases]);

  const eventsByDayKey = useMemo(() => {
    const map = new Map<string, AgendaEventItem[]>();
    for (const e of filteredEvents) {
      const d = new Date(e.starts_at);
      const key = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
      const list = map.get(key) ?? [];
      list.push(e);
      map.set(key, list);
    }
    Array.from(map.values()).forEach((list) => {
      list.sort(
        (a: AgendaEventItem, b: AgendaEventItem) =>
          new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
      );
    });
    return map;
  }, [filteredEvents]);

  function dayKey(d: Date) {
    return `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
  }

  function eventsForDay(d: Date) {
    return eventsByDayKey.get(dayKey(d)) ?? [];
  }

  const overlappingHint = useMemo(() => {
    for (let i = 0; i < filteredEvents.length; i++) {
      for (let j = i + 1; j < filteredEvents.length; j++) {
        const a = filteredEvents[i];
        const b = filteredEvents[j];
        if (!sameDay(new Date(a.starts_at), new Date(b.starts_at))) continue;
        if (eventsOverlap(a, b)) {
          return ar
            ? `تنبيه: تداخل محتمل بين «${a.title}» و «${b.title}» في نفس اليوم.`
            : `Indice de conflit : « ${a.title} » et « ${b.title} » se chevauchent le même jour.`;
        }
      }
    }
    return null;
  }, [filteredEvents, ar]);

  const rangeLabel = useMemo(() => {
    const loc = ar ? "ar-MA" : "fr-FR";
    if (view === "year") {
      return String(anchor.getFullYear());
    }
    if (view === "month") {
      return anchor.toLocaleDateString(loc, { month: "long", year: "numeric" });
    }
    if (view === "day") {
      return anchor.toLocaleDateString(loc, {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
      });
    }
    const a = week[0];
    const b = week[6];
    const fmt = (d: Date) =>
      d.toLocaleDateString(loc, { day: "numeric", month: "short" });
    return `${fmt(a)} — ${fmt(b)}`;
  }, [view, anchor, week, ar]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [e, c] = await Promise.all([api.getAgenda(), api.getCases()]);
      setEvents(e);
      setCases(c);
    } catch {
      setEvents([]);
      setCases([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    setMiniMonth(new Date(anchor.getFullYear(), anchor.getMonth(), 1));
  }, [anchor]);

  useEffect(() => {
    const id = window.setInterval(() => setNow(new Date()), 60_000);
    return () => window.clearInterval(id);
  }, []);

  useEffect(() => {
    if (!form && !datePickerOpen) return;
    function onKey(e: KeyboardEvent) {
      if (e.key !== "Escape") return;
      if (form && !saving) {
        setForm(null);
        setFormHint("");
      } else if (datePickerOpen) {
        setDatePickerOpen(false);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [form, saving, datePickerOpen]);

  useEffect(() => {
    if (!datePickerOpen) return;
    function onPointer(e: MouseEvent) {
      if (
        datePickerRef.current &&
        !datePickerRef.current.contains(e.target as Node)
      ) {
        setDatePickerOpen(false);
      }
    }
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [datePickerOpen]);

  const dowLabels = ar
    ? ["إث", "ثلا", "أر", "خم", "جم", "سب", "أح"]
    : ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

  const monthNames = useMemo(() => {
    const loc = ar ? "ar-MA" : "fr-FR";
    return Array.from({ length: 12 }, (_, m) =>
      new Date(2024, m, 1).toLocaleDateString(loc, { month: "long" }),
    );
  }, [ar]);

  const monthNamesShort = useMemo(() => {
    const loc = ar ? "ar-MA" : "fr-FR";
    return Array.from({ length: 12 }, (_, m) =>
      new Date(2024, m, 1).toLocaleDateString(loc, { month: "short" }),
    );
  }, [ar]);

  const labels = {
    openCase: ar ? "الوصول إلى الملف" : "Accéder au dossier",
    linkCase: ar
      ? "اختياري: اربطوا ملفاً للوصول إليه بنقرة. يمكن ترك الحدث بدون ملف."
      : "Optionnel : liez un dossier pour y accéder en un clic. L’événement peut rester sans dossier.",
    needCase: ar
      ? "اختياري — يمكن حفظ الحدث بدون ملف."
      : "Conseil : liez un dossier pour afficher « Accéder au dossier ».",
    delete: ar ? "حذف" : "Supprimer",
    edit: ar ? "تعديل" : "Modifier",
    save: ar ? "حفظ" : "Enregistrer",
    cancel: ar ? "إلغاء" : "Annuler",
    deleteConfirm: ar ? "حذف هذا الموعد؟" : "Supprimer cet événement ?",
    deleteFail: ar ? "تعذّر الحذف." : "Suppression impossible.",
    saveFail: ar ? "تعذّر الحفظ." : "Enregistrement impossible.",
    add: ar ? "إضافة" : "Ajouter",
    newEvent: ar ? "حدث جديد" : "Nouvel événement",
    today: ar ? "اليوم" : "Aujourd'hui",
    prev: ar
      ? view === "year"
        ? "السنة السابقة"
        : view === "month"
          ? "الشهر السابق"
          : view === "day"
            ? "اليوم السابق"
            : "الأسبوع السابق"
      : view === "year"
        ? "Année précédente"
        : view === "month"
          ? "Mois précédent"
          : view === "day"
            ? "Jour précédent"
            : "Semaine précédente",
    next: ar
      ? view === "year"
        ? "السنة التالية"
        : view === "month"
          ? "الشهر التالي"
          : view === "day"
            ? "اليوم التالي"
            : "الأسبوع التالي"
      : view === "year"
        ? "Année suivante"
        : view === "month"
          ? "Mois suivant"
          : view === "day"
            ? "Jour suivant"
            : "Semaine suivante",
    clickHint: ar
      ? "انقر على خانة فارغة لإضافة موعد. من عرض الشهر: انقر يوماً لفتح اليوم."
      : "Cliquez sur une case vide pour ajouter. En mois : cliquez un jour pour l’ouvrir.",
    search: ar ? "بحث…" : "Rechercher…",
    allTypes: ar ? "الكل" : "Tous",
    allCases: ar ? "كل الملفات" : "Tous les dossiers",
    year: ar ? "سنة" : "Année",
    month: ar ? "شهر" : "Mois",
    week: ar ? "أسبوع" : "Semaine",
    day: ar ? "يوم" : "Jour",
    more: ar ? "المزيد" : "de plus",
    jumpDate: ar ? "الانتقال إلى تاريخ" : "Aller à une date",
    miniCal: ar ? "تقويم مصغّر" : "Mini-calendrier",
  };

  function typeLabel(t: string) {
    const hit = AGENDA_EVENT_TYPES.find((x) => x.value === t);
    if (hit) return ar ? hit.ar : hit.fr;
    return ar ? "آخر" : "Autre";
  }

  function shiftAnchor(dir: -1 | 1) {
    setAnchor((prev) => {
      const next = new Date(prev);
      if (view === "year") next.setFullYear(next.getFullYear() + dir);
      else if (view === "month") next.setMonth(next.getMonth() + dir);
      else if (view === "day") next.setDate(next.getDate() + dir);
      else next.setDate(next.getDate() + dir * 7);
      return startOfDay(next);
    });
  }

  function goToday() {
    const t = startOfDay(new Date());
    setAnchor(t);
    setMiniMonth(new Date(t.getFullYear(), t.getMonth(), 1));
  }

  function openCreate(day: Date, hour: number) {
    const defaultCase =
      caseFilter || (cases.length === 1 ? cases[0].id : "");
    setFormHint("");
    setForm({
      mode: "create",
      title: "",
      eventType: typeFilter !== "all" ? typeFilter : "audience",
      when: dateAtHour(day, hour),
      caseId: defaultCase,
      city: "",
      location: "",
    });
  }

  function openEdit(ev: AgendaEventItem) {
    setFormHint("");
    setForm({
      mode: "edit",
      editingId: ev.id,
      title: ev.title,
      eventType: ev.event_type,
      when: toLocalInputValue(ev.starts_at),
      caseId: ev.case_id || "",
      city: ev.city || "",
      location: ev.location || "",
    });
  }

  function closeForm() {
    if (saving) return;
    setForm(null);
    setFormHint("");
  }

  function goToDay(day: Date) {
    setAnchor(startOfDay(day));
    setView("day");
    setDatePickerOpen(false);
  }

  function goToMonth(year: number, month: number) {
    setAnchor(startOfDay(new Date(year, month, 1)));
    setView("month");
    setDatePickerOpen(false);
  }

  function jumpToMonthYear(year: number, month: number) {
    const day = Math.min(
      anchor.getDate(),
      new Date(year, month + 1, 0).getDate(),
    );
    setAnchor(startOfDay(new Date(year, month, day)));
    setDatePickerOpen(false);
  }

  async function submitForm() {
    if (!form || !form.title.trim() || !form.when) return;
    setFormHint("");
    setSaving(true);
    try {
      const payload = {
        title: form.title.trim(),
        event_type: form.eventType,
        starts_at: new Date(form.when).toISOString(),
        case_id: form.caseId || undefined,
        city: form.city.trim() || undefined,
        location: form.location.trim() || undefined,
      };
      if (form.mode === "create") {
        await api.createAgendaEvent(payload);
      } else if (form.editingId) {
        await api.updateAgendaEvent(form.editingId, {
          ...payload,
          case_id: form.caseId || null,
        });
      }
      setForm(null);
      await load();
    } catch {
      await confirm({ title: labels.saveFail, confirmLabel: ar ? "حسناً" : "OK" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(ev: AgendaEventItem) {
    const ok = await confirm({
      title: labels.deleteConfirm,
      description: ar
        ? "سيتم حذف هذا الموعد من التخطيط."
        : "Cet événement sera retiré du planning.",
      tone: "danger",
      requireDeletePhrase: true,
      deleteVisual: "generic",
      confirmLabel: labels.delete,
    });
    if (!ok) return;
    setDeletingId(ev.id);
    try {
      await api.deleteAgendaEvent(ev.id);
      setEvents((prev) => prev.filter((e) => e.id !== ev.id));
      if (form?.editingId === ev.id) setForm(null);
    } catch {
      await confirm({ title: labels.deleteFail, confirmLabel: ar ? "حسناً" : "OK" });
    } finally {
      setDeletingId(null);
    }
  }

  function resolveCaseId(ev: AgendaEventItem): string | null {
    if (ev.case_id) return ev.case_id;
    if (ev.case_reference) {
      const hit = cases.find((c) => c.reference === ev.case_reference);
      return hit?.id ?? null;
    }
    return null;
  }

  const editingEvent =
    form?.mode === "edit" && form.editingId
      ? events.find((e) => e.id === form.editingId) ?? null
      : null;
  const editingCaseId = editingEvent ? resolveCaseId(editingEvent) : null;
  const gridHeight = HOURS.length * HOUR_PX;
  const nowTop = nowLineTop(now);

  const typeFilters: TypeFilter[] = [
    "all",
    ...AGENDA_EVENT_TYPES.map((t) => t.value),
  ];

  const yearOptions = useMemo(() => {
    const y = today.getFullYear();
    return Array.from({ length: 11 }, (_, i) => y - 5 + i);
  }, [today]);

  function renderNowLine(day: Date) {
    if (!sameDay(day, today) || nowTop == null) return null;
    return (
      <div
        className="cal-now-line"
        style={{ top: nowTop }}
        aria-hidden
      >
        <span className="cal-now-line__dot" />
        <span className="cal-now-line__rail" />
      </div>
    );
  }

  function renderTimeGrid(days: Date[]) {
    const colCount = days.length;
    return (
      <motion.div
        className={`week-cal${colCount === 1 ? " week-cal--day" : ""}`}
        dir={ar ? "rtl" : "ltr"}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28, ease: [0.2, 0.9, 0.25, 1] }}
      >
        {loading ? (
          <p className="section-sub" style={{ padding: 24, margin: 0 }}>
            …
          </p>
        ) : (
          <>
            <div
              className="week-cal__head"
              style={{
                gridTemplateColumns: `56px repeat(${colCount}, minmax(0,1fr))`,
              }}
            >
              <div className="week-cal__gutter" aria-hidden />
              {days.map((d) => {
                const isToday = sameDay(d, today);
                const dowIdx = (d.getDay() + 6) % 7;
                return (
                  <button
                    key={d.toISOString()}
                    type="button"
                    className={`week-cal__day-head${isToday ? " is-today" : ""}`}
                    onClick={() => goToDay(d)}
                    title={labels.day}
                  >
                    <span className="week-cal__dow">
                      {colCount === 1
                        ? d.toLocaleDateString(ar ? "ar-MA" : "fr-FR", {
                            weekday: "short",
                          })
                        : dowLabels[dowIdx]}
                    </span>
                    <span className={`week-cal__num${isToday ? " is-today" : ""}`}>
                      {d.getDate()}
                    </span>
                  </button>
                );
              })}
            </div>

            <div
              className="week-cal__body"
              style={{
                height: gridHeight,
                gridTemplateColumns: `56px repeat(${colCount}, minmax(0,1fr))`,
              }}
            >
              <div className="week-cal__times" aria-hidden>
                {HOURS.map((h) => (
                  <div key={h} className="week-cal__time" style={{ height: HOUR_PX }}>
                    {String(h).padStart(2, "0")}:00
                  </div>
                ))}
              </div>

              {days.map((day) => {
                const isToday = sameDay(day, today);
                const dayEvents = eventsForDay(day);
                return (
                  <div
                    key={day.toISOString()}
                    className={`week-cal__col${isToday ? " is-today" : ""}`}
                  >
                    {HOURS.map((h) => (
                      <button
                        key={h}
                        type="button"
                        className="week-cal__slot"
                        style={{ height: HOUR_PX }}
                        aria-label={`${dowLabels[(day.getDay() + 6) % 7]} ${String(h).padStart(2, "0")}:00`}
                        onClick={() => openCreate(day, h)}
                      />
                    ))}

                    {dayEvents.map((ev) => {
                      const layout = eventLayout(ev);
                      if (!layout.visible) return null;
                      return (
                        <button
                          key={ev.id}
                          type="button"
                          className={`week-cal__event ${eventTypeClass(ev.event_type)}`}
                          style={{ top: layout.top, height: layout.height }}
                          onClick={(e) => {
                            e.stopPropagation();
                            openEdit(ev);
                          }}
                          title={ev.title}
                        >
                          <span className="week-cal__event-title">{ev.title}</span>
                          {ev.case_reference ? (
                            <span className="week-cal__event-ref">
                              {ev.case_reference}
                            </span>
                          ) : null}
                        </button>
                      );
                    })}

                    {renderNowLine(day)}
                  </div>
                );
              })}
            </div>
          </>
        )}
      </motion.div>
    );
  }

  function renderMonthView() {
    const month = anchor.getMonth();
    const MAX_CHIPS = 3;

    return (
      <motion.div
        className="month-cal"
        dir={ar ? "rtl" : "ltr"}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28, ease: [0.2, 0.9, 0.25, 1] }}
      >
        {loading ? (
          <p className="section-sub" style={{ padding: 24, margin: 0 }}>
            …
          </p>
        ) : (
          <>
            <div className="month-cal__head">
              {dowLabels.map((lab) => (
                <div key={lab} className="month-cal__dow">
                  {lab}
                </div>
              ))}
            </div>
            <div className="month-cal__grid">
              {monthCells.map((cell) => {
                const inMonth = cell.getMonth() === month;
                const isToday = sameDay(cell, today);
                const isSelected = sameDay(cell, anchor);
                const dayEvents = eventsForDay(cell);
                const shown = dayEvents.slice(0, MAX_CHIPS);
                const extra = dayEvents.length - shown.length;

                return (
                  <div
                    key={cell.toISOString()}
                    className={[
                      "month-cal__cell",
                      !inMonth ? "is-outside" : "",
                      isToday ? "is-today" : "",
                      isSelected && !isToday ? "is-selected" : "",
                    ]
                      .filter(Boolean)
                      .join(" ")}
                  >
                    <div className="month-cal__cell-top">
                      <button
                        type="button"
                        className={`month-cal__num${isToday ? " is-today" : ""}`}
                        onClick={() => goToDay(cell)}
                        aria-label={cell.toLocaleDateString(
                          ar ? "ar-MA" : "fr-FR",
                        )}
                      >
                        {cell.getDate()}
                      </button>
                      <button
                        type="button"
                        className="month-cal__add"
                        aria-label={labels.add}
                        onClick={() => openCreate(cell, 9)}
                      >
                        +
                      </button>
                    </div>

                    <div className="month-cal__chips">
                      {shown.map((ev) => (
                        <button
                          key={ev.id}
                          type="button"
                          className={`month-cal__chip ${eventTypeClass(ev.event_type)}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            openEdit(ev);
                          }}
                          title={ev.title}
                        >
                          <span className="month-cal__chip-time">
                            {new Date(ev.starts_at).toLocaleTimeString(
                              ar ? "ar-MA" : "fr-FR",
                              { hour: "2-digit", minute: "2-digit" },
                            )}
                          </span>
                          <span className="month-cal__chip-title">{ev.title}</span>
                        </button>
                      ))}
                      {extra > 0 ? (
                        <button
                          type="button"
                          className="month-cal__more"
                          onClick={() => goToDay(cell)}
                        >
                          +{extra} {labels.more}
                        </button>
                      ) : null}
                      {dayEvents.length === 0 ? (
                        <button
                          type="button"
                          className="month-cal__empty"
                          onClick={() => goToDay(cell)}
                          aria-label={labels.day}
                        />
                      ) : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </motion.div>
    );
  }

  function renderYearView() {
    const year = anchor.getFullYear();
    return (
      <motion.div
        className="year-cal"
        dir={ar ? "rtl" : "ltr"}
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.28, ease: [0.2, 0.9, 0.25, 1] }}
      >
        {loading ? (
          <p className="section-sub" style={{ padding: 24, margin: 0 }}>
            …
          </p>
        ) : (
          <div className="year-cal__grid">
            {Array.from({ length: 12 }, (_, month) => {
              const cells = buildMonthGrid(new Date(year, month, 1));
              const isCurrentMonth =
                today.getFullYear() === year && today.getMonth() === month;
              return (
                <div
                  key={month}
                  className={`year-cal__month${isCurrentMonth ? " is-current" : ""}`}
                >
                  <button
                    type="button"
                    className="year-cal__month-title"
                    onClick={() => goToMonth(year, month)}
                  >
                    {monthNames[month]}
                  </button>
                  <div className="year-cal__dow-row">
                    {dowLabels.map((lab) => (
                      <span key={lab} className="year-cal__dow">
                        {lab.charAt(0)}
                      </span>
                    ))}
                  </div>
                  <div className="year-cal__days">
                    {cells.map((cell) => {
                      const inMonth = cell.getMonth() === month;
                      const isToday = sameDay(cell, today);
                      const dayEvents = inMonth ? eventsForDay(cell) : [];
                      const hasEvents = dayEvents.length > 0;
                      const types = Array.from(
                        new Set(dayEvents.map((e) => e.event_type)),
                      ).slice(0, 3);
                      return (
                        <button
                          key={cell.toISOString()}
                          type="button"
                          className={[
                            "year-cal__day",
                            !inMonth ? "is-outside" : "",
                            isToday ? "is-today" : "",
                            hasEvents ? "has-events" : "",
                          ]
                            .filter(Boolean)
                            .join(" ")}
                          disabled={!inMonth}
                          onClick={() => {
                            if (!inMonth) return;
                            goToDay(cell);
                          }}
                          aria-label={
                            inMonth
                              ? cell.toLocaleDateString(ar ? "ar-MA" : "fr-FR")
                              : undefined
                          }
                        >
                          <span className="year-cal__day-num">
                            {inMonth ? cell.getDate() : ""}
                          </span>
                          {hasEvents ? (
                            <span className="year-cal__dots" aria-hidden>
                              {types.map((t) => (
                                <span
                                  key={t}
                                  className={`year-cal__dot ${eventTypeClass(t)}`}
                                />
                              ))}
                            </span>
                          ) : null}
                        </button>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </motion.div>
    );
  }

  function renderMiniCalendar() {
    const month = miniMonth.getMonth();
    const year = miniMonth.getFullYear();
    return (
      <aside className="mini-cal" aria-label={labels.miniCal} dir={ar ? "rtl" : "ltr"}>
        <div className="mini-cal__nav">
          <button
            type="button"
            className="mini-cal__nav-btn"
            aria-label={ar ? "الشهر السابق" : "Mois précédent"}
            onClick={() =>
              setMiniMonth((p) => new Date(p.getFullYear(), p.getMonth() - 1, 1))
            }
          >
            {ar ? <ChevronRight className="h-3.5 w-3.5" /> : <ChevronLeft className="h-3.5 w-3.5" />}
          </button>
          <button
            type="button"
            className="mini-cal__title"
            onClick={() => goToMonth(year, month)}
          >
            {miniMonth.toLocaleDateString(ar ? "ar-MA" : "fr-FR", {
              month: "long",
              year: "numeric",
            })}
          </button>
          <button
            type="button"
            className="mini-cal__nav-btn"
            aria-label={ar ? "الشهر التالي" : "Mois suivant"}
            onClick={() =>
              setMiniMonth((p) => new Date(p.getFullYear(), p.getMonth() + 1, 1))
            }
          >
            {ar ? <ChevronLeft className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          </button>
        </div>

        <div className="mini-cal__dow-row">
          {dowLabels.map((lab) => (
            <span key={lab} className="mini-cal__dow">
              {lab}
            </span>
          ))}
        </div>

        <div className="mini-cal__grid">
          {miniCells.map((cell) => {
            const inMonth = cell.getMonth() === month;
            const isToday = sameDay(cell, today);
            const isSelected = sameDay(cell, anchor);
            const hasEvents = inMonth && eventsForDay(cell).length > 0;
            return (
              <button
                key={cell.toISOString()}
                type="button"
                className={[
                  "mini-cal__day",
                  !inMonth ? "is-outside" : "",
                  isToday ? "is-today" : "",
                  isSelected ? "is-selected" : "",
                  hasEvents ? "has-events" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => goToDay(cell)}
              >
                {cell.getDate()}
              </button>
            );
          })}
        </div>

        <button type="button" className="mini-cal__today-btn" onClick={goToday}>
          {labels.today}
        </button>
      </aside>
    );
  }

  return (
    <AppShell>
      <div className="section-title">{ar ? "التخطيط" : "Planning"}</div>
      <div className="section-sub">
        {ar
          ? "الجلسات والمهام والمواعيد — متزامنة مع ملفاتك."
          : "Audiences, tâches et rendez-vous — synchronisés avec vos dossiers."}
      </div>

      <div className="cal-toolbar cal-toolbar--sticky" dir={ar ? "rtl" : "ltr"}>
        <div className="cal-toolbar__nav">
          <button
            type="button"
            className="cal-toolbar__icon-btn"
            aria-label={labels.prev}
            onClick={() => shiftAnchor(-1)}
          >
            {ar ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </button>

          <div className="cal-toolbar__date-wrap" ref={datePickerRef}>
            <button
              type="button"
              className="cal-toolbar__label"
              aria-expanded={datePickerOpen}
              aria-haspopup="dialog"
              title={labels.jumpDate}
              onClick={() => setDatePickerOpen((o) => !o)}
            >
              <span>{rangeLabel}</span>
              <ChevronDown className="h-3.5 w-3.5 cal-toolbar__label-chevron" />
            </button>

            <AnimatePresence>
              {datePickerOpen ? (
                <motion.div
                  className="cal-date-picker"
                  role="dialog"
                  aria-label={labels.jumpDate}
                  initial={{ opacity: 0, y: -6, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -4, scale: 0.98 }}
                  transition={{ duration: 0.18 }}
                >
                  <label className="cal-date-picker__field">
                    <span>{ar ? "السنة" : "Année"}</span>
                    <select
                      value={anchor.getFullYear()}
                      onChange={(e) =>
                        jumpToMonthYear(
                          Number(e.target.value),
                          anchor.getMonth(),
                        )
                      }
                    >
                      {yearOptions.map((y) => (
                        <option key={y} value={y}>
                          {y}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="cal-date-picker__field">
                    <span>{ar ? "الشهر" : "Mois"}</span>
                    <select
                      value={anchor.getMonth()}
                      onChange={(e) =>
                        jumpToMonthYear(
                          anchor.getFullYear(),
                          Number(e.target.value),
                        )
                      }
                    >
                      {monthNamesShort.map((name, i) => (
                        <option key={name} value={i}>
                          {name}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    type="button"
                    className="cal-date-picker__today"
                    onClick={() => {
                      goToday();
                      setDatePickerOpen(false);
                    }}
                  >
                    {labels.today}
                  </button>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>

          <button
            type="button"
            className="cal-toolbar__icon-btn"
            aria-label={labels.next}
            onClick={() => shiftAnchor(1)}
          >
            {ar ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>

          <button
            type="button"
            className="cal-toolbar__today"
            onClick={goToday}
          >
            {labels.today}
          </button>
        </div>

        <div className="cal-view-switch" role="group" aria-label="Vue">
          {(
            [
              ["year", labels.year],
              ["month", labels.month],
              ["week", labels.week],
              ["day", labels.day],
            ] as const
          ).map(([id, lab]) => (
            <button
              key={id}
              type="button"
              className={`cal-view-switch__btn${view === id ? " is-active" : ""}`}
              onClick={() => setView(id)}
            >
              {lab}
            </button>
          ))}
        </div>
      </div>

      <div className="cal-filters" dir={ar ? "rtl" : "ltr"}>
        <div className="cal-type-chips" role="group">
          {typeFilters.map((t) => (
            <button
              key={t}
              type="button"
              className={`cal-type-chip${typeFilter === t ? " is-active" : ""} ${t !== "all" ? eventTypeClass(t) : ""}`}
              onClick={() => setTypeFilter(t)}
            >
              {t === "all" ? labels.allTypes : typeLabel(t)}
            </button>
          ))}
        </div>

        <div className="cal-filters__meta">
          <select
            className="cal-case-select"
            value={caseFilter}
            onChange={(e) => setCaseFilter(e.target.value)}
            aria-label={labels.allCases}
          >
            <option value="">{labels.allCases}</option>
            {cases.map((c) => (
              <option key={c.id} value={c.id}>
                {c.reference} — {c.client_name}
              </option>
            ))}
          </select>

          <label className="cal-search">
            <Search className="h-3.5 w-3.5 cal-search__icon" aria-hidden />
            <input
              type="search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={labels.search}
            />
          </label>

          <button
            type="button"
            className="cal-toolbar__today"
            disabled={icsBusy}
            title={
              ar
                ? "ICS = ملف تقويم يمكن فتحه في Google Calendar أو Outlook"
                : "ICS = fichier calendrier à ouvrir dans Google Agenda ou Outlook"
            }
            onClick={() => {
              setIcsBusy(true);
              void api
                .exportAgendaIcs(caseFilter || undefined)
                .catch(async (err) => {
                  await confirm({
                    title:
                      err instanceof Error
                        ? err.message
                        : ar
                          ? "تعذّر تصدير ICS."
                          : "Export ICS impossible.",
                    confirmLabel: ar ? "حسناً" : "OK",
                  });
                })
                .finally(() => setIcsBusy(false));
            }}
          >
            {icsBusy ? "…" : ar ? "تصدير ICS" : "Exporter ICS"}
          </button>
        </div>
      </div>

      {overlappingHint ? (
        <p className="row-sub cal-hint" style={{ color: "var(--navy, #0B1A4D)" }}>
          {overlappingHint}
        </p>
      ) : null}

      <p className="row-sub cal-hint">{labels.clickHint}</p>

      <div className={`cal-layout${view === "year" ? " cal-layout--year" : ""}`}>
        {view !== "year" ? renderMiniCalendar() : null}

        <div className="cal-main">
          {view === "year"
            ? renderYearView()
            : view === "month"
              ? renderMonthView()
              : view === "day"
                ? renderTimeGrid([anchor])
                : renderTimeGrid(week)}
        </div>
      </div>

      <AnimatePresence>
        {form ? (
          <motion.div
            key="agenda-modal"
            className="modal-overlay open"
            role="presentation"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.22 }}
            onClick={closeForm}
          >
            <motion.div
              role="dialog"
              aria-modal="true"
              className="modal-card"
              style={{ maxWidth: 480 }}
              initial={{ opacity: 0, y: 18, scale: 0.97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.98 }}
              transition={{ duration: 0.28, ease: [0.2, 0.9, 0.25, 1] }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-head" style={{ alignItems: "center" }}>
                <h2 className="modal-title" style={{ marginBottom: 0 }}>
                  {form.mode === "create" ? labels.newEvent : labels.edit}
                </h2>
                <button
                  type="button"
                  className="modal-close"
                  aria-label={labels.cancel}
                  onClick={closeForm}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>

              <div className="form-grid" style={{ marginTop: 18 }}>
                <div className="form-field full">
                  <label>{ar ? "العنوان" : "Titre"}</label>
                  <input
                    autoFocus
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder={ar ? "جلسة المحكمة…" : "Audience Tribunal…"}
                  />
                </div>
                <div className="form-field">
                  <label>{ar ? "النوع" : "Type"}</label>
                  <select
                    value={form.eventType}
                    onChange={(e) =>
                      setForm({ ...form, eventType: e.target.value })
                    }
                  >
                    {AGENDA_EVENT_TYPES.map((t) => (
                      <option key={t.value} value={t.value}>
                        {ar ? t.ar : t.fr}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-field">
                  <label>{ar ? "التاريخ والوقت" : "Date & heure"}</label>
                  <input
                    type="datetime-local"
                    value={form.when}
                    onChange={(e) => setForm({ ...form, when: e.target.value })}
                  />
                </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-500">{ar ? "مدينة الجلسة" : "Ville (audience)"}</label>
                    <input
                      type="text"
                      value={form.city}
                      onChange={(e) => setForm({ ...form, city: e.target.value })}
                      placeholder="Casablanca, Rabat…"
                      className="w-full rounded-lg border px-3 py-2 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-500">{ar ? "المكان" : "Lieu / salle"}</label>
                    <input
                      type="text"
                      value={form.location}
                      onChange={(e) => setForm({ ...form, location: e.target.value })}
                      placeholder={ar ? "قاعة 3 · المحكمة…" : "Salle 3 · Tribunal…"}
                      className="w-full rounded-lg border px-3 py-2 text-sm"
                    />
                  </div>

                <div className="form-field full">
                  <label>
                    {ar ? "الملف (اختياري)" : "Dossier (optionnel)"}
                  </label>
                  <select
                    value={form.caseId}
                    onChange={(e) => {
                      setForm({ ...form, caseId: e.target.value });
                      setFormHint("");
                    }}
                  >
                    <option value="">
                      {ar
                        ? "بدون ملف — حدث عام"
                        : "Sans dossier — événement général"}
                    </option>
                    {cases.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.reference} — {c.client_name}
                      </option>
                    ))}
                  </select>
                  <p className="row-sub" style={{ marginTop: 8 }}>
                    {labels.linkCase}
                  </p>
                  {formHint ? (
                    <p
                      className="row-sub"
                      style={{ marginTop: 6, color: "#b91c1c" }}
                    >
                      {formHint}
                    </p>
                  ) : null}
                </div>
              </div>

              {form.mode === "edit" && editingEvent ? (
                <div className="tl-actions" style={{ marginBottom: 4 }}>
                  {editingCaseId ? (
                    <Link
                      href={`/cases/${editingCaseId}`}
                      className="btn-action btn-action--primary"
                      title={labels.openCase}
                    >
                      {labels.openCase}
                    </Link>
                  ) : null}
                  <button
                    type="button"
                    className="btn-action btn-action--danger"
                    disabled={deletingId === editingEvent.id}
                    onClick={() => void handleDelete(editingEvent)}
                  >
                    {labels.delete}
                  </button>
                </div>
              ) : null}

              <div className="modal-foot">
                <button type="button" className="btn-ghost" onClick={closeForm}>
                  {labels.cancel}
                </button>
                <button
                  type="button"
                  className="btn-create"
                  disabled={saving || !form.title.trim() || !form.when}
                  onClick={() => void submitForm()}
                >
                  {form.mode === "create" ? labels.add : labels.save}
                </button>
              </div>
            </motion.div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </AppShell>
  );
}
