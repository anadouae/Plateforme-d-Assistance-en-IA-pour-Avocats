"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { api, type AgendaEventItem, type CaseListItem } from "@/lib/api";
import { useLocaleStore } from "@/store/locale";

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

function buildWeek(anchor: Date) {
  const start = startOfDay(anchor);
  const day = start.getDay(); // 0 Sun
  const mondayOffset = day === 0 ? -6 : 1 - day;
  start.setDate(start.getDate() + mondayOffset);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}

export default function AgendaPage() {
  const locale = useLocaleStore((s) => s.locale);
  const ar = locale === "ar";
  const [events, setEvents] = useState<AgendaEventItem[]>([]);
  const [cases, setCases] = useState<CaseListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDay, setSelectedDay] = useState(() => startOfDay(new Date()));
  const [eventTitle, setEventTitle] = useState("");
  const [eventType, setEventType] = useState("audience");
  const [eventWhen, setEventWhen] = useState("");
  const [eventCase, setEventCase] = useState("");

  const week = useMemo(() => buildWeek(new Date()), []);

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

  const dayEvents = useMemo(() => {
    return events
      .filter((e) => sameDay(new Date(e.starts_at), selectedDay))
      .sort(
        (a, b) => new Date(a.starts_at).getTime() - new Date(b.starts_at).getTime(),
      );
  }, [events, selectedDay]);

  const dowLabels = ar
    ? ["إث", "ثلا", "أر", "خم", "جم", "سب", "أح"]
    : ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"];

  async function addEvent() {
    if (!eventTitle.trim() || !eventWhen) return;
    await api.createAgendaEvent({
      title: eventTitle.trim(),
      event_type: eventType as "audience" | "deadline" | "rdv" | "other",
      starts_at: new Date(eventWhen).toISOString(),
      case_id: eventCase || undefined,
    });
    setEventTitle("");
    setEventWhen("");
    setEventCase("");
    await load();
  }

  return (
    <AppShell>
      <div className="section-title">{ar ? "التخطيط" : "Planning"}</div>
      <div className="section-sub">
        {ar
          ? "الجلسات والمهام والمواعيد — متزامنة مع ملفاتك."
          : "Audiences, tâches et rendez-vous — synchronisés avec vos dossiers."}
      </div>

      <div className="day-strip">
        {week.map((d, i) => {
          const active = sameDay(d, selectedDay);
          return (
            <button
              key={d.toISOString()}
              type="button"
              className={`day-chip${active ? " active" : ""}`}
              onClick={() => setSelectedDay(startOfDay(d))}
            >
              <div className="dow">{dowLabels[i]}</div>
              <div className="num">{d.getDate()}</div>
            </button>
          );
        })}
      </div>

      <div className="timeline">
        {loading ? (
          <p className="section-sub">…</p>
        ) : dayEvents.length === 0 ? (
          <div className="card tl-card">
            <span className="tl-time">—</span>
            <span className="tl-title" style={{ color: "var(--ink-soft)", fontWeight: 500 }}>
              {ar ? "لا أحداث لهذا اليوم" : "Aucun événement pour ce jour"}
            </span>
          </div>
        ) : (
          dayEvents.map((ev) => {
            const time = new Date(ev.starts_at).toLocaleTimeString(
              ar ? "ar-MA" : "fr-FR",
              { hour: "2-digit", minute: "2-digit" },
            );
            const isRdv = ev.event_type === "rdv" || ev.event_type === "deadline";
            const tag =
              ev.event_type === "audience"
                ? ar
                  ? "جلسة"
                  : "Audience"
                : ev.event_type === "rdv"
                  ? ar
                    ? "موعد"
                    : "Rendez-vous"
                  : ev.event_type === "deadline"
                    ? ar
                      ? "أجل"
                      : "Délai"
                    : ar
                      ? "آخر"
                      : "Autre";
            return (
              <div key={ev.id} className="tl-item">
                <div className="card tl-card">
                  <span className="tl-time">{time}</span>
                  <span className="tl-title">
                    {ev.title}
                    {ev.case_reference ? ` — ${ev.case_reference}` : ""}
                  </span>
                  <span className={`tl-tag${isRdv ? " tl-tag--rdv" : ""}`}>{tag}</span>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="card" style={{ marginTop: 22 }}>
        <div
          style={{
            fontFamily: "var(--font-fraunces), Fraunces, serif",
            fontSize: 19,
            fontWeight: 500,
            marginBottom: 14,
          }}
        >
          {ar ? "حدث جديد" : "Nouvel événement"}
        </div>
        <div className="form-grid">
          <div className="form-field full">
            <label>{ar ? "العنوان" : "Titre"}</label>
            <input
              value={eventTitle}
              onChange={(e) => setEventTitle(e.target.value)}
              placeholder={ar ? "جلسة المحكمة…" : "Audience Tribunal…"}
            />
          </div>
          <div className="form-field">
            <label>{ar ? "النوع" : "Type"}</label>
            <select value={eventType} onChange={(e) => setEventType(e.target.value)}>
              <option value="audience">{ar ? "جلسة" : "Audience"}</option>
              <option value="rdv">{ar ? "موعد" : "Rendez-vous"}</option>
              <option value="deadline">{ar ? "أجل" : "Délai"}</option>
              <option value="other">{ar ? "آخر" : "Autre"}</option>
            </select>
          </div>
          <div className="form-field">
            <label>{ar ? "التاريخ والوقت" : "Date & heure"}</label>
            <input
              type="datetime-local"
              value={eventWhen}
              onChange={(e) => setEventWhen(e.target.value)}
            />
          </div>
          <div className="form-field full">
            <label>{ar ? "الملف" : "Dossier"}</label>
            <select value={eventCase} onChange={(e) => setEventCase(e.target.value)}>
              <option value="">{ar ? "بدون ملف" : "Sans dossier"}</option>
              {cases.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.reference} — {c.client_name}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="modal-foot" style={{ borderTop: "none", marginTop: 8, paddingTop: 0 }}>
          <button type="button" className="btn-new" onClick={() => void addEvent()}>
            {ar ? "إضافة" : "Ajouter"}
          </button>
        </div>
      </div>
    </AppShell>
  );
}
