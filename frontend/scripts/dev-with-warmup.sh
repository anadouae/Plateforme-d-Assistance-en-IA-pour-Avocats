#!/bin/sh
# Next.js cold start: compile les routes critiques dès le boot Docker.
set -eu

echo "[sanad] starting next dev…"
npm run dev -- --hostname 0.0.0.0 --port 3000 &
PID=$!

cleanup() {
  kill "$PID" 2>/dev/null || true
}
trap cleanup INT TERM

echo "[sanad] waiting for Next.js…"
i=0
while [ "$i" -lt 90 ]; do
  if wget -q -O /dev/null "http://127.0.0.1:3000/login" 2>/dev/null; then
    echo "[sanad] Next.js ready — warming routes"
    break
  fi
  i=$((i + 1))
  sleep 2
done

for path in \
  /login \
  /home \
  /dashboard \
  /cases \
  /documents \
  /redaction \
  /agenda \
  /team \
  /settings \
  /join
do
  wget -q -O /dev/null "http://127.0.0.1:3000${path}" 2>/dev/null \
    && echo "[sanad] warmed ${path}" \
    || echo "[sanad] warm skip ${path}"
done

echo "[sanad] warmup done — keeping next dev (pid $PID)"
wait "$PID"
