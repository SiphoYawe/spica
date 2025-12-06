"use client";

import { useEffect } from "react";
import { useUiStore } from "@/stores";
import { apiClient } from "@/api/client";

/**
 * Shared hook for app-level initialization.
 * Handles theme application and backend health checks.
 * Use this in all pages to ensure consistent behavior.
 */
export function useAppInitialization() {
  const { setBackendStatus, setBackendVersion, theme } = useUiStore();

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove("light", "dark");
    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);

  // Health check on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await apiClient.healthCheck();
        if (response.data?.status === "healthy" || response.data?.status === "ok") {
          setBackendStatus("connected");
          const version = (response.data as Record<string, unknown>).version;
          setBackendVersion(typeof version === "string" ? version : "");
        } else {
          setBackendStatus("disconnected");
        }
      } catch {
        setBackendStatus("disconnected");
      }
    };

    checkHealth();

    // Periodic health check every 30s
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [setBackendStatus, setBackendVersion]);
}
