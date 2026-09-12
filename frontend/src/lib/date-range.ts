/** Filtre optionnel par plage de dates (YYYY-MM-DD). */
export function inDateRange(iso: string | undefined | null, from: string, to: string) {
  if (!iso) return !from && !to;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return false;
  if (from) {
    const start = new Date(from);
    start.setHours(0, 0, 0, 0);
    if (t < start.getTime()) return false;
  }
  if (to) {
    const end = new Date(to);
    end.setHours(23, 59, 59, 999);
    if (t > end.getTime()) return false;
  }
  return true;
}
