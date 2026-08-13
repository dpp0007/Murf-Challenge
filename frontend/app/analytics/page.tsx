"use client";

import { useEffect, useState } from "react";

// Use environment variable or fallback to localhost
const BACKEND_URL = typeof window !== 'undefined' 
  ? (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8080')
  : 'http://localhost:8080';

interface AnalyticsSummary {
  total_calls: number;
  successful_calls: number;
  failed_calls: number;
  success_rate: number;
}

interface CallRecord {
  call_id: string;
  channel: string;
  language: string;
  started_at: string;
  duration_seconds: number | null;
  outcome: string;
  outcome_reason: string | null;
  task_type: string;
  tool_used: string | null;
  escalated: boolean;
  failure_type: string | null;
  created_at: string;
}

interface RecentCallsResponse {
  calls: CallRecord[];
  total_count: number;
  query_time_ms: number;
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [recentCalls, setRecentCalls] = useState<CallRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [timeRange, setTimeRange] = useState<string>("all");

  // Fetch analytics data via Next.js API route (avoids CORS)
  const fetchAnalytics = async () => {
    try {
      setError(null);
      console.log(`[Analytics] Fetching data with timeRange: ${timeRange}`);

      // Use Next.js API route as proxy to avoid CORS issues
      console.log(`[Analytics] Fetching summary from /api/analytics/summary`);
      const summaryRes = await fetch(`/api/analytics/summary`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
        },
      });

      if (!summaryRes.ok) {
        console.error(`[Analytics] Summary fetch failed: ${summaryRes.status}`);
        throw new Error(`Failed to fetch summary: ${summaryRes.status} ${summaryRes.statusText}`);
      }

      const summaryData = await summaryRes.json();
      console.log(`[Analytics] Summary received:`, summaryData);

      // Fetch recent calls
      console.log(`[Analytics] Fetching recent calls from /api/analytics/recent`);
      const recentRes = await fetch(`/api/analytics/recent?limit=20`, {
        method: "GET",
        headers: { 
          "Content-Type": "application/json",
        },
      });

      if (!recentRes.ok) {
        console.error(`[Analytics] Recent calls fetch failed: ${recentRes.status}`);
        throw new Error(`Failed to fetch recent calls: ${recentRes.status} ${recentRes.statusText}`);
      }

      const recentData = await recentRes.json();
      console.log(`[Analytics] Recent calls received:`, recentData);

      setSummary(summaryData);
      setRecentCalls(recentData.calls || []);
      console.log(`[Analytics] Data updated successfully`);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load analytics. Make sure the backend is running on port 8080.";
      setError(message);
      console.error("[Analytics] Error:", err);
    } finally {
      setLoading(false);
    }
  };

  // Auto-refresh
  useEffect(() => {
    fetchAnalytics();

    if (!autoRefresh) return;

    const interval = setInterval(fetchAnalytics, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, [autoRefresh, timeRange]);

  // Format duration
  const formatDuration = (seconds: number | null) => {
    if (!seconds) return "-";
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  // Format time
  const formatTime = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString();
    } catch {
      return isoString;
    }
  };

  // Get outcome badge color
  const getOutcomeBadgeColor = (outcome: string) => {
    switch (outcome) {
      case "SUCCESS":
        return "bg-green-100 text-green-800";
      case "FAILED":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  // Get channel badge
  const getChannelBadge = (channel: string) => {
    switch (channel) {
      case "browser":
        return "🌐 Browser";
      case "sip":
        return "📞 SIP";
      default:
        return channel;
    }
  };

  // Get task icon
  const getTaskIcon = (taskType: string) => {
    switch (taskType) {
      case "weather":
        return "🌤️";
      case "mandi":
        return "🛒";
      case "escalation":
        return "⬆️";
      case "crop_advisory":
        return "🌾";
      default:
        return "📞";
    }
  };

  if (loading && !summary) {
    return (
      <div className="container mx-auto p-6">
        <div className="text-center">
          <p className="text-gray-500">Loading analytics...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">📊 Kisan Mitra Analytics</h1>
        <p className="text-gray-600">Real-time call performance and system metrics</p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
          <p className="font-semibold">Error loading analytics:</p>
          <p>{error}</p>
        </div>
      )}

      {/* Controls */}
      <div className="mb-6 flex gap-4 items-center flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium">Time Range:</label>
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-3 py-2 border rounded-lg text-sm"
          >
            <option value="all">All Time</option>
            <option value="1d">Today</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>
        </div>

        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={autoRefresh}
            onChange={(e) => setAutoRefresh(e.target.checked)}
            className="rounded"
          />
          Auto-refresh (every 15s)
        </label>

        <button
          onClick={fetchAnalytics}
          className="ml-auto px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          ↻ Refresh
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {/* Total Calls */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="pb-2">
              <h3 className="text-sm font-medium text-gray-600">Total Calls</h3>
            </div>
            <div>
              <div className="text-3xl font-bold">{summary.total_calls}</div>
              <p className="text-xs text-gray-500 mt-1">All calls (Success + Failed)</p>
            </div>
          </div>

          {/* Successful Calls */}
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="pb-2">
              <h3 className="text-sm font-medium text-green-700">✓ Successful</h3>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600">{summary.successful_calls}</div>
              <p className="text-xs text-green-600 mt-1">Tasks completed successfully</p>
            </div>
          </div>

          {/* Failed Calls */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="pb-2">
              <h3 className="text-sm font-medium text-red-700">✗ Failed</h3>
            </div>
            <div>
              <div className="text-3xl font-bold text-red-600">{summary.failed_calls}</div>
              <p className="text-xs text-red-600 mt-1">Incomplete or failed calls</p>
            </div>
          </div>

          {/* Success Rate */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
            <div className="pb-2">
              <h3 className="text-sm font-medium text-blue-700">📈 Success Rate</h3>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">{summary.success_rate.toFixed(1)}%</div>
              <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${summary.success_rate}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Recent Calls Table */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <div className="mb-4">
          <h2 className="text-lg font-semibold">Recent Calls</h2>
          <p className="text-sm text-gray-500">Last 20 completed calls</p>
        </div>
        
        {recentCalls.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>No calls yet. Start making calls to see analytics here.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b">
                <tr className="text-left text-gray-600">
                  <th className="pb-2 font-semibold">Time</th>
                  <th className="pb-2 font-semibold">Channel</th>
                  <th className="pb-2 font-semibold">Task</th>
                  <th className="pb-2 font-semibold">Duration</th>
                  <th className="pb-2 font-semibold">Outcome</th>
                  <th className="pb-2 font-semibold">Details</th>
                </tr>
              </thead>
              <tbody>
                {recentCalls.map((call) => (
                  <tr key={call.call_id} className="border-b hover:bg-gray-50">
                    <td className="py-3 text-xs text-gray-500">
                      {formatTime(call.created_at)}
                    </td>
                    <td className="py-3 text-xs">
                      <span className="inline-block bg-gray-100 px-2 py-1 rounded">
                        {getChannelBadge(call.channel)}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className="text-lg">{getTaskIcon(call.task_type)}</span>
                      <span className="ml-1 text-xs text-gray-600 capitalize">{call.task_type}</span>
                    </td>
                    <td className="py-3 text-xs font-mono text-gray-600">
                      {formatDuration(call.duration_seconds)}
                    </td>
                    <td className="py-3">
                      <span
                        className={`inline-block px-2 py-1 rounded text-xs font-semibold ${getOutcomeBadgeColor(
                          call.outcome
                        )}`}
                      >
                        {call.outcome === "SUCCESS" ? "✓" : "✗"} {call.outcome}
                      </span>
                    </td>
                    <td className="py-3 text-xs text-gray-600">
                      {call.failure_type && (
                        <span className="text-red-600">{call.failure_type}</span>
                      )}
                      {call.tool_used && (
                        <span className="text-blue-600">{call.tool_used}</span>
                      )}
                      {call.escalated && (
                        <span className="text-purple-600">Escalated</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="mt-6 text-xs text-gray-500 text-center">
        <p>Analytics dashboard • Updates every 15 seconds • Data from SQLite analytics database</p>
      </div>
    </div>
  );
}
