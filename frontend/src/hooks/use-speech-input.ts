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
  تجاريه: "تجارية",
  اداريه: "إدارية",
  إداريه: "إدارية",
  مدنيه: "مدنية",
  المدعيه: "المدعية",
  العارضه: "العارضة",
};

/** Répare ه→ة sur lexique juridique + nettoie boucles Chrome. */
export function cleanDictationNoise(text: string): string {
  let t = text.replace(/\s+/g, " ").trim();
  if (!t) return "";

  for (const [wrong, right] of Object.entries(TEH_FIX)) {
    t = t.split(wrong).join(right);
  }
  // Finales ه → ة (mots ≥ 4 lettres, hors pronoms courants)
  const skip = new Set(["فيه", "عليه", "إليه", "منه", "عنه", "له", "به", "هذه", "تلك", "الله"]);
  t = t
    .split(/(\s+)/)
    .map((w) => {
      if (skip.has(w) || w.length < 4 || !w.endsWith("ه")) return w;
      if (/^[\u0600-\u06FF]+ه$/.test(w)) return `${w.slice(0, -1)}ة`;
      return w;
    })
    .join("");

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
          // Ne coupe pas la session — Chrome envoie souvent no-speech entre deux phrases
          setError(
            locale.startsWith("ar")
              ? "لم يُلتقط كلام للحظة — واصل الحديث أو أعد المحاولة."
              : "Silence détecté — continuez à parler ou réessayez.",
          );
          return;
        }

        if (code === "network") {
          // 1 retry silencieux, puis message clair — SANS boucler sur les dialectes
          // (les retries multi-lang causaient des textes en double)
          networkRetriesRef.current += 1;
          if (networkRetriesRef.current <= 1 && shouldRestartRef.current) {
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
                shouldRestartRef.current = false;
                setListening(false);
              }
            }, 600);
            return;
          }
          shouldRestartRef.current = false;
          setListening(false);
          setError(
            locale.startsWith("ar")
              ? "خطأ شبكة التعرف الصوتي. Chrome يحتاج إنترنت مستقر. يمكنك كتابة النص يدوياً ثم « تصحيح و ترقيم »."
              : "Erreur réseau dictée — Chrome a besoin d'Internet. Tapez le texte puis « Corriger ».",
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
        if (shouldRestartRef.current) {
          try {
            recognition.start();
            setListening(true);
            return;
          } catch {
            /* ignore */
          }
        }
        setListening(false);
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
