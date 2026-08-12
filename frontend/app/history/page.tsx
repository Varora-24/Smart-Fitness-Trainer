"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/Card"
import { StatusBadge } from "@/components/ui/StatusBadge"
import { api, HistorySession } from "@/lib/api"
import { Activity } from "lucide-react"

export default function History() {
  const [data, setData] = useState<HistorySession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const history = await api.getHistory()
        setData(history)
      } catch (err: any) {
        setError(err.message || "Failed to load history")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-text-primary">Workout History</h1>
        <p className="text-text-secondary">Review your past sessions and form trends.</p>
      </section>

      {loading ? (
        <Card className="p-8 flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </Card>
      ) : error ? (
        <Card className="p-8 flex flex-col items-center justify-center h-64 gap-4 bg-[rgba(239,68,68,0.05)] border-error/20">
          <p className="text-error font-medium">{error}</p>
          <button onClick={() => window.location.reload()} className="btn-secondary px-4 py-2 text-sm">Retry</button>
        </Card>
      ) : data.length === 0 ? (
        <Card className="p-12 flex flex-col items-center justify-center text-center gap-4">
          <div className="w-16 h-16 rounded-full bg-surface-container flex items-center justify-center">
            <Activity className="w-8 h-8 text-text-muted" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-text-primary">No History Yet</h3>
            <p className="text-sm text-text-secondary mt-1 max-w-sm">Complete your first video analysis or live trainer session to see your progress here.</p>
          </div>
        </Card>
      ) : (
        <Card className="p-0 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-surface-container border-b border-border-subtle text-text-secondary">
                <tr>
                  <th className="px-6 py-4 font-medium">Date</th>
                  <th className="px-6 py-4 font-medium">Exercise</th>
                  <th className="px-6 py-4 font-medium">Total Reps</th>
                  <th className="px-6 py-4 font-medium">Avg Score</th>
                  <th className="px-6 py-4 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle">
                {data.map((session) => {
                  const dateObj = new Date(session.date)
                  const dateStr = isNaN(dateObj.getTime()) ? session.date : dateObj.toLocaleDateString()
                  
                  // Simple heuristic for label since history table doesn't have it natively in DB
                  const label = session.avg_rep_score >= 80 ? "good" : session.avg_rep_score >= 60 ? "neutral" : "bad"
                  const badgeText = label === "good" ? "Excellent" : label === "bad" ? "Needs Work" : "Fair"

                  return (
                    <tr key={session.id} className="hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                      <td className="px-6 py-4 text-text-muted">{dateStr}</td>
                      <td className="px-6 py-4 font-medium text-text-primary capitalize">{session.exercise.replace("_", " ")}</td>
                      <td className="px-6 py-4 text-text-primary">{session.total_reps}</td>
                      <td className="px-6 py-4 font-mono text-secondary">{session.avg_rep_score.toFixed(1)}/100</td>
                      <td className="px-6 py-4">
                        <StatusBadge variant={label as any}>
                          {badgeText}
                        </StatusBadge>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
