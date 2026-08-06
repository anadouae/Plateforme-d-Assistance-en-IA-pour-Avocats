"use client";

import { useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential: string }) => void;
          }) => void;
          renderButton: (
            element: HTMLElement,
            config: { theme?: string; size?: string; width?: number; text?: string; locale?: string },
          ) => void;
        };
      };
    };
  }
}

interface GoogleSignInProps {
  onSuccess: (idToken: string) => void;
  onError?: () => void;
  label: string;
  disabled?: boolean;
}

const CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

export function GoogleSignIn({ onSuccess, onError, label, disabled }: GoogleSignInProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!CLIENT_ID || disabled || !ref.current) return;

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.onload = () => {
      if (!window.google || !ref.current) return;
      window.google.accounts.id.initialize({
        client_id: CLIENT_ID,
        callback: (res) => onSuccess(res.credential),
      });
      ref.current.innerHTML = "";
      window.google.accounts.id.renderButton(ref.current, {
        theme: "outline",
        size: "large",
        width: 320,
        text: "continue_with",
      });
    };
    script.onerror = () => onError?.();
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, [onSuccess, onError, disabled]);

  if (!CLIENT_ID) {
    return (
      <Button variant="outline" className="w-full border-sanad-gold/20" disabled title="Configurez GOOGLE_CLIENT_ID">
        {label}
      </Button>
    );
  }

  return <div ref={ref} className="flex justify-center" />;
}
