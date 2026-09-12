from pathlib import Path

api = Path(r"C:\Users\daurinia\Desktop\Avocat-AI-Assistance\frontend\src\lib\api.ts")
t = api.read_text(encoding="utf-8")
needle = """  undoCancelSubscription: () =>
    request<{ message: string }>("/api/billing/cancel/undo", {
      method: "POST",
      body: JSON.stringify({}),
    }),
"""
insert = needle + """
  simulatePaymentFailed: () =>
    request<{ message: string }>("/api/billing/payment-failed", {
      method: "POST",
      body: JSON.stringify({}),
    }),
"""
if "simulatePaymentFailed" not in t:
    if needle not in t:
        raise SystemExit("undoCancel block not found")
    api.write_text(t.replace(needle, insert), encoding="utf-8")
    print("api ok")
else:
    print("api already")
