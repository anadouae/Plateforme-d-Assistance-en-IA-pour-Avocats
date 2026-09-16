"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";

/** Whisper : arabe, français, ou détection auto (sans changer l’UI). */
export type WhisperLang = "ar" | "fr" | "auto";

const FINAL_TRANSCRIBE_TIMEOUT_MS = 1_800_000;
const FILE_TRANSCRIBE_TIMEOUT_MS = 1_800_000;
const RECORDER_STOP_TIMEOUT_MS = 3_500;

/** Nom fichier cohérent avec le MIME (iOS = audio/mp4 → .m4a). */
function blobUploadName(mime: string): string {
  const m = (mime || "").toLowerCase();
  if (m.includes("mp4") || m.includes("aac") || m.includes("m4a")) return "dictation.m4a";
  if (m.includes("mpeg") || m.includes("mp3")) return "dictation.mp3";
  if (m.includes("ogg")) return "dictation.ogg";
  if (m.includes("wav")) return "dictation.wav";
  return "dictation.webm";
}

function isIosDevice(): boolean {
  if (typeof navigator === "undefined") return false;
  return /iPhone|iPad|iPod/i.test(navigator.userAgent);
}

/**
 * Dictée : MediaRecorder → Whisper à l’arrêt.
 * Capture micro renforcée (gain, bitrate) pour éviter silence → hallucinations.
 */
