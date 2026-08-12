"use client"

import * as React from "react"
import { Bell, Search } from "lucide-react"
import { usePathname } from "next/navigation"
import { StatusBadge } from "@/components/ui/StatusBadge"

function getPageTitle(pathname: string) {
  switch (pathname) {
    case "/": return "Dashboard Overview"
    case "/live-trainer": return "Live Trainer"
    case "/yoga": return "Yoga Coach"
    case "/history": return "Workout History"
    case "/video-analysis": return "Video Analysis"
    case "/nutrition": return "Nutrition Targets"
    case "/supplements": return "Supplements Guide"
    default: return "Arogya Vision"
  }
}

export function Header() {
  const pathname = usePathname()
  const title = getPageTitle(pathname)

  const isLive = pathname === "/live-trainer" || pathname === "/yoga"

  return (
    <header className="h-[72px] shrink-0 border-b border-border-subtle bg-surface/50 backdrop-blur-xl flex items-center justify-between px-8 sticky top-0 z-10">
      <div className="flex items-center gap-4">
        <h1 className="text-xl font-semibold text-text-primary">{title}</h1>
        {isLive && <StatusBadge variant="live">LIVE AI ACTIVE</StatusBadge>}
      </div>

      <div className="flex items-center gap-4">
        <div className="relative hidden md:block">
          <Search className="w-4 h-4 text-text-muted absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search..."
            className="glass-input pl-9 pr-4 py-2 text-sm text-text-primary placeholder:text-text-muted w-64"
          />
        </div>
        <button className="w-10 h-10 rounded-full glass-card flex items-center justify-center hover:bg-[rgba(255,255,255,0.08)] transition-colors">
          <Bell className="w-4 h-4 text-text-secondary" />
        </button>
      </div>
    </header>
  )
}
