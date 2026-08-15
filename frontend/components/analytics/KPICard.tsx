"use client";

interface KPICardProps {
  label: string;
  value: string | number;
  supportingText?: string;
  indicator?: "success" | "failed" | "neutral";
  progress?: number;
  trend?: {
    direction: "up" | "down";
    percentage: number;
  };
}

export function KPICard({
  label,
  value,
  supportingText,
  indicator = "neutral",
  progress,
  trend,
}: KPICardProps) {
  const indicatorColor = {
    success: "bg-cyan-100",
    failed: "bg-orange-100",
    neutral: "bg-gray-100",
  }[indicator];

  const indicatorDot = {
    success: "bg-cyan-400",
    failed: "bg-orange-500",
    neutral: "bg-gray-400",
  }[indicator];

  return (
    <div
      className="bg-white border border-gray-200 p-8"
      style={{
        borderRadius: "4px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      {/* Header with Indicator */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <span className={`inline-block w-2 h-2 rounded-full ${indicatorDot}`}></span>
          <h3 className="font-mono text-xs uppercase tracking-wider text-gray-600">{label}</h3>
        </div>
      </div>

      {/* Main Value */}
      <div className="mb-4">
        <div className="text-4xl font-medium tracking-tight mb-2">{value}</div>
        {supportingText && (
          <p className="text-sm text-gray-600">{supportingText}</p>
        )}
      </div>

      {/* Progress Bar (if provided) */}
      {progress !== undefined && (
        <div className="mt-4">
          <div className="w-full h-1 bg-gray-200" style={{ borderRadius: "2px" }}>
            <div
              className="h-1 bg-gradient-to-r from-orange-500 via-pink-500 to-purple-400 transition-all duration-300"
              style={{
                width: `${Math.min(100, Math.max(0, progress))}%`,
                borderRadius: "2px",
              }}
            ></div>
          </div>
          {progress !== undefined && (
            <p className="text-xs text-gray-500 mt-2">{progress.toFixed(1)}%</p>
          )}
        </div>
      )}

      {/* Trend (if provided) */}
      {trend && (
        <div className="mt-3 flex items-center gap-1">
          <span className={`text-xs font-mono ${trend.direction === "up" ? "text-green-600" : "text-red-600"}`}>
            {trend.direction === "up" ? "↑" : "↓"} {trend.percentage}%
          </span>
        </div>
      )}
    </div>
  );
}
