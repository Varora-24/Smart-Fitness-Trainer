"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/Card"
import { api, SupplementInfo } from "@/lib/api"

export default function Supplements() {
  const [data, setData] = useState<Record<string, SupplementInfo[]>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Hardcoded to match nutrition dev user goal "gain_muscle" for now
  const goal = "gain_muscle"

  useEffect(() => {
    async function load() {
      try {
        const result = await api.getSupplements()
        setData(result)
      } catch (err: any) {
        setError(err.message || "Failed to load supplements data")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const currentSupplements = data[goal] || []

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-text-primary">Supplements Guide</h1>
        <p className="text-text-secondary">Educational information for your current fitness goal.</p>
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
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {currentSupplements.map((item, idx) => (
            <Card key={idx}>
              <h3 className="text-lg font-semibold text-primary">{item.name}</h3>
              <p className="text-text-secondary text-sm mt-2">
                {item.note}
              </p>
            </Card>
          ))}
        </div>
      )}

      <div className="mt-8 p-4 rounded-lg bg-surface-container border border-border-subtle">
        <p className="text-xs text-text-muted">
          This is general educational information, not medical advice. Supplement needs vary by individual health status, 
          medications, and circumstances. Talk to a doctor or registered dietitian before starting any new supplement, 
          especially if you are pregnant, nursing, taking medication, or managing a health condition.
        </p>
      </div>
    </div>
  )
}
