@echo off
REM Compile le rapport PFA LexHub (2 passes pdflatex)
cd /d "%~dp0"
where pdflatex >nul 2>&1
if errorlevel 1 (
  echo pdflatex introuvable. Installez MiKTeX ou TeX Live, ou uploadez sur Overleaf.
  exit /b 1
)
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
echo.
if exist main.pdf (
  echo OK: main.pdf genere.
) else (
  echo Echec compilation - voir main.log
)
