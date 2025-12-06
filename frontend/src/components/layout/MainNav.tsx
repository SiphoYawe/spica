"use client";

import { useMemo } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { PlusCircle, Activity, History } from "lucide-react";
import type { LucideIcon } from "lucide-react";

interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

const navItems: NavItem[] = [
  { label: "Create", href: "/", icon: PlusCircle },
  { label: "Active", href: "/active", icon: Activity },
  { label: "History", href: "/history", icon: History },
];

// Constants for indicator positioning
const NAV_ITEM_COUNT = navItems.length;
const ITEM_WIDTH_PERCENTAGE = 100 / NAV_ITEM_COUNT;
const INDICATOR_OFFSET_PERCENT = 0.5;
const INDICATOR_PADDING_PX = 4;
const TRANSFORM_OFFSET_PX = 2;

export function MainNav() {
  const pathname = usePathname();

  // Memoize active tab calculation
  const activeTab = useMemo((): string => {
    if (pathname === "/") return "/";
    // Workflow detail pages belong to Active section
    if (pathname.startsWith("/active") || pathname.match(/^\/workflows\/[^/]+$/)) {
      return "/active";
    }
    if (pathname.startsWith("/history")) return "/history";
    return "/";
  }, [pathname]);

  // Memoize active index calculation
  const activeIndex = useMemo(
    () => navItems.findIndex((item) => item.href === activeTab),
    [activeTab]
  );

  // Memoize indicator style to prevent recalculation
  const indicatorStyle = useMemo(
    () => ({
      left: `${activeIndex * ITEM_WIDTH_PERCENTAGE + INDICATOR_OFFSET_PERCENT}%`,
      width: `calc(${ITEM_WIDTH_PERCENTAGE}% - ${INDICATOR_PADDING_PX}px)`,
      transform: `translateX(${activeIndex * TRANSFORM_OFFSET_PX}px)`,
    }),
    [activeIndex]
  );

  return (
    <nav
      role="navigation"
      aria-label="Main navigation"
      className="relative flex items-center gap-1 px-1 py-1 bg-background/50 backdrop-blur-sm rounded-lg border border-border/50"
    >
      {/* Animated background indicator */}
      <div
        aria-hidden="true"
        className="absolute inset-y-1 rounded-md bg-spica/10 border border-spica/30 transition-all duration-300 ease-out"
        style={indicatorStyle}
      />

      {navItems.map((item) => {
        const isActive = activeTab === item.href;
        const Icon = item.icon;

        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              "relative flex items-center justify-center gap-2 px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-200 z-10",
              "hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-spica focus-visible:ring-offset-2 focus-visible:ring-offset-background",
              isActive
                ? "text-spica"
                : "text-muted-foreground hover:text-foreground/80"
            )}
          >
            <Icon
              aria-hidden="true"
              className={cn(
                "h-4 w-4 transition-all duration-200",
                isActive && "drop-shadow-[0_0_6px_rgba(0,255,72,0.6)]"
              )}
            />
            <span className="hidden sm:inline">{item.label}</span>
            <span className="sr-only sm:hidden">{item.label}</span>

            {/* Active indicator line */}
            {isActive && (
              <span
                aria-hidden="true"
                className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-spica rounded-full shadow-[0_0_8px_rgba(0,255,72,0.8)]"
              />
            )}
          </Link>
        );
      })}
    </nav>
  );
}
