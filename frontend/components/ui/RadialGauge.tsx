import * as React from "react"
import { cn } from "@/lib/utils"

export interface RadialGaugeProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number
  max: number
  label: string
  color?: string
  size?: number
  strokeWidth?: number
}

export function RadialGauge({
  value,
  max,
  label,
  color = "var(--color-primary)",
  size = 120,
  strokeWidth = 12,
  className,
  ...props
}: RadialGaugeProps) {
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI
  const percentage = Math.min(Math.max(value / max, 0), 1)
  const strokeDashoffset = circumference - percentage * circumference

  return (
    <div className={cn("relative flex flex-col items-center justify-center", className)} style={{ width: size }} {...props}>
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="var(--color-border-subtle)"
          strokeWidth={strokeWidth}
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          fill="none"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold">{value}</span>
        <span className="text-[10px] text-text-secondary font-medium uppercase tracking-wider">{label}</span>
      </div>
    </div>
  )
}
