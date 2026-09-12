import type { ReactNode } from "react";

/** Détection simple du réseau carte (Visa / Mastercard). */
export function detectCardBrand(num: string): "visa" | "mastercard" | null {
  const d = num.replace(/\D/g, "");
  if (!d) return null;
  if (d.startsWith("4")) return "visa";
  if (/^5[1-5]/.test(d) || /^2[2-7]/.test(d)) return "mastercard";
  return null;
}

function BadgeFrame({
  active,
  children,
  label,
}: {
  active?: boolean;
  children: ReactNode;
  label: string;
}) {
  return (
    <span
      className={`inline-flex h-8 w-[46px] items-center justify-center rounded-md border bg-white shadow-sm transition ${
        active ? "border-[#1B3F9C] ring-2 ring-[#1B3F9C]/20" : "border-slate-200 opacity-90"
      }`}
      aria-label={label}
      title={label}
    >
      {children}
    </span>
  );
}

function VisaLogo() {
  return (
    <svg viewBox="0 0 48 16" className="h-3.5 w-10" aria-hidden>
      <rect width="48" height="16" rx="2" fill="#1A1F71" />
      <text
        x="24"
        y="11.5"
        textAnchor="middle"
        fill="#fff"
        fontSize="9"
        fontWeight="700"
        fontFamily="Arial, sans-serif"
        letterSpacing="0.5"
      >
        VISA
      </text>
    </svg>
  );
}

function MastercardLogo() {
  return (
    <svg viewBox="0 0 48 30" className="h-5 w-8" aria-hidden>
      <circle cx="18" cy="15" r="11" fill="#EB001B" />
      <circle cx="30" cy="15" r="11" fill="#F79E1B" fillOpacity="0.95" />
      <path
        d="M24 7.2a11 11 0 0 1 0 15.6A11 11 0 0 1 24 7.2Z"
        fill="#FF5F00"
        fillOpacity="0.85"
      />
    </svg>
  );
}

function CmiLogo() {
  return (
    <svg viewBox="0 0 48 16" className="h-3.5 w-10" aria-hidden>
      <rect width="48" height="16" rx="2" fill="#0B5C4B" />
      <text
        x="24"
        y="11.5"
        textAnchor="middle"
        fill="#fff"
        fontSize="8.5"
        fontWeight="700"
        fontFamily="Arial, sans-serif"
        letterSpacing="0.3"
      >
        CMI
      </text>
    </svg>
  );
}

type Props = {
  className?: string;
  /** Met en avant le réseau détecté depuis le numéro saisi. */
  cardNumber?: string;
};

export function CardBrandBadges({ className = "", cardNumber }: Props) {
  const detected = cardNumber ? detectCardBrand(cardNumber) : null;

  return (
    <div className={`flex flex-wrap items-center gap-2 ${className}`} aria-label="Cartes acceptées">
      <BadgeFrame label="Visa" active={!detected || detected === "visa"}>
        <VisaLogo />
      </BadgeFrame>
      <BadgeFrame label="Mastercard" active={!detected || detected === "mastercard"}>
        <MastercardLogo />
      </BadgeFrame>
      <BadgeFrame label="CMI — Centre Monétique Interbancaire">
        <CmiLogo />
      </BadgeFrame>
    </div>
  );
}
