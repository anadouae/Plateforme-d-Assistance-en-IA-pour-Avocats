from pathlib import Path

html = Path(r"c:\Users\daurinia\Downloads\sanad-redesign (1).html").read_text(
    encoding="utf-8"
)
start = html.index("<style>") + 7
end = html.index("</style>")
css = html[start:end].strip()

extra = r"""

/* --- App wiring helpers (routing + a11y) — valeurs spec --- */
.wave { opacity: 0.25; }
.wave.is-listening { opacity: 1; }
.drop-zone.is-dragover {
  animation: none;
  border-style: solid;
  border-color: var(--gold);
  background: rgba(199,151,63,0.08);
}
.status-pill--closed { background: rgba(31,111,84,0.14); color: #155943; }
.tl-tag--rdv { background: rgba(199,151,63,0.15); color: #8a6321; }
[dir="rtl"] .dock-item::after {
  left: auto;
  right: 64px;
  transform: translateY(-50%) translateX(6px);
}
[dir="rtl"] .dock-item:hover::after {
  transform: translateY(-50%) translateX(0);
}
[dir="rtl"] .timeline { padding-left: 0; padding-right: 26px; }
[dir="rtl"] .timeline::before { left: auto; right: 6px; }
[dir="rtl"] .tl-item::before { left: auto; right: -25px; }
[dir="rtl"] .doc-row:hover { transform: translateX(-3px); }
[dir="rtl"] .avatar-stack .av { margin-left: 0; margin-right: -8px; }
[dir="rtl"] .avatar-stack .av:first-child { margin-right: 0; }
.shell { position: relative; z-index: 1; min-height: 100vh; }
.shell .main { width: 100%; }
.panel.show { display: block; animation: rise .5s cubic-bezier(.2,.9,.25,1); }
.dossier-card.ghost:hover { transform: none; }
@media (prefers-reduced-motion: reduce) {
  .blob, .orb span, .wave i, .status-pill::before, .drop-zone { animation: none !important; }
}
"""

out = Path(__file__).resolve().parents[1] / "src" / "styles" / "sanad-ui.css"
out.write_text(css + "\n" + extra, encoding="utf-8")
print("wrote", out, "bytes", out.stat().st_size)
