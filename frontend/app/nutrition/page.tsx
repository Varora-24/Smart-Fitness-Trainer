"use client"

import { useEffect, useState } from "react"
import { Card } from "@/components/ui/Card"
import { RadialGauge } from "@/components/ui/RadialGauge"
import { Button } from "@/components/ui/Button"
import { AlertCircle, Activity } from "lucide-react"
import { api, NutritionResponse } from "@/lib/api"

export default function Nutrition() {
  const [data, setData] = useState<NutritionResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Form State
  const [weight, setWeight] = useState("75")
  const [height, setHeight] = useState("180")
  const [age, setAge] = useState("30")
  const [gender, setGender] = useState("male")
  const [activity, setActivity] = useState("active")
  const [goal, setGoal] = useState("gain_muscle")

  const loadNutrition = async () => {
    // Basic validation
    const w = parseFloat(weight)
    const h = parseFloat(height)
    const a = parseInt(age, 10)

    if (isNaN(w) || w <= 0 || isNaN(h) || h <= 0 || isNaN(a) || a <= 0) {
      setError("Please enter valid numeric values for weight, height, and age.")
      return
    }

    setLoading(true)
    setError(null)

    try {
      const result = await api.getNutrition({
        weight_kg: w,
        height_cm: h,
        age: a,
        gender,
        activity_level: activity,
        goal
      })
      setData(result)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load nutrition data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadNutrition()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-text-primary">Nutrition Targets</h1>
        <p className="text-text-secondary">Your calculated macro goals based on your profile.</p>
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Compact Settings Panel */}
        <Card className="lg:col-span-1 p-6 flex flex-col gap-4">
          <h2 className="font-semibold text-text-primary flex items-center gap-2">
            <Activity className="w-5 h-5 text-secondary" />
            Your Profile
          </h2>
          
          <div className="grid grid-cols-2 gap-4 lg:flex lg:flex-col">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Weight (kg)</label>
              <input type="number" value={weight} onChange={e => setWeight(e.target.value)} className="w-full glass-input px-3 py-2 text-sm text-text-primary bg-surface" />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Height (cm)</label>
              <input type="number" value={height} onChange={e => setHeight(e.target.value)} className="w-full glass-input px-3 py-2 text-sm text-text-primary bg-surface" />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Age</label>
              <input type="number" value={age} onChange={e => setAge(e.target.value)} className="w-full glass-input px-3 py-2 text-sm text-text-primary bg-surface" />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1">Sex</label>
              <select value={gender} onChange={e => setGender(e.target.value)} className="w-full glass-input px-3 py-2 text-sm text-text-primary bg-surface">
                <option value="male">Male</option>
                <option value="female">Female</option>
              </select>
            </div>
            <div className="col-span-2 lg:col-span-1">
              <label className="block text-xs font-medium text-text-secondary mb-1">Activity Level</label>
              <select value={activity} onChange={e => setActivity(e.target.value)} className="w-full glass-input px-3 py-2 text-sm text-text-primary bg-surface">
                <option value="sedentary">Sedentary</option>
                <option value="light">Light</option>
                <option value="moderate">Moderate</option>
                <option value="active">Active</option>
                <option value="very_active">Very Active</option>
              </select>
            </div>
            <div className="col-span-2 lg:col-span-1">
              <label className="block text-xs font-medium text-text-secondary mb-1">Goal</label>
              <select value={goal} onChange={e => setGoal(e.target.value)} className="w-full glass-input px-3 py-2 text-sm text-text-primary bg-surface">
                <option value="lose_fat">Lose Fat</option>
                <option value="maintain">Maintain</option>
                <option value="gain_muscle">Gain Muscle</option>
              </select>
            </div>
          </div>
          
          <Button variant="primary" className="w-full mt-2" onClick={loadNutrition} disabled={loading}>
            {loading ? "Calculating..." : "Update Macros"}
          </Button>

          {error && (
            <div className="mt-2 p-3 bg-[rgba(239,68,68,0.05)] border border-error/20 rounded-lg flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-error shrink-0 mt-0.5" />
              <p className="text-xs text-error">{error}</p>
            </div>
          )}
        </Card>

        {/* Results Area */}
        <div className="lg:col-span-3 flex flex-col gap-6">
          {loading && !data ? (
            <Card className="p-8 flex justify-center items-center h-[300px]">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </Card>
          ) : data ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
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
          ) : null}
        </div>
      </div>
    </div>
  )
}
