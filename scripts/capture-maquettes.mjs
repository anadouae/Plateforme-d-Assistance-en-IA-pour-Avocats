/**
 * Capture des maquettes UI Sanad pour présentation professeur.
 * Usage: node scripts/capture-maquettes.mjs
 */
import { chromium } from "playwright";
import { mkdir, writeFile } from "fs/promises";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.resolve(__dirname, "../docs/maquettes");
const BASE = process.env.SANAD_URL || "http://localhost:3000";
const EMAIL = process.env.SANAD_EMAIL || "demo@sanad.ma";
const PASSWORD = process.env.SANAD_PASSWORD || "Sanad2026!";

const publicPages = [
  { slug: "01-accueil", url: "/", name: "Accueil / Landing" },
  { slug: "02-connexion", url: "/login", name: "Connexion" },
  { slug: "03-inscription", url: "/register", name: "Inscription cabinet" },
  { slug: "04-a-propos", url: "/about", name: "À propos" },
  { slug: "05-fonctionnalites", url: "/fonctionnalites", name: "Fonctionnalités" },
  { slug: "06-securite", url: "/securite", name: "Sécurité" },
  { slug: "07-mentions-legales", url: "/mentions-legales", name: "Mentions légales" },
  { slug: "08-confidentialite", url: "/confidentialite", name: "Confidentialité" },
  { slug: "09-mot-de-passe-oublie", url: "/forgot-password", name: "Mot de passe oublié" },
];

const appPages = [
  { slug: "10-tableau-de-bord", url: "/dashboard", name: "Tableau de bord" },
  { slug: "11-dossiers", url: "/cases", name: "Dossiers" },
  { slug: "12-nouveau-dossier", url: "/cases/new", name: "Nouveau dossier" },
  { slug: "13-documents", url: "/documents", name: "Documents" },
  { slug: "14-plaidoirie", url: "/redaction", name: "Plaidoirie — choix modèle" },
  { slug: "14b-plaidoirie-workspace", url: "/redaction/libre", name: "Plaidoirie — dictée & document" },
  { slug: "15-planning", url: "/agenda", name: "Planning" },
  { slug: "16-equipe", url: "/team", name: "Équipe" },
  { slug: "17-parametres", url: "/settings", name: "Paramètres" },
  { slug: "02b-connexion-actuelle", url: "/login", name: "Connexion (actuelle)" },
];

async function shot(page, slug, name, index, total) {
  const file = path.join(OUT, `${slug}.png`);
  await page.waitForTimeout(800);
  await page.screenshot({ path: file, fullPage: true });
  console.log(`[${index}/${total}] ${name} → ${slug}.png`);
  return { slug, name, file: `${slug}.png` };
}

async function main() {
  await mkdir(OUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    locale: "fr-FR",
  });
  const page = await context.newPage();
  const catalog = [];

  const total = publicPages.length + appPages.length;
  let i = 0;

  for (const p of publicPages) {
    i++;
    try {
      await page.goto(`${BASE}${p.url}`, { waitUntil: "networkidle", timeout: 120000 });
      catalog.push(await shot(page, p.slug, p.name, i, total));
    } catch (e) {
      console.error(`FAIL ${p.slug}:`, e.message);
      try {
        await page.screenshot({ path: path.join(OUT, `${p.slug}.png`), fullPage: true });
        catalog.push({ slug: p.slug, name: p.name + " (partiel)", file: `${p.slug}.png` });
      } catch {}
    }
  }

  // Login via API (plus fiable que le formulaire UI en headless)
  console.log("Login API…");
  const apiBase = process.env.SANAD_API || "http://localhost:8001";
  const loginRes = await fetch(`${apiBase}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
  });
  if (!loginRes.ok) {
    throw new Error(`Login API failed: ${loginRes.status} ${await loginRes.text()}`);
  }
  const auth = await loginRes.json();
  await page.goto(`${BASE}/login`, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.evaluate((data) => {
    localStorage.setItem("sanad_token", data.access_token);
    localStorage.setItem("sanad_refresh_token", data.refresh_token);
    localStorage.setItem(
      "sanad-auth",
      JSON.stringify({
        state: { user: data.user, token: data.access_token },
        version: 0,
      }),
    );
  }, auth);
  await page.goto(`${BASE}/dashboard`, { waitUntil: "networkidle", timeout: 120000 });
  await page.waitForTimeout(1500);
  console.log("After login URL:", page.url());

  for (const p of appPages) {
    i++;
    try {
      await page.goto(`${BASE}${p.url}`, { waitUntil: "networkidle", timeout: 120000 });
      await page.waitForTimeout(1000);
      // If redirected to login, skip
      if (page.url().includes("/login")) {
        console.error(`SKIP ${p.slug}: redirected to login`);
        continue;
      }
      catalog.push(await shot(page, p.slug, p.name, i, total));
    } catch (e) {
      console.error(`FAIL ${p.slug}:`, e.message);
      try {
        await page.screenshot({ path: path.join(OUT, `${p.slug}.png`), fullPage: true });
        catalog.push({ slug: p.slug, name: p.name + " (partiel)", file: `${p.slug}.png` });
      } catch {}
    }
  }

  const md = [
    "# Maquettes UI — Sanad",
    "",
    "**Plateforme d’Assistance en Intelligence Artificielle pour Avocats**",
    "",
    "Captures d’écran des interfaces de l’application (à présenter à l’encadrant école).",
    "",
    `Généré le : ${new Date().toLocaleString("fr-FR")}`,
    "",
    "| # | Écran | Fichier |",
    "|---|-------|---------|",
    ...catalog.map((c, idx) => `| ${idx + 1} | ${c.name} | \`${c.file}\` |`),
    "",
    "## Aperçu",
    "",
    ...catalog.map((c) => `### ${c.name}\n\n![${c.name}](./${c.file})\n`),
  ].join("\n");

  await writeFile(path.join(OUT, "README.md"), md, "utf8");
  console.log(`\nDone. ${catalog.length} maquettes → ${OUT}`);
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
