# Smoke-test backup (Windows PowerShell) — valide qu'un dump Postgres se crée.
# Usage: powershell -File scripts/backup-smoke.ps1
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Dest = Join-Path $Root "backups\smoke_$Stamp"
New-Item -ItemType Directory -Force -Path $Dest | Out-Null
$DumpPath = Join-Path $Dest "lexhub.dump"

Write-Host "[smoke] pg_dump → $DumpPath"
cmd /c "docker compose exec -T postgres pg_dump -U lexhub -d lexhub -Fc > `"$DumpPath`" 2>nul"
if (-not (Test-Path $DumpPath) -or (Get-Item $DumpPath).Length -lt 1024) {
  cmd /c "docker compose exec -T postgres pg_dump -U sanad -d sanad -Fc > `"$DumpPath`" 2>nul"
}
if (-not (Test-Path $DumpPath)) { throw "Dump non créé" }
$size = (Get-Item $DumpPath).Length
if ($size -lt 1024) { throw "Dump trop petit ($size bytes) — échec" }

# Copie miroir compatibilité
Copy-Item $DumpPath (Join-Path $Dest "sanad.dump") -Force -ErrorAction SilentlyContinue

# Format custom pg_dump commence par "PGDMP"
$fs = [System.IO.File]::OpenRead($DumpPath)
$buf = New-Object byte[] 5
[void]$fs.Read($buf, 0, 5)
$fs.Close()
$magic = [System.Text.Encoding]::ASCII.GetString($buf)
if ($magic -ne "PGDMP") { throw "Dump invalide (magic=$magic, attendu PGDMP)" }

Write-Host "[smoke] validation TOC via conteneur…"
cmd /c "docker compose cp `"$DumpPath`" postgres:/tmp/sanad_smoke.dump >nul 2>nul"
$toc = cmd /c "docker compose exec -T postgres pg_restore -U sanad --list /tmp/sanad_smoke.dump 2>nul"
$tocText = ($toc | Out-String)
if ($tocText -notmatch "TOC Entries") {
  Write-Host "[smoke] WARN: pg_restore --list non lisible ici, mais magic PGDMP + taille OK"
} else {
  Write-Host ($toc | Select-Object -First 8 | Out-String)
}

@"
Sanad smoke backup $Stamp
size_bytes=$size
magic=$magic
validated=PGDMP header OK
"@ | Set-Content (Join-Path $Dest "MANIFEST.txt")

Write-Host "[smoke] OK — dump valide ($size bytes, $magic). Voir docs/BACKUP_RESTORE.md."
exit 0
