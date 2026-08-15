"use client";

import { useEffect, useState } from "react";
import { AnalyticsHeader } from "@/components/analytics/AnalyticsHeader";
import { AnalyticsControls } from "@/components/analytics/AnalyticsControls";
import { KPICard } from "@/components/analytics/KPICard";
import { RecentCallsTable } from "@/components/analytics/RecentCallsTable";
import { CallDetailDrawer } from "@/components/analytics/CallDetailDrawer";
import { ErrorState } from "@/components/analytics/ErrorState";
import { LoadingState } from "@/components/analytics/LoadingState";

// Use environment variable or fallback to localhost
const BACKEND_URL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8080"
    : "http://localhost:8080";

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
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedCall, setSelectedCall] = useState<CallRecord | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch analytics data via Next.js API route (avoids CORS)
  const fetchAnalytics = async () => {
    try {
      setError(null);
      setIsRefreshing(true);
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
        throw new Error(
          `Failed to fetch summary: ${summaryRes.status} ${summaryRes.statusText}`
        );
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
        throw new Error(
          `Failed to fetch recent calls: ${recentRes.status} ${recentRes.statusText}`
        );
      }

      const recentData = await recentRes.json();
      console.log(`[Analytics] Recent calls received:`, recentData);

      setSummary(summaryData);
      setRecentCalls(recentData.calls || []);
      setLastUpdated(new Date());
      console.log(`[Analytics] Data updated successfully`);
    } catch (err) {
      const message =
        err instanceof Error
          ? err.message
          : "Failed to load analytics. Make sure the backend is running on port 8080.";
      setError(message);
      console.error("[Analytics] Error:", err);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  };

  // Auto-refresh
  useEffect(() => {
    fetchAnalytics();

    if (!autoRefresh) return;

    const interval = setInterval(fetchAnalytics, 15000); // Refresh every 15 seconds
    return () => clearInterval(interval);
  }, [autoRefresh, timeRange]);

  if (loading && !summary) {
    return <LoadingState />;
  }

  return (
    <div className="flex flex-col h-screen bg-white">
      {/* Header */}
      <AnalyticsHeader isLive={autoRefresh} lastUpdated={lastUpdated || undefined} />

      {/* Controls */}
      <AnalyticsControls
        timeRange={timeRange}
        onTimeRangeChange={setTimeRange}
        autoRefresh={autoRefresh}
        onAutoRefreshChange={setAutoRefresh}
        onRefresh={fetchAnalytics}
        isRefreshing={isRefreshing}
      />

      {/* Main Content - scrollable */}
      <div className="flex-1 overflow-y-auto bg-white px-8 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Error State */}
          {error && (
            <ErrorState
              title="ANALYTICS UNAVAILABLE"
              message={error}
              onRetry={fetchAnalytics}
            />
          )}

          {/* KPI Cards Section */}
          {summary && (
            <div className="mb-12">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {/* Total Calls */}
                <KPICard
                  label="Total Calls"
                  value={summary.total_calls}
                  supportingText="All calls (success + failed)"
                  indicator="neutral"
                />

                {/* Successful Calls */}
                <KPICard
                  label="Successful"
                  value={summary.successful_calls}
                  supportingText={`${((summary.successful_calls / summary.total_calls) * 100).toFixed(1)}% of calls`}
                  indicator="success"
                />

                {/* Failed Calls */}
                <KPICard
                  label="Failed"
                  value={summary.failed_calls}
                  supportingText={`${((summary.failed_calls / summary.total_calls) * 100).toFixed(1)}% of calls`}
                  indicator="failed"
                />

                {/* Success Rate */}
                <KPICard
                  label="Success Rate"
                  value={`${summary.success_rate.toFixed(1)}%`}
                  progress={summary.success_rate}
                  supportingText="Overall success percentage"
                  indicator="neutral"
                />
              </div>
            </div>
          )}

          {/* Recent Calls Section */}
          <div
            className="bg-white border border-gray-200"
            style={{ borderRadius: "4px" }}
          >
            {/* Section Header */}
            <div className="border-b border-gray-200 px-6 py-4">
              <h2 className="font-mono text-xs uppercase tracking-wider font-semibold text-black mb-1">
                RECENT CALLS
              </h2>
              <p className="font-mono text-xs text-gray-600">
                Latest voice-agent activity
              </p>
            </div>

            {/* Table */}
            <RecentCallsTable
              calls={recentCalls}
              onRowClick={setSelectedCall}
            />
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-gray-200 bg-white px-8 py-4 flex-shrink-0">
        <div className="max-w-7xl mx-auto">
          <p className="font-mono text-xs text-gray-500">
            Analytics dashboard • Real-time monitoring • Data from SQLite analytics database
          </p>
        </div>
      </div>

      {/* Call Detail Drawer */}
      <CallDetailDrawer
        call={selectedCall}
        onClose={() => setSelectedCall(null)}
      />
    </div>
  );
}
