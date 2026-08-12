"use client"

import { useEffect } from "react"
import { Card } from "@/components/ui/Card"
import { Button } from "@/components/ui/Button"
import { AlertCircle } from "lucide-react"
import { useRouter } from "next/navigation"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  const router = useRouter()

  useEffect(() => {
    // Log the error to an error reporting service if this were production
    console.error(error)
  }, [error])

  return (
    <div className="flex h-[80vh] w-full items-center justify-center p-4">
      <Card className="max-w-md w-full p-8 flex flex-col items-center text-center gap-6 border-error/20 bg-[rgba(239,68,68,0.02)]">
        <div className="w-16 h-16 rounded-full bg-[rgba(239,68,68,0.1)] flex items-center justify-center">
          <AlertCircle className="w-8 h-8 text-error" />
        </div>
        
        <div className="flex flex-col gap-2">
          <h2 className="text-xl font-bold text-text-primary">Something went wrong</h2>
          <p className="text-sm text-text-secondary">
            Arogya Vision encountered an unexpected error. Please try again.
          </p>
        </div>

        <div className="flex gap-4 w-full mt-2">
          <Button 
            variant="secondary" 
            className="flex-1"
            onClick={() => router.push('/')}
          >
            Go Home
          </Button>
          <Button 
            variant="primary" 
            className="flex-1"
            onClick={() => reset()}
          >
            Try Again
          </Button>
        </div>
      </Card>
    </div>
  )
}
