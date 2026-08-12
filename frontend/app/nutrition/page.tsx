"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/Card"
import { RadialGauge } from "@/components/ui/RadialGauge"
import { api, NutritionResponse } from "@/lib/api"

export default function Nutrition() {
  const [data, setData] = useState<NutritionResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function load() {
      try {
        const result = await api.getNutrition({
          weight_kg: 75,
          height_cm: 180,
          age: 30,
          gender: "male",
          activity_level: "active",
          goal: "gain_muscle"
        })
        setData(result)
      } catch (err: any) {
        setError(err.message || "Failed to load nutrition data")
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-text-primary">Nutrition Targets</h1>
        <p className="text-text-secondary">Your calculated macro goals based on your profile.</p>
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
      ) : data && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="items-center justify-center py-8">
            <RadialGauge value={data.macros.calories} max={data.tdee * 1.5} label="Calories" color="var(--color-primary)" size={160} strokeWidth={16} />
          </Card>
          <Card className="items-center justify-center py-8">
            <RadialGauge value={data.macros.protein_g} max={250} label="Protein (g)" color="var(--color-secondary)" />
          </Card>
          <Card className="items-center justify-center py-8">
            <RadialGauge value={data.macros.carbs_g} max={400} label="Carbs (g)" color="var(--color-success)" />
          </Card>
          <Card className="items-center justify-center py-8">
            <RadialGauge value={data.macros.fat_g} max={120} label="Fat (g)" color="var(--color-error)" />
          </Card>
        </div>
      )}
    </div>
  )
}
