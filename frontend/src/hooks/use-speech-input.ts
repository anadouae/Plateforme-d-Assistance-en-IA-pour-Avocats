"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type SpeechLang = "fr" | "ar";

/** Chrome : ar-SA souvent plus fiable que ar-MA pour la lettre ة. */
function speechLangsForLocale(locale: string): string[] {
  if (locale === "ar" || locale.startsWith("ar")) {
    return ["ar-SA", "ar-EG", "ar-MA", "ar-AE", "ar"];
  }
  return ["fr-FR", "fr"];
}

const TEH_FIX: Record<string, string> = {
  محكمه: "محكمة",
  مرافعه: "مرافعة",
  المرافعه: "المرافعة",
  جلسه: "جلسة",
  دعوه: "دعوى",
  قضيه: "قضية",
  نفقه: "نفقة",
  حضانه: "حضانة",
  شركه: "شركة",
  هيئه: "هيئة",
  مذكره: "مذكرة",
  مسطره: "مسطرة",
  ابتدائيه: "ابتدائية",
  استئنافيه: "استئنافية",
  تجاريه: "تجارية",
  اداريه: "إدارية",
  إداريه: "إدارية",
  مدنيه: "مدنية",
  المدعيه: "المدعية",
  العارضه: "العارضة",
  جريمه: "جريمة",
  سيده: "سيدة",
  سنه: "سنة",
  متورطه: "متورطة",
  مجموعه: "مجموعة",
  الدعاره: "الدعارة",
  دعاره: "دعارة",
  المغربيه: "المغربية",
  مغربيه: "مغربية",
  الدستوريه: "الدستورية",
  دستوريه: "دستورية",
  والدستوريه: "والدستورية",
  نقطه: "نقطة",
  السيده: "السيدة",
  الاهميه: "الأهمية",
  الأهميه: "الأهمية",
  اهميه: "أهمية",
  الموقره: "الموقرة",
  موقره: "موقرة",
  عقوبه: "عقوبة",
  قاصره: "قاصرة",
  القاصره: "القاصرة",
  مدينه: "مدينة",
  المدينه: "المدينة",
  شرطه: "شرطة",
  النيابه: "النيابة",
  نيابه: "نيابة",
  حمايه: "حماية",
  الحمايه: "الحماية",
  حريه: "حرية",
  الحريه: "الحرية",
  قانونيه: "قانونية",
  القانونيه: "القانونية",
  جزائيه: "جزائية",
  وثيقه: "وثيقة",
  شهاده: "شهادة",
  تهمه: "تهمة",
  براءه: "براءة",
  ماده: "مادة",
  فقره: "فقرة",
  مصلحه: "مصلحة",
  سلطه: "سلطة",
  دوله: "دولة",
};

const KEEP_FINAL_HEH = new Set([
  "الله",
  "ولله",
  "بالله",
  "وجه",
  "فقه",
  "شبه",
  "كره",
  "فيه",
  "عليه",
  "إليه",
  "اليه",
  "منه",
  "عنه",
  "له",
  "به",
  "معه",
  "لديه",
  "أمامه",
  "امامه",
  "نفسه",
  "كله",
  "بعضه",
  "ضده",
  "نحوه",
  "هذه",
  "لهذه",
  "بهذه",
  "كهذه",
  "فهذه",
  "وهذه",
]);

function fixTehMarbutaWord(word: string): string {
  const m = word.match(/^([\u0600-\u06FF]+)(.*)$/);
  if (!m) return word;
  let core = m[1];
  const rest = m[2] || "";
  if (TEH_FIX[core]) return TEH_FIX[core] + rest;
  if (KEEP_FINAL_HEH.has(core)) return word;
  for (const pref of ["وال", "بال", "كال", "فال", "لل", "ال", "و", "ف", "ب", "ك", "ل"]) {
    if (core.startsWith(pref) && core.length > pref.length + 2) {
      const stem = core.slice(pref.length);
      if (TEH_FIX[stem]) return pref + TEH_FIX[stem] + rest;
      if (KEEP_FINAL_HEH.has(stem)) return word;
      if (stem.endsWith("ه") && !KEEP_FINAL_HEH.has(stem) && stem.length >= 3) {
        return pref + stem.slice(0, -1) + "ة" + rest;
      }
      break;
    }
  }
  if (core.endsWith("ه") && !KEEP_FINAL_HEH.has(core) && core.length >= 3) {
    return core.slice(0, -1) + "ة" + rest;
  }
  return word;
}

