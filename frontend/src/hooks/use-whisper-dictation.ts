"use client";

import { useCallback, useRef, useState } from "react";
import { api } from "@/lib/api";

/** Produit Maroc : transcription arabe uniquement. */
export type WhisperLang = "ar";

/** Segment auto : longue plaidoirie → texte progressif (sinon rien jusqu'au Stop). */
const SEGMENT_MS = 55_000;
const TRANSCRIBE_TIMEOUT_MS = 600_000;

/**
 * Dictée Whisper (arabe) : micro + segments périodiques + fichier audio.
 */
export function useWhisperDictation(_initialLang: WhisperLang = "ar") {
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [provider, setProvider] = useState("");
  const [language, setLanguage] = useState<WhisperLang>("ar");
  const [analyser, setAnalyser] = useState<AnalyserNode | null>(null);
  const [livePartial, setLivePartial] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const mimeRef = useRef("audio/webm");
  const languageRef = useRef<WhisperLang>("ar");
  const segmentTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const onSegmentTextRef = useRef<((text: string) => void) | null>(null);
  const recordingRef = useRef(false);
  const livePartialRef = useRef("");
  languageRef.current = "ar";

  const stopTracks = () => {
    if (segmentTimerRef.current) {
      clearInterval(segmentTimerRef.current);
      segmentTimerRef.current = null;
    }
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    try {
      audioCtxRef.current?.close();
    } catch {
      /* ignore */
    }
    audioCtxRef.current = null;
    setAnalyser(null);
  };

  const pickMime = () => {
    if (typeof MediaRecorder === "undefined") return "";
    if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
      return "audio/webm;codecs=opus";
    }
    if (MediaRecorder.isTypeSupported("audio/webm")) return "audio/webm";
    if (MediaRecorder.isTypeSupported("audio/mp4")) return "audio/mp4";
    return "";
  };

  const transcribeBlob = useCallback(async (blob: Blob, name: string) => {
    const file = new File([blob], name, { type: blob.type || mimeRef.current });
    return api.transcribeDictation(file, languageRef.current, TRANSCRIBE_TIMEOUT_MS);
  }, []);

  const flushSegment = useCallback(async () => {
    const recorder = mediaRecorderRef.current;
    const stream = streamRef.current;
    if (!recorder || !stream || recorder.state !== "recording") return;

    const blob: Blob = await new Promise((resolve) => {
      const prev = chunksRef.current;
      chunksRef.current = [];
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      recorder.onstop = () => {
        resolve(new Blob(prev, { type: recorder.mimeType || mimeRef.current }));
      };
      try {
        recorder.requestData();
      } catch {
        /* ignore */
      }
      try {
        recorder.stop();
      } catch {
        resolve(new Blob());
      }
    });

    // Relancer immédiatement l'enregistrement sur le même flux
    if (recordingRef.current && stream.active) {
      const mime = mimeRef.current;
      const next = mime
        ? new MediaRecorder(stream, { mimeType: mime })
        : new MediaRecorder(stream);
      mediaRecorderRef.current = next;
      chunksRef.current = [];
      next.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data);
      };
      next.start(250);
    }

    if (!blob.size || blob.size < 2000) return;

    setTranscribing(true);
    try {
      const res = await transcribeBlob(blob, "segment.webm");
      const text = res.text?.trim() || "";
      if (text) {
        setProvider(res.provider);
        livePartialRef.current = livePartialRef.current
          ? `${livePartialRef.current} ${text}`
          : text;
        setLivePartial(livePartialRef.current);
        onSegmentTextRef.current?.(text);
      }
    } catch {
      /* segment failed — continue recording */
    } finally {
      if (recordingRef.current) setTranscribing(false);
    }
  }, [transcribeBlob]);

  const startRecording = useCallback(
    async (onSegmentText?: (text: string) => void) => {
      setError(null);
      setProvider("");
      livePartialRef.current = "";
      setLivePartial("");
      onSegmentTextRef.current = onSegmentText || null;
      if (!navigator.mediaDevices?.getUserMedia) {
        setError("Micro non disponible.");
        return false;
      }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            channelCount: 1,
          },
        });
        streamRef.current = stream;
        chunksRef.current = [];

        const AudioCtx =
          window.AudioContext ||
          (window as unknown as { webkitAudioContext: typeof AudioContext })
            .webkitAudioContext;
        const ctx = new AudioCtx();
        audioCtxRef.current = ctx;
        const source = ctx.createMediaStreamSource(stream);
        const anal = ctx.createAnalyser();
        anal.fftSize = 256;
        anal.smoothingTimeConstant = 0.75;
        source.connect(anal);
        setAnalyser(anal);

        const mime = pickMime();
        mimeRef.current = mime || "audio/webm";
        const recorder = mime
          ? new MediaRecorder(stream, { mimeType: mime })
          : new MediaRecorder(stream);
        mediaRecorderRef.current = recorder;
        recorder.ondataavailable = (e) => {
          if (e.data.size > 0) chunksRef.current.push(e.data);
        };
        recorder.start(250);
        recordingRef.current = true;
        setRecording(true);

        segmentTimerRef.current = setInterval(() => {
          void flushSegment();
        }, SEGMENT_MS);

        return true;
      } catch {
        setError("Micro bloqué — autorisez l'accès dans le navigateur.");
        stopTracks();
        return false;
      }
    },
    [flushSegment],
  );

  const stopRecordingAndTranscribe = useCallback(async (): Promise<{
    text: string;
    provider: string;
  } | null> => {
    if (segmentTimerRef.current) {
      clearInterval(segmentTimerRef.current);
      segmentTimerRef.current = null;
    }
    recordingRef.current = false;

    const recorder = mediaRecorderRef.current;
    if (!recorder || recorder.state === "inactive") {
      setRecording(false);
      stopTracks();
      const already = livePartialRef.current.trim();
      if (already) return { text: already, provider: provider || "whisper" };
      return null;
    }

    setRecording(false);
    setTranscribing(true);
    setError(null);

    const blob: Blob = await new Promise((resolve) => {
      recorder.onstop = () => {
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
        resolve(new Blob());
      }
    });
    stopTracks();
    mediaRecorderRef.current = null;

    const prior = livePartialRef.current.trim();
    if ((!blob.size || blob.size < 1200) && prior) {
      setTranscribing(false);
      return { text: prior, provider: provider || "whisper" };
    }
    if (!blob.size || blob.size < 1200) {
      setTranscribing(false);
      setError("Aucun audio capturé.");
      return null;
    }

    try {
      const res = await transcribeBlob(blob, "dictation.webm");
      setProvider(res.provider);
      setTranscribing(false);
      const text = res.text?.trim() || "";
      const merged = [prior, text].filter(Boolean).join(" ").trim();
      livePartialRef.current = merged;
      setLivePartial(merged);
      if (!merged) {
        setError("Aucune parole détectée.");
        return null;
      }
      return { text: merged, provider: res.provider };
    } catch (e) {
      setTranscribing(false);
      if (prior) return { text: prior, provider: provider || "whisper" };
      setError(
        e instanceof Error ? e.message : "Transcription indisponible.",
      );
      return null;
    }
  }, [provider, transcribeBlob]);

  const transcribeFile = useCallback(
    async (file: File): Promise<{ text: string; provider: string } | null> => {
      setError(null);
      setTranscribing(true);
      livePartialRef.current = "";
      setLivePartial("");
      try {
        const res = await api.transcribeDictation(
          file,
          languageRef.current,
          TRANSCRIBE_TIMEOUT_MS,
        );
        setProvider(res.provider);
        setTranscribing(false);
        const text = res.text?.trim() || "";
        livePartialRef.current = text;
        setLivePartial(text);
        if (!text) {
          setError("Aucune parole détectée dans ce fichier.");
          return null;
        }
        return { text, provider: res.provider };
      } catch (e) {
        setTranscribing(false);
        setError(e instanceof Error ? e.message : "Échec de la transcription.");
        return null;
      }
    },
    [],
  );

  return {
    recording,
    transcribing,
    error,
    provider,
    language,
    setLanguage,
    analyser,
    livePartial,
    startRecording,
    stopRecordingAndTranscribe,
    transcribeFile,
    supported:
      typeof window !== "undefined" &&
      !!navigator.mediaDevices?.getUserMedia &&
      typeof MediaRecorder !== "undefined",
  };
}