export function useWhisperDictation(initialLang: WhisperLang = "ar") {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState("");
  const [language, setLanguageState] = useState<WhisperLang>(initialLang);
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const [livePartial, setLivePartial] = useState("");
  /** 0–100 : niveau micro moyen pendant l’enregistrement */
  const [micLevel, setMicLevel] = useState(0);
  const [micTooQuiet, setMicTooQuiet] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const mimeRef = useRef("audio/webm");
  const languageRef = useRef<WhisperLang>(initialLang);
  const recordingRef = useRef(false);
  const stopGenRef = useRef(0);
  const levelRafRef = useRef(0);
  const peakLevelRef = useRef(0);

  const setLanguage = useCallback((lang: WhisperLang) => {
    languageRef.current = lang;
    setLanguageState(lang);
  }, []);

  const stopLevelMonitor = () => {
    if (levelRafRef.current) {
      cancelAnimationFrame(levelRafRef.current);
      levelRafRef.current = 0;
    }
  };

  const stopTracks = () => {
    stopLevelMonitor();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    try {
      audioCtxRef.current?.close();
    } catch {
      /* ignore */
    }
    audioCtxRef.current = null;
    setAnalyser(null);
    setMicLevel(0);
  };

  const pickMime = () => {
    if (typeof MediaRecorder === "undefined") return "";
    const ua = typeof navigator !== "undefined" ? navigator.userAgent : "";
    const ios = /iPhone|iPad|iPod/i.test(ua);
    if (ios) {
      if (MediaRecorder.isTypeSupported("audio/mp4")) return "audio/mp4";
      if (MediaRecorder.isTypeSupported("audio/aac")) return "audio/aac";
    }
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
      return "audio/webm;codecs=opus";
    }
    if (MediaRecorder.isTypeSupported("audio/webm")) return "audio/webm";
    if (MediaRecorder.isTypeSupported("audio/mp4")) return "audio/mp4";
    if (MediaRecorder.isTypeSupported("audio/aac")) return "audio/aac";
    return "";
  };

  const transcribeBlob = useCallback(
    async (blob: Blob, name?: string, timeoutMs = FINAL_TRANSCRIBE_TIMEOUT_MS) => {
      const mime = blob.type || mimeRef.current;
      const file = new File([blob], name || blobUploadName(mime), { type: mime });
      return api.transcribeDictation(file, languageRef.current, timeoutMs);
    },
    [],
  );

  const startRecording = useCallback(async (_onSegmentText?: (text: string) => void) => {
    setError(null);
    setProvider("");
    setLivePartial("");
    setMicTooQuiet(false);
    peakLevelRef.current = 0;
    if (!navigator.mediaDevices?.getUserMedia) {
      setError("Micro non disponible sur cet appareil.");
      return false;
    }
    try {
      let stream: MediaStream;
      try {
        // echoCancellation OFF : coupe souvent les consonnes arabes
        // noiseSuppression OFF : mange les mots faibles
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: false,
            noiseSuppression: false,
            autoGainControl: true,
            channelCount: 1,
            sampleRate: 48000,
          },
        });
      } catch {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      }
      streamRef.current = stream;
      chunksRef.current = [];

      const AudioCtx =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      const ctx = new AudioCtx({ sampleRate: 48000 });
      audioCtxRef.current = ctx;
      try {
        if (ctx.state === "suspended") await ctx.resume();
      } catch {
        /* ignore */
      }
      const source = ctx.createMediaStreamSource(stream);
      // Analyseur SEULEMENT pour le niveau — on enregistre le micro BRUT (plus fiable)
      const anal = ctx.createAnalyser();
      anal.fftSize = 512;
      anal.smoothingTimeConstant = 0.65;
      source.connect(anal);
      setAnalyser(anal);

      // Moniteur niveau micro → alerte « trop faible »
      const timeData = new Uint8Array(anal.fftSize);
      const tickLevel = () => {
        anal.getByteTimeDomainData(timeData);
        let sum = 0;
        for (let i = 0; i < timeData.length; i++) {
          const v = (timeData[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / timeData.length);
        const level = Math.min(100, Math.round(rms * 350));
        peakLevelRef.current = Math.max(peakLevelRef.current, level);
        setMicLevel(level);
        setMicTooQuiet(peakLevelRef.current < 8 && recordingRef.current);
        levelRafRef.current = requestAnimationFrame(tickLevel);
      };
      levelRafRef.current = requestAnimationFrame(tickLevel);

      const mime = pickMime();
      mimeRef.current = mime || "audio/webm";
      // Micro brut → Whisper/Groq (MediaStreamDestination déformait l'arabe)
      const recorder = mime
        ? new MediaRecorder(stream, {
            mimeType: mime,
            audioBitsPerSecond: 256_000,
          })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      // iOS Safari : timeslice court → chunks vides ; 1 s est plus fiable.
      recorder.start(isIosDevice() ? 1000 : 250);
      recordingRef.current = true;
      setRecording(true);
      return true;
    } catch {
      setError("Micro bloqué — autorisez l'accès (navigateur / réglages téléphone).");
      stopTracks();
      return false;
    }
  }, []);

  const pauseRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "recording") return;
    try {
      recorder.pause();
    } catch {
      /* ignore */
    }
  }, []);

  const resumeRecording = useCallback(() => {
    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state !== "paused") return;
    try {
      recorder.resume();
    } catch {
      /* ignore */
    }
  }, []);

  const stopRecordingAndTranscribe = useCallback(
    async (_opts?: { skipFinalTranscribe?: boolean }): Promise<{
      text: string;
      provider: string;
    } | null> => {
      const skipFinal = !!_opts?.skipFinalTranscribe;
      const gen = ++stopGenRef.current;
      recordingRef.current = false;

      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === "inactive") {
        setRecording(false);
        stopTracks();
        return null;
      }

      setRecording(false);
      setMicTooQuiet(false);

      if (skipFinal) {
        try {
          if (recorder.state !== "inactive") recorder.stop();
        } catch {
          /* ignore */
        }
        stopTracks();
        mediaRecorderRef.current = null;
        setTranscribing(false);
        return null;
      }

      setTranscribing(true);
      setError(null);

      const blob: Blob = await new Promise((resolve) => {
        const timer = window.setTimeout(() => {
          resolve(new Blob(chunksRef.current, { type: recorder.mimeType || mimeRef.current }));
        }, RECORDER_STOP_TIMEOUT_MS);
        recorder.onstop = () => {
          window.clearTimeout(timer);
          resolve(new Blob(chunksRef.current, { type: recorder.mimeType || mimeRef.current }));
        };
        try {
          recorder.requestData();
        } catch {
          /* ignore */
        }
        try {
          recorder.stop();
        } catch {
          window.clearTimeout(timer);
          resolve(new Blob(chunksRef.current, { type: recorder.mimeType || mimeRef.current }));
        }
      });
      const peak = peakLevelRef.current;
      stopTracks();
      mediaRecorderRef.current = null;
      chunksRef.current = [];

      if (gen !== stopGenRef.current) {
        setTranscribing(false);
        return null;
      }

      if (!blob.size || blob.size < 400) {
        setTranscribing(false);
        setError("Aucun audio capturé — vérifiez le micro et rapprochez-vous.");
        return null;
      }

      if (peak < 6) {
        setError(
          "Micro trop faible : rapprochez-vous et parlez plus fort, puis réessayez.",
        );
      }

      try {
        const res = await transcribeBlob(blob, undefined, FINAL_TRANSCRIBE_TIMEOUT_MS);
        if (gen !== stopGenRef.current) return null;
        setProvider(res.provider);
        const text = res.text?.trim() || "";
        setLivePartial(text);
        if (!text) {
          setError(
            peak < 10
              ? "Aucune parole claire — micro trop faible ou trop loin."
              : "Aucune parole détectée.",
          );
          return null;
        }
        return { text, provider: res.provider };
      } catch (e) {
        if (gen !== stopGenRef.current) return null;
        setError(e instanceof Error ? e.message : "Transcription indisponible.");
        return null;
      } finally {
        if (gen === stopGenRef.current) setTranscribing(false);
      }
    },
    [transcribeBlob],
  );

  const cancelTranscribing = useCallback(() => {
    stopGenRef.current += 1;
    setTranscribing(false);
    recordingRef.current = false;
    try {
      const r = mediaRecorderRef.current;
      if (r && r.state !== "inactive") r.stop();
    } catch {
      /* ignore */
    }
    mediaRecorderRef.current = null;
    chunksRef.current = [];
    stopTracks();
    setRecording(false);
    setMicTooQuiet(false);
  }, []);

  const transcribeFile = useCallback(async (file: File) => {
    setTranscribing(true);
    setError(null);
    try {
      const res = await api.transcribeDictation(file, languageRef.current, FILE_TRANSCRIBE_TIMEOUT_MS);
      setProvider(res.provider);
      const text = res.text?.trim() || "";
      if (!text) {
        setError("Aucune parole détectée dans le fichier.");
        return null;
      }
      setLivePartial(text);
      return { text, provider: res.provider };
    } catch (e) {
      setError(e instanceof Error ? e.message : "Transcription fichier impossible.");
      return null;
    } finally {
      setTranscribing(false);
    }
  }, []);

  return {
    recording,
    transcribing,
    error,
    provider,
    language,
    setLanguage,
    analyser,
    livePartial,
    micLevel,
    micTooQuiet,
    supported:
      typeof window !== "undefined" &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof MediaRecorder !== "undefined",
    startRecording,
    pauseRecording,
    resumeRecording,
    stopRecordingAndTranscribe,
    cancelTranscribing,
    transcribeFile,
  };
}
