"use client";

import { useEffect, useState } from "react";
import { BarChart3, Loader2, Play, RefreshCw } from "lucide-react";
import { AdminShell } from "@/components/layout/admin-shell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api, type BenchmarkSummary, type CorpusStats } from "@/lib/api";

export default function AdminBenchmarkPage() {
  const [stats, setStats] = useState<CorpusStats | null>(null);
  const [benchmark, setBenchmark] = useState<BenchmarkSummary | null>(null);
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState("");

  const load = () => {
    api.getCorpusStats().then(setStats).catch(() => {});
    api.getBenchmarkResults().then((r) => {
      if ("results" in r && r.results) setBenchmark(r.results);
      else setMessage("message" in r ? r.message : "");
    }).catch(() => {});
  };

  useEffect(() => { load(); }, []);

  const run = async () => {
    setRunning(true);
    try {
      const result = await api.runBenchmark();
      setBenchmark(result);
      setMessage("");
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Erreur benchmark");
    } finally {
      setRunning(false);
    }
  };

  return (
    <AdminShell>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="flex items-center gap-2 text-2xl font-bold text-sanad-slate">
            <BarChart3 className="h-6 w-6 text-sanad-blue" />
            Benchmark juridique MA (50 questions)
          </h1>
          <div className="flex gap-2">
            <Button variant="outline" onClick={load}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Actualiser
            </Button>
            <Button onClick={run} disabled={running}>
              {running ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Play className="mr-2 h-4 w-4" />}
              Lancer le benchmark
            </Button>
          </div>
        </div>

        {message && <p className="text-sm text-slate-500">{message}</p>}

        {stats && (
          <div className="grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="p-6">
                <p className="text-2xl font-bold">{stats.total_entries}</p>
                <p className="text-sm text-slate-500">Entrées corpus (cible Adala : {stats.target_adala.toLocaleString()})</p>
              </CardContent>
            </Card>
            {Object.entries(stats.collections).map(([name, c]) => (
              <Card key={name}>
                <CardContent className="p-6">
                  <p className="text-lg font-bold">{c.entries}</p>
                  <p className="text-sm text-slate-500">{name} — {c.chunks_indexed} chunks indexés</p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {benchmark && (
          <>
            <div className="grid gap-4 sm:grid-cols-4">
              <Card><CardContent className="p-6"><p className="text-2xl font-bold text-green-600">{benchmark.pass_rate_pct}%</p><p className="text-sm text-slate-500">Taux de réussite</p></CardContent></Card>
              <Card><CardContent className="p-6"><p className="text-2xl font-bold">{benchmark.avg_score}</p><p className="text-sm text-slate-500">Score moyen</p></CardContent></Card>
              <Card><CardContent className="p-6"><p className="text-2xl font-bold">{benchmark.passed}/{benchmark.total}</p><p className="text-sm text-slate-500">Questions réussies</p></CardContent></Card>
              <Card><CardContent className="p-6"><p className="text-xs text-slate-500">Réf. Kanoun</p><p className="text-sm font-medium">{benchmark.kanoun_reference}</p></CardContent></Card>
            </div>

            <Card>
              <CardContent className="p-0">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-sanad-light text-left text-slate-500">
                      <th className="px-4 py-3">#</th>
                      <th className="px-4 py-3">Domaine</th>
                      <th className="px-4 py-3">Question</th>
                      <th className="px-4 py-3">Score</th>
                      <th className="px-4 py-3">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {benchmark.results.map((r) => (
                      <tr key={r.id} className="border-b border-sanad-border">
                        <td className="px-4 py-2">{r.id}</td>
                        <td className="px-4 py-2">{r.domain}</td>
                        <td className="max-w-md truncate px-4 py-2">{r.question}</td>
                        <td className="px-4 py-2">{r.score}</td>
                        <td className="px-4 py-2">
                          <span className={r.passed ? "text-green-600" : "text-red-600"}>
                            {r.passed ? "OK" : "Échec"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AdminShell>
  );
}
