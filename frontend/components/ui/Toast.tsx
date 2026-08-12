import * as React from "react"
import { cn } from "@/lib/utils"

export interface ToastProps extends React.HTMLAttributes<HTMLDivElement> {
  title: string
  description?: string
  variant?: "default" | "error" | "success"
}

export function Toast({ title, description, variant = "default", className, ...props }: ToastProps) {
  return (
    <div
      className={cn(
        "glass-card px-4 py-3 flex flex-col gap-1 shadow-lg pointer-events-auto",
        {
          "border-error/50 bg-error/10": variant === "error",
          "border-success/50 bg-success/10": variant === "success",
        },
        className
      )}
      {...props}
    >
      <span className="text-sm font-semibold text-text-primary">{title}</span>
      {description && <span className="text-xs text-text-secondary">{description}</span>}
    </div>
  )
}

export function ToastContainer({ children }: { children: React.ReactNode }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
      {children}
    </div>
  )
}
