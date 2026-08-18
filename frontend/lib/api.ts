const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api"

export interface HistorySession {
  id: number
  exercise: string
  total_reps: number
  clean_reps: number
  bad_reps: number
  calories: number
  duration_secs: number
  avg_rep_score: number
  date: string
}

export interface NutritionResponse {
  bmr: number
  tdee: number
  macros: {
    protein_g: number
    carbs_g: number
    fat_g: number
    calories: number
  }
}

export interface SupplementInfo {
  name: string
  note: string
}

export interface VideoSummary {
  exercise: string
  total_reps: number
  clean_reps: number
  bad_reps: number
  calories: number
  duration_secs: number
  avg_rep_score: number
  avg_symmetry: number
  avg_form: number
  avg_alignment?: number | null
}

export interface RepData {
  rep_number: number
  symmetry: number
  range_of_motion: number
  posture: number
  control: number
  rep_score: number
  rep_label: string
}

export interface YogaScore {
  frame: number
  time_s: number
  score: number
}

export interface VideoAnalysisResponse {
  is_yoga: boolean
  summary: VideoSummary
  reps?: RepData[] | null
  yoga_scores?: YogaScore[] | null
}

// Helper to catch network errors vs HTTP errors
async function fetchWithHandling(url: string, options?: RequestInit) {
  let res;
  try {
    res = await fetch(url, options)
  } catch (_err) {
    throw new Error("Unable to connect to the Arogya Vision API. Please make sure the backend is running.")
  }
  return res;
}

export const api = {
  getHistory: async (exercise?: string): Promise<HistorySession[]> => {
    const url = exercise ? `${API_BASE}/history?exercise=${encodeURIComponent(exercise)}` : `${API_BASE}/history`
    const res = await fetchWithHandling(url)
    if (!res.ok) throw new Error("Failed to fetch history")
    return res.json()
  },

  getNutrition: async (params: {
    weight_kg: number
    height_cm: number
    age: number
    gender: string
    activity_level: string
    goal: string
  }): Promise<NutritionResponse> => {
    const search = new URLSearchParams()
    Object.entries(params).forEach(([key, value]) => search.append(key, value.toString()))
    const res = await fetchWithHandling(`${API_BASE}/nutrition?${search.toString()}`)
    if (!res.ok) throw new Error("Failed to fetch nutrition")
    return res.json()
  },

  getSupplements: async (): Promise<Record<string, SupplementInfo[]>> => {
    const res = await fetchWithHandling(`${API_BASE}/supplements`)
    if (!res.ok) throw new Error("Failed to fetch supplements")
    return res.json()
  },

  analyzeVideo: async (file: File, exercise: string): Promise<VideoAnalysisResponse> => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("exercise", exercise)
    
    const res = await fetchWithHandling(`${API_BASE}/analyze-video`, {
      method: "POST",
      body: formData,
    })
    if (!res.ok) {
      throw new Error(`Video analysis failed. Please try another video.`)
    }
    return res.json()
  }
}
