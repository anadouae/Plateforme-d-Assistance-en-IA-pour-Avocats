/** Password policy shared by login/register UI (mirrors backend). */

export const MIN_PASSWORD_LENGTH = 12;

export function passwordStrength(pw: string): number {
  let score = 0;
  if (pw.length >= MIN_PASSWORD_LENGTH) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  return score;
}

export function passwordRules(pw: string) {
  return {
    length: pw.length >= MIN_PASSWORD_LENGTH && pw.length <= 72,
    upperLower: /[A-Z]/.test(pw) && /[a-z]/.test(pw),
    digit: /[0-9]/.test(pw),
    symbol: /[^A-Za-z0-9]/.test(pw),
  };
}

export function isPasswordStrong(pw: string): boolean {
  const r = passwordRules(pw);
  return r.length && r.upperLower && r.digit && r.symbol;
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}
