import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { Video } from "lucide-react"
import Link from "next/link"

export default function YogaCoach() {
  return (
    <div className="flex h-[80vh] w-full items-center justify-center p-4">
      <Card className="max-w-2xl w-full p-12 flex flex-col items-center text-center gap-6">
        <div className="w-20 h-20 rounded-full bg-[rgba(242,202,80,0.1)] flex items-center justify-center mb-2">
          {/* Using a generic icon for Yoga MVP placeholder */}
          <span className="text-4xl">🧘</span>
        </div>
        
        <div className="flex flex-col gap-3">
          <h1 className="text-3xl font-bold text-text-primary">Yoga Coach Coming Soon</h1>
          <p className="text-text-secondary max-w-lg mx-auto leading-relaxed">
            Live WebRTC yoga coaching is currently available through the existing Streamlit architecture and will be migrated to the Next.js experience in a future phase.
          </p>
        </div>

        <div className="mt-4">
          <Link href="/video-analysis">
            <Button variant="primary" size="lg" className="gap-2">
              <Video className="w-5 h-5" />
              Analyze a Yoga Video
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  )
}
