import * as React from "react"
import { cn } from "@/lib/utils"

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant: "live" | "ai" | "good" | "bad" | "neutral"
}

export function StatusBadge({ className, variant, children, ...props }: StatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        {
          "bg-error text-white": variant === "live" || variant === "bad",
          "bg-secondary text-surface": variant === "ai",
          "bg-success text-surface": variant === "good",
          "bg-surface-elevated text-text-secondary border border-border-subtle": variant === "neutral",
        },
        className
      )}
      {...props}
    >
      {children}
    </span>
  )
}
