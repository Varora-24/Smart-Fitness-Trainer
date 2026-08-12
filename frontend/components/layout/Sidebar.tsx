"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  Home,
  Video,
  Activity,
  History,
  Apple,
  Pill,
} from "lucide-react"

const NAV_ITEMS = [
  { name: "Home", href: "/", icon: Home },
  { name: "Live Trainer", href: "/live-trainer", icon: Activity },
  { name: "Yoga Coach", href: "/yoga", icon: Activity },
  { name: "History", href: "/history", icon: History },
  { name: "Video Analysis", href: "/video-analysis", icon: Video },
  { name: "Nutrition", href: "/nutrition", icon: Apple },
  { name: "Supplements", href: "/supplements", icon: Pill },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-[260px] flex-shrink-0 border-r border-border-subtle bg-surface/50 backdrop-blur-xl flex flex-col h-screen sticky top-0">
      {/* Brand Header */}
      <div className="h-[72px] flex items-center px-6 border-b border-border-subtle shrink-0 gap-3">
        <img src="/assets/AV_icon_512.png" alt="Arogya Vision Logo" className="w-8 h-8 object-contain" />
        <img src="/assets/wordmark.png" alt="Arogya Vision Wordmark" className="h-5 object-contain" />
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-6 px-4 flex flex-col gap-2">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200",
                isActive
                  ? "bg-[rgba(242,202,80,0.1)] text-primary shadow-[inset_4px_0_0_0_var(--color-primary)]"
                  : "text-text-secondary hover:bg-[rgba(255,255,255,0.04)] hover:text-text-primary"
              )}
            >
              <item.icon className={cn("w-5 h-5", isActive ? "text-primary" : "text-text-muted")} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* User Area */}
      <div className="p-4 border-t border-border-subtle">
        <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-[rgba(255,255,255,0.02)]">
          <div className="w-8 h-8 rounded-full bg-surface-container border border-border-subtle flex items-center justify-center">
            <span className="text-xs font-semibold text-text-secondary">U</span>
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium text-text-primary">Dev User</span>
            <span className="text-xs text-text-muted">Pro Plan</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
