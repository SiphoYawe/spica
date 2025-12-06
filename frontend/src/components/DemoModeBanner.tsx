/**
 * Demo Mode Banner Component
 * Displays a prominent banner when the application is running in demo mode
 */

import { ExternalLink, AlertTriangle } from 'lucide-react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { cn } from '@/lib/utils';

interface DemoModeBannerProps {
  className?: string;
}

export default function DemoModeBanner({ className }: DemoModeBannerProps) {
  const FAUCET_URL = 'https://neoxwish.ngd.network/';

  return (
    <Alert
      variant="default"
      className={cn(
        "sticky top-0 z-50 rounded-none border-x-0 border-t-0",
        "border-b-2 border-amber-500/50",
        "bg-gradient-to-r from-amber-500/20 via-orange-500/20 to-amber-500/20",
        "shadow-lg shadow-amber-500/10",
        className
      )}
    >
      <AlertTriangle className="h-5 w-5 text-amber-400" />
      <AlertDescription className="flex flex-col items-center justify-between gap-3 sm:flex-row">
        <div className="flex flex-col items-center gap-2 text-center sm:flex-row sm:text-left">
          <span className="font-semibold uppercase tracking-wide text-amber-200">
            Testnet Demo Mode
          </span>
          <span className="hidden text-amber-300/60 sm:inline">•</span>
          <span className="text-sm text-amber-300/90">
            Transactions use pre-funded demo wallet
          </span>
        </div>
        <a
          href={FAUCET_URL}
          target="_blank"
          rel="noopener noreferrer"
          className={cn(
            "inline-flex items-center gap-1.5 rounded-md border border-amber-400/30",
            "bg-amber-500/10 px-3 py-1.5 text-sm font-medium text-amber-200",
            "transition-all duration-200",
            "hover:border-amber-400/60 hover:bg-amber-500/20 hover:text-amber-100",
            "focus:outline-none focus:ring-2 focus:ring-amber-400/50"
          )}
        >
          <span>Get Testnet Tokens</span>
          <ExternalLink className="h-3.5 w-3.5" />
        </a>
      </AlertDescription>
    </Alert>
  );
}
