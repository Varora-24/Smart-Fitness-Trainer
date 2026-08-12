"use client"

import { useState } from "react"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { Metric } from "@/components/ui/Metric"
import { StatusBadge } from "@/components/ui/StatusBadge"
import { api, VideoAnalysisResponse } from "@/lib/api"
import { Video, UploadCloud, AlertCircle } from "lucide-react"

const EXERCISE_OPTIONS = [
  { value: "squats", label: "Squats" },
  { value: "pushups", label: "Push-ups" },
  { value: "curls", label: "Bicep Curls" },
  { value: "lunges", label: "Lunges" },
  { value: "shoulder_press", label: "Shoulder Press" },
  { value: "chair_pose", label: "Chair Pose (Yoga)" },
  { value: "warrior_2", label: "Warrior II (Yoga)" },
  { value: "tree_pose", label: "Tree Pose (Yoga)" },
]

export default function VideoAnalysis() {
  const [file, setFile] = useState<File | null>(null)
  const [exercise, setExercise] = useState(EXERCISE_OPTIONS[0].value)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<VideoAnalysisResponse | null>(null)

  const handleUpload = async () => {
    if (!file) return
    setProcessing(true)
    setError(null)
    setResult(null)

    try {
      const res = await api.analyzeVideo(file, exercise)
      setResult(res)
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred during processing.")
    } finally {
      setProcessing(false)
    }
  }

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-text-primary">Video Analysis</h1>
        <p className="text-text-secondary">Upload a workout clip for AI-powered biomechanical feedback.</p>
      </section>

      {!processing && !result && (
        <Card className="p-8 max-w-2xl">
          <div className="flex flex-col gap-6">
            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">Exercise / Pose</label>
              <select 
                className="w-full glass-input px-4 py-3 text-text-primary bg-surface"
                value={exercise}
                onChange={(e) => setExercise(e.target.value)}
              >
                {EXERCISE_OPTIONS.map(opt => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-text-secondary mb-2">Video File</label>
              <div className="border-2 border-dashed border-border-subtle rounded-xl p-8 text-center bg-[rgba(255,255,255,0.01)] hover:bg-[rgba(255,255,255,0.03)] transition-colors">
                <input 
                  type="file" 
                  accept="video/mp4,video/quicktime,video/x-msvideo,video/x-matroska"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden" 
                  id="video-upload"
                />
                <label htmlFor="video-upload" className="cursor-pointer flex flex-col items-center gap-3">
                  <UploadCloud className="w-10 h-10 text-secondary" />
                  <div className="text-sm">
                    <span className="font-semibold text-primary">Click to upload</span> or drag and drop
                  </div>
                  <p className="text-xs text-text-muted">MP4, MOV, AVI, MKV (Max 100MB, up to 90s)</p>
                </label>
                {file && (
                  <div className="mt-4 p-3 bg-surface-container rounded-lg border border-border-subtle flex justify-between items-center">
                    <span className="text-sm font-medium truncate max-w-[200px]">{file.name}</span>
                    <span className="text-xs text-text-muted">{(file.size / (1024*1024)).toFixed(1)} MB</span>
                  </div>
                )}
              </div>
            </div>

            {error && (
              <div className="p-4 bg-[rgba(239,68,68,0.05)] border border-error/20 rounded-lg flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-error shrink-0 mt-0.5" />
                <p className="text-sm text-error">{error}</p>
              </div>
            )}

            <Button 
              variant="primary" 
              className="w-full mt-2" 
              disabled={!file}
              onClick={handleUpload}
            >
              Start Analysis
            </Button>
          </div>
        </Card>
      )}

      {processing && (
        <Card className="p-12 flex flex-col items-center justify-center text-center gap-6 max-w-2xl h-80">
          <div className="relative">
            <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-primary absolute inset-0"></div>
            <div className="animate-spin rounded-full h-16 w-16 border-l-2 border-r-2 border-secondary absolute inset-0 opacity-50 blur-sm animation-delay-150"></div>
            <div className="w-16 h-16 rounded-full bg-[rgba(0,210,253,0.1)] flex items-center justify-center relative">
              <Video className="w-6 h-6 text-primary animate-pulse" />
            </div>
          </div>
          <div>
            <h3 className="text-xl font-bold text-text-primary">AI is Analyzing your Video...</h3>
            <p className="text-sm text-text-secondary mt-2">Processing frame by frame. This may take a minute.</p>
          </div>
        </Card>
      )}

      {result && (
        <div className="flex flex-col gap-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-text-primary">Results</h2>
            <Button variant="secondary" onClick={() => { setResult(null); setFile(null); }}>
              Analyze Another Video
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="py-6 flex flex-col justify-center gap-2">
              <p className="text-text-secondary text-sm font-medium">Exercise</p>
              <p className="text-2xl font-bold text-primary capitalize">{result.summary.exercise.replace("_", " ")}</p>
            </Card>
            
            {result.is_yoga ? (
              <>
                <Card className="py-6 flex flex-col justify-center gap-2">
                  <p className="text-text-secondary text-sm font-medium">Avg Alignment</p>
                  <p className="text-3xl font-bold text-text-primary">{result.summary.avg_alignment?.toFixed(1)}%</p>
                </Card>
                <Card className="py-6 flex flex-col justify-center gap-2">
                  <p className="text-text-secondary text-sm font-medium">Duration Analyzed</p>
                  <p className="text-3xl font-bold text-text-primary">{result.summary.duration_secs.toFixed(1)}s</p>
                </Card>
              </>
            ) : (
              <>
                <Card className="py-6 flex flex-col justify-center gap-2">
                  <p className="text-text-secondary text-sm font-medium">Good / Total Reps</p>
                  <div className="flex items-baseline gap-2">
                    <p className="text-3xl font-bold text-text-primary">{result.summary.clean_reps}</p>
                    <p className="text-text-muted">/ {result.summary.total_reps}</p>
                  </div>
                </Card>
                <Card className="py-6 flex flex-col justify-center gap-2">
                  <p className="text-text-secondary text-sm font-medium">Avg Form Score</p>
                  <p className="text-3xl font-bold text-text-primary">{result.summary.avg_rep_score.toFixed(1)}</p>
                </Card>
                <Card className="py-6 flex flex-col justify-center gap-2">
                  <p className="text-text-secondary text-sm font-medium">Calories Burned</p>
                  <p className="text-3xl font-bold text-text-primary">{result.summary.calories} kcal</p>
                </Card>
              </>
            )}
          </div>

          {/* Detailed Telemetry */}
          {!result.is_yoga && result.reps && result.reps.length > 0 && (
            <Card className="p-0 overflow-hidden mt-4">
              <div className="p-4 border-b border-border-subtle bg-surface-container">
                <h3 className="font-semibold text-text-primary">Per-Rep Biomechanics</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-surface border-b border-border-subtle text-text-secondary">
                    <tr>
                      <th className="px-6 py-4 font-medium">Rep #</th>
                      <th className="px-6 py-4 font-medium">Symmetry</th>
                      <th className="px-6 py-4 font-medium">Range of Motion</th>
                      <th className="px-6 py-4 font-medium">Posture</th>
                      <th className="px-6 py-4 font-medium">Control</th>
                      <th className="px-6 py-4 font-medium">Rep Score</th>
                      <th className="px-6 py-4 font-medium">Quality</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border-subtle">
                    {result.reps.map((rep) => (
                      <tr key={rep.rep_number} className="hover:bg-[rgba(255,255,255,0.02)] transition-colors">
                        <td className="px-6 py-4 font-medium text-text-primary">{rep.rep_number}</td>
                        <td className="px-6 py-4">{rep.symmetry.toFixed(1)}</td>
                        <td className="px-6 py-4">{rep.range_of_motion.toFixed(1)}</td>
                        <td className="px-6 py-4">{rep.posture.toFixed(1)}</td>
                        <td className="px-6 py-4">{rep.control.toFixed(1)}</td>
                        <td className="px-6 py-4 font-mono text-secondary">{rep.rep_score.toFixed(1)}</td>
                        <td className="px-6 py-4">
                          <StatusBadge variant={rep.rep_label === "good_rep" ? "good" : "bad"}>
                            {rep.rep_label === "good_rep" ? "Good" : "Needs Work"}
                          </StatusBadge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          )}

          {result.is_yoga && result.yoga_scores && result.yoga_scores.length > 0 && (
            <Card className="mt-4">
              <h3 className="font-semibold text-text-primary mb-4">Alignment Over Time</h3>
              <p className="text-sm text-text-secondary mb-4">
                The AI tracked your pose alignment across {result.yoga_scores.length} specific keyframes.
              </p>
              <div className="flex items-center gap-4 text-sm font-mono text-primary bg-[rgba(242,202,80,0.05)] p-4 rounded-lg">
                 [Chart rendering omitted for MVP - Data is captured securely]
              </div>
            </Card>
          )}

          {((!result.is_yoga && (!result.reps || result.reps.length === 0)) || 
             (result.is_yoga && (!result.yoga_scores || result.yoga_scores.length === 0))) && (
            <Card className="p-8 flex flex-col items-center justify-center text-center gap-4 bg-[rgba(255,255,255,0.01)] border-border-subtle border-dashed">
               <AlertCircle className="w-8 h-8 text-secondary" />
               <div>
                  <h3 className="text-lg font-semibold text-text-primary">No Reps/Poses Detected</h3>
                  <p className="text-sm text-text-secondary mt-1">Make sure your full body is visible and you selected the correct exercise.</p>
               </div>
            </Card>
          )}
        </div>
      )}
    </div>
  )
}
