"use client";

interface AnalyticsControlsProps {
  timeRange: string;
  onTimeRangeChange: (range: string) => void;
  autoRefresh: boolean;
  onAutoRefreshChange: (enabled: boolean) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export function AnalyticsControls({
  timeRange,
  onTimeRangeChange,
  autoRefresh,
  onAutoRefreshChange,
  onRefresh,
  isRefreshing = false,
}: AnalyticsControlsProps) {
  const timeRangeOptions = [
    { value: "all", label: "ALL TIME" },
    { value: "1d", label: "LAST 24H" },
    { value: "7d", label: "LAST 7D" },
    { value: "30d", label: "LAST 30D" },
  ];

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-4">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-6 flex-wrap">
        {/* Time Range Controls */}
        <div className="flex items-center gap-2">
          <span className="font-mono text-xs uppercase tracking-wider text-gray-600">Time Range</span>
          <div className="flex gap-1">
            {timeRangeOptions.map((option) => (
              <button
                key={option.value}
                onClick={() => onTimeRangeChange(option.value)}
                className={`px-3 py-1.5 font-mono text-xs uppercase tracking-wider transition ${
                  timeRange === option.value
                    ? "bg-black text-white"
                    : "bg-white text-black border border-gray-300 hover:border-gray-400"
                }`}
                style={{ borderRadius: "4px" }}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        {/* Auto-Refresh Control */}
        <label className="flex items-center gap-2 cursor-pointer">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => onAutoRefreshChange(e.target.checked)}
            className="w-4 h-4 rounded"
            style={{ borderRadius: "2px" }}
          />
          <span className="font-mono text-xs uppercase tracking-wider text-gray-600">
            Auto-refresh 15S
          </span>
        </label>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="ml-auto px-4 py-1.5 bg-black text-white font-mono text-xs uppercase tracking-wider hover:bg-gray-900 disabled:opacity-50 transition"
          style={{ borderRadius: "4px" }}
        >
          {isRefreshing ? "↻ UPDATING..." : "↻ REFRESH"}
        </button>
      </div>
    </div>
  );
}
