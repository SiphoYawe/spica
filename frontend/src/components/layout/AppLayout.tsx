"use client";

import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores";

interface AppLayoutProps {
  children: React.ReactNode;
  sidebar?: React.ReactNode;
  propertiesPanel?: React.ReactNode;
  header?: React.ReactNode;
}

export function AppLayout({
  children,
  sidebar,
  propertiesPanel,
  header,
}: AppLayoutProps) {
  const { sidebarOpen, propertiesPanelOpen } = useUiStore();

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar */}
      {sidebar && (
        <aside
          className={cn(
            "flex-shrink-0 border-r border-border bg-sidebar transition-all duration-200",
            sidebarOpen ? "w-64" : "w-16"
          )}
        >
          {sidebar}
        </aside>
      )}

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Optional header */}
        {header && (
          <header className="flex-shrink-0 border-b border-border bg-card">
            {header}
          </header>
        )}

        {/* Canvas area */}
        <main className="relative flex-1 overflow-hidden canvas-bg">
          {children}
        </main>
      </div>

      {/* Properties Panel */}
      {propertiesPanel && (
        <aside
          className={cn(
            "flex-shrink-0 border-l border-border bg-card transition-all duration-200 overflow-hidden",
            propertiesPanelOpen ? "w-80" : "w-0"
          )}
        >
          <div className="h-full w-80">{propertiesPanel}</div>
        </aside>
      )}
    </div>
  );
}
