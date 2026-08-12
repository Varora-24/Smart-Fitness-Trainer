import * as React from "react"
import { cn } from "@/lib/utils"

export interface MetricProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string
  value: string | number
  delta?: string
  deltaType?: "positive" | "negative" | "neutral"
}

export function Metric({ label, value, delta, deltaType, className, ...props }: MetricProps) {
  return (
    <div className={cn("flex flex-col gap-1", className)} {...props}>
      <span className="text-sm font-medium text-text-secondary">{label}</span>
      <div className="flex items-baseline gap-2">
        <span className="text-4xl font-bold tracking-tight text-text-primary font-sans">{value}</span>
        {delta && (
          <span
            className={cn("text-xs font-semibold", {
              "text-success": deltaType === "positive",
              "text-error": deltaType === "negative",
              "text-text-muted": deltaType === "neutral",
            })}
          >
            {delta}
          </span>
        )}
      </div>
    </div>
  )
}
