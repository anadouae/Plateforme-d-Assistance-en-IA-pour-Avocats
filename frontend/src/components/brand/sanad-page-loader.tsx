"use client";

/** Logo LexHub 3D — sans texte. CSS only (évite l’erreur d’hydratation Framer Motion). */
export function SanadPageLoader({ compact = false }: { compact?: boolean }) {
  const size = compact ? 88 : 132;
  return (
    <div
      className={compact ? "sanad-loader sanad-loader--compact" : "sanad-loader"}
      role="status"
      aria-label="LexHub"
    >
      <div className="sanad-loader__scene">
        <span className="sanad-loader__orbit" aria-hidden />
        <span className="sanad-loader__orbit sanad-loader__orbit--slow" aria-hidden />
        <div className="sanad-loader__stage" style={{ width: size, height: size }}>
          <span className="sanad-loader__glow" aria-hidden />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/logo-lexhub-cube.png?v=cube-2"
            alt=""
            width={size}
            height={size}
            className="sanad-loader__cube"
          />
        </div>
      </div>
      <div className="sanad-loader__bar" aria-hidden>
        <span className="sanad-loader__fill" />
      </div>
    </div>
  );
}

/** Alias marque LexHub (même composant). */
export const LexHubPageLoader = SanadPageLoader;