/** Répare ه→ة (artefact Chrome STT) sans changer le sens. */
export function lightCleanDictation(text: string): string {
  let t = text.replace(/\s+/g, " ").trim();
  if (!t) return "";
  t = t.split("هذة").join("هذه").split("لهذة").join("لهذه");
  for (const [wrong, right] of Object.entries(TEH_FIX)) {
    t = t.split(wrong).join(right);
  }
  t = t
    .split(" ")
    .map((w) => fixTehMarbutaWord(w))
    .join(" ");
  return t.trim();
}

/** Chrome redit parfois toute la moitié du texte d’un coup. */
function collapseDuplicatedHalf(text: string): string {
  const t = text.trim();
  if (t.length < 40) return t;
  const words = t.split(/\s+/);
  if (words.length >= 8 && words.length % 2 === 0) {
    const mid = words.length / 2;
    const a = words.slice(0, mid).join(" ");
    const b = words.slice(mid).join(" ");
    if (a === b) return a;
  }
  const midChar = Math.floor(t.length / 2);
  for (let i = midChar - 30; i <= midChar + 30; i++) {
    if (i <= 10 || i >= t.length - 10) continue;
    const left = t.slice(0, i).trim();
    const right = t.slice(i).trim();
    if (left.length >= 25 && left === right) return left;
  }
  return t;
}

/** Lexique + anti-boucles Chrome (ne pas appliquer sur Whisper brut). */
export function cleanDictationNoise(text: string): string {
  let t = lightCleanDictation(text);
  if (!t) return "";

  const parts = t
    .split(/(?<=[.。؟!?])\s+/)
    .map((s) => s.trim())
    .filter(Boolean);

  const out: string[] = [];
  for (const s of parts) {
    if (out.slice(-4).some((x) => x === s)) continue;
    out.push(s);
  }
  t = out.join(" ").trim();

  for (let n = 0; n < 5; n++) {
    const next = t.replace(/(.{20,}?)(?:\s+\1){1,}/g, "$1");
    if (next === t) break;
    t = next;
  }
  t = collapseDuplicatedHalf(t);
  t = t.replace(/((?:[\u0600-\u06FF]+\s+){2,10}[\u0600-\u06FF]+)(?:\s+\1)+/g, "$1");
  return t.trim();
}

