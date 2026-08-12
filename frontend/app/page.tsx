import { Card } from "@/components/ui/Card"
import { Metric } from "@/components/ui/Metric"
import { Button } from "@/components/ui/Button"
import { Activity, Dumbbell, TrendingUp } from "lucide-react"
import Link from "next/link"

export default function Home() {
  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto">
      {/* Welcome Section */}
      <section className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold text-text-primary">Welcome back, Athlete.</h1>
        <p className="text-text-secondary">Here is your training summary for this week.</p>
      </section>

      {/* Metrics Row */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <div className="flex items-center gap-3 text-secondary mb-2">
            <Activity className="w-5 h-5" />
            <h2 className="font-semibold text-text-primary">Sessions Completed</h2>
          </div>
          <Metric label="This Week" value="4" delta="+1" deltaType="positive" />
        </Card>
        
        <Card>
          <div className="flex items-center gap-3 text-secondary mb-2">
            <Dumbbell className="w-5 h-5" />
            <h2 className="font-semibold text-text-primary">Total Reps</h2>
          </div>
          <Metric label="This Week" value="342" delta="+42" deltaType="positive" />
        </Card>
        
        <Card>
          <div className="flex items-center gap-3 text-secondary mb-2">
            <TrendingUp className="w-5 h-5" />
            <h2 className="font-semibold text-text-primary">Avg Form Score</h2>
          </div>
          <Metric label="Trailing 7 days" value="88%" delta="-2%" deltaType="negative" />
        </Card>
      </section>

      {/* Quick Actions */}
      <section className="flex flex-col gap-4 mt-4">
        <h2 className="text-xl font-semibold text-text-primary">Quick Actions</h2>
        <div className="flex flex-wrap gap-4">
          <Button variant="primary" size="lg" className="gap-2">
            <Activity className="w-5 h-5" />
            Start Live Trainer
          </Button>
          <Button variant="secondary" size="lg" className="gap-2 text-surface">
            <Dumbbell className="w-5 h-5" />
            Start Yoga Coach
          </Button>
          <Link href="/video-analysis">
            <Button variant="glass" size="lg" className="gap-2">
              Upload Video for Analysis
            </Button>
          </Link>
        </div>
      </section>
    </div>
  )
}
