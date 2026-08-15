"use client";

interface AnalyticsHeaderProps {
  isLive: boolean;
  lastUpdated?: Date;
}

export function AnalyticsHeader({ isLive, lastUpdated }: AnalyticsHeaderProps) {
  const formattedTime = lastUpdated?.toLocaleTimeString() || "";

  return (
    <div className="bg-black text-white py-12 px-8 mb-0">
      <div className="max-w-7xl mx-auto">
        {/* Eyebrow */}
        <div className="font-mono text-xs uppercase tracking-wider text-gray-400 mb-2">
          Kisan Mitra / Analytics
        </div>

        {/* Main Heading */}
        <div className="flex items-start justify-between gap-8">
          <div className="flex-1">
            <h1 className="text-5xl font-medium tracking-tight mb-3" style={{ letterSpacing: "-0.02em" }}>
              Kisan Mitra Analytics
            </h1>
            <p className="text-lg text-gray-300 max-w-2xl leading-relaxed">
              Real-time performance across voice calls, tasks, tools, escalation and agent behavior.
            </p>
          </div>

          {/* Live Status Indicator */}
          <div className="flex items-center gap-2 pt-2">
            {isLive && (
              <>
                <span className="inline-block w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
                <span className="text-sm font-mono text-gray-300">LIVE</span>
              </>
            )}
            {lastUpdated && (
              <span className="text-xs font-mono text-gray-500 ml-4">
                Last updated: {formattedTime}
              </span>
            )}
          </div>
        </div>

        {/* Accent Line */}
        <div className="mt-8 h-1 w-20 bg-gradient-to-r from-orange-500 via-pink-500 to-purple-400"></div>
      </div>
    </div>
  );
}