export function useSpeechInput(locale: string = "fr") {
  const [listening, setListening] = useState(false);
  const [supported, setSupported] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const langIndexRef = useRef(0);
  /** Callback: (finalsSession, interimLive) — finals = texte figé de la session, interim = en cours */
  const onResultRef = useRef<((finals: string, interim: string) => void) | null>(null);
  const langsRef = useRef<string[]>(speechLangsForLocale(locale));
  const finalsRef = useRef<string[]>([]);
  const shouldRestartRef = useRef(false);
  const networkRetriesRef = useRef(0);

  useEffect(() => {
    const SR =
      typeof window !== "undefined"
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : null;
    setSupported(!!SR);
    langsRef.current = speechLangsForLocale(locale);
    langIndexRef.current = 0;

    if (!SR) return;

    const recognition = new SR();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.maxAlternatives = 3;
    recognition.lang = langsRef.current[0];
    recognitionRef.current = recognition;

    return () => {
      shouldRestartRef.current = false;
      try {
        recognition.stop();
      } catch {
        /* ignore */
      }
    };
  }, [locale]);

  const emit = useCallback((interim: string) => {
    const finals = finalsRef.current.join(" ").trim();
    onResultRef.current?.(finals, interim.trim());
  }, []);

  const pushFinal = useCallback(
    (piece: string) => {
      const p = piece.trim();
      if (!p) return;
      const last = finalsRef.current[finalsRef.current.length - 1];
      // Évite d'empiler la même phrase (redémarrages Chrome)
      if (last && last === p) return;
      if (finalsRef.current.slice(-3).includes(p)) return;
      finalsRef.current.push(p);
      emit("");
    },
    [emit],
  );

  const startListening = useCallback(
    (onResult: (finals: string, interim: string) => void) => {
      const recognition = recognitionRef.current;
      if (!recognition) {
        setError(
          locale.startsWith("ar")
            ? "التعرف على الصوت غير مدعوم — استخدم Chrome."
            : "Reconnaissance vocale non supportée (utilisez Chrome).",
        );
        return;
      }

      onResultRef.current = onResult;
      setError(null);
      langIndexRef.current = 0;
      finalsRef.current = [];
      networkRetriesRef.current = 0;
      shouldRestartRef.current = true;
      recognition.lang = langsRef.current[0];

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const alts = event.results[i];
          // Préfère l'alternative qui contient ة (souvent plus fidèle en arabe)
          let piece = alts[0]?.transcript || "";
          for (let a = 0; a < alts.length; a++) {
            const cand = alts[a]?.transcript || "";
            if (cand.includes("ة")) {
              piece = cand;
              break;
            }
          }
          piece = cleanDictationNoise(piece) || piece;
          if (event.results[i].isFinal) {
            pushFinal(piece);
          } else {
            interim += piece;
          }
        }
        if (interim) emit(interim);
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        const code = event.error;

        if (code === "aborted") {
          return;
        }

        if (code === "no-speech") {
          // Normal entre deux phrases — NE PAS afficher d'erreur (ça bloquait l'avocat)
          if (shouldRestartRef.current) {
            window.setTimeout(() => {
              if (!shouldRestartRef.current) return;
              try {
                recognition.start();
                setListening(true);
              } catch {
                /* already started */
              }
            }, 250);
          }
          return;
        }

        if (code === "network") {
          // Chrome coupe souvent l’aperçu live — on relance (l’audio MediaRecorder continue)
          networkRetriesRef.current += 1;
          if (networkRetriesRef.current <= 8 && shouldRestartRef.current) {
            try {
              recognition.stop();
            } catch {
              /* ignore */
            }
            window.setTimeout(() => {
              if (!shouldRestartRef.current) return;
              try {
                recognition.start();
                setListening(true);
                setError(null);
              } catch {
                /* retry via onend */
              }
            }, 400 + networkRetriesRef.current * 200);
            return;
          }
          // Ne tue PAS la dictée : l’enregistrement serveur continue sans aperçu
          setError(
            locale.startsWith("ar")
              ? "معاينة Chrome متوقفة مؤقتاً — التسجيل مستمر. النص الكامل عند الإيقاف."
              : "Aperçu Chrome en pause — l’enregistrement continue. Texte complet à l’arrêt.",
          );
          return;
        }

        if (code === "language-not-supported" || code === "service-not-allowed") {
          const next = langIndexRef.current + 1;
          if (next < langsRef.current.length) {
            langIndexRef.current = next;
            recognition.lang = langsRef.current[next];
            try {
              recognition.start();
              setListening(true);
              return;
            } catch {
              /* fall through */
            }
          }
          shouldRestartRef.current = false;
          setListening(false);
          setError(
            locale.startsWith("ar")
              ? "المتصفح لا يدعم العربية الصوتية جيداً. اكتب في المربع ثم تصحيح."
              : "Langue vocale non supportée. Tapez le texte à la main.",
          );
          return;
        }

        if (code === "not-allowed") {
          shouldRestartRef.current = false;
          setListening(false);
          setError(
            locale.startsWith("ar")
              ? "الميكروفون محظور — اسمح بالوصول في المتصفح."
              : "Microphone bloqué — autorisez l'accès dans le navigateur.",
          );
          return;
        }

        shouldRestartRef.current = false;
        setListening(false);
        setError(
          locale.startsWith("ar")
            ? `خطأ الميكروفون (${code}). اكتب النص يدوياً.`
            : `Erreur micro (${code}). Tapez le texte à la main.`,
        );
      };

      recognition.onend = () => {
        // Chrome coupe l’aperçu après ~1 phrase / silence — ce n’est PAS une limite LexHub.
        // On relance tant que la dictée est active (MediaRecorder tourne en parallèle).
        if (!shouldRestartRef.current) {
          setListening(false);
          return;
        }
        const tryStart = (attempt: number) => {
          if (!shouldRestartRef.current) {
            setListening(false);
            return;
          }
          try {
            recognition.start();
            setListening(true);
            networkRetriesRef.current = 0;
          } catch {
            if (attempt < 6) {
              window.setTimeout(() => tryStart(attempt + 1), 300 + attempt * 200);
            } else {
              setListening(false);
            }
          }
        };
        window.setTimeout(() => tryStart(0), 200);
      };

      try {
        recognition.start();
        setListening(true);
      } catch {
        // Already started
        setListening(true);
      }
    },
    [locale, emit, pushFinal],
  );

  const stopListening = useCallback(() => {
    shouldRestartRef.current = false;
    try {
      recognitionRef.current?.stop();
    } catch {
      /* ignore */
    }
    setListening(false);
  }, []);

  return { listening, supported, error, startListening, stopListening };
}

declare global {
  interface Window {
    SpeechRecognition: typeof SpeechRecognition;
    webkitSpeechRecognition: typeof SpeechRecognition;
  }
}
