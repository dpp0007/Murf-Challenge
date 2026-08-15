"use client";

import { CallStatusBadge } from "./CallStatusBadge";
import { ChannelBadge } from "./ChannelBadge";

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

interface RecentCallsTableProps {
  calls: CallRecord[];
  onRowClick?: (call: CallRecord) => void;
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes}m ${secs}s`;
}

function formatTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

function getTaskIcon(taskType: string): string {
  const icons: Record<string, string> = {
    weather: "🌤",
    mandi: "🛒",
    escalation: "⬆",
    crop_advisory: "🌾",
    unknown: "❓",
  };
  return icons[taskType.toLowerCase()] || "●";
}

function getDetailLabel(call: CallRecord): string {
  if (call.failure_type) return call.failure_type;
  if (call.tool_used) return call.tool_used;
  if (call.escalated) return "Escalation";
  return "—";
}

export function RecentCallsTable({ calls, onRowClick }: RecentCallsTableProps) {
  if (calls.length === 0) {
    return (
      <div className="text-center py-12 px-8">
        <p className="text-gray-500 font-mono text-sm uppercase tracking-wider">
          No calls yet. Start making calls to see analytics here.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto max-h-96">
      <table className="w-full min-w-max" style={{ borderCollapse: "collapse" }}>
        <thead>
          <tr
            className="bg-gray-100 border-b border-gray-200 sticky top-0"
            style={{ borderBottom: "1px solid #EBEBEB" }}
          >
            <th
              className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider text-gray-600 font-semibold whitespace-nowrap"
              style={{ textAlign: "left" }}
            >
              TIME
            </th>
            <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider text-gray-600 font-semibold whitespace-nowrap">
              CHANNEL
            </th>
            <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider text-gray-600 font-semibold whitespace-nowrap">
              TASK
            </th>
            <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider text-gray-600 font-semibold whitespace-nowrap">
              DURATION
            </th>
            <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider text-gray-600 font-semibold whitespace-nowrap">
              OUTCOME
            </th>
            <th className="px-6 py-3 text-left font-mono text-xs uppercase tracking-wider text-gray-600 font-semibold whitespace-nowrap">
              DETAILS
            </th>
          </tr>
        </thead>
        <tbody>
          {calls.map((call, index) => (
            <tr
              key={call.call_id}
              className="border-b border-gray-200 hover:bg-gray-50 cursor-pointer transition"
              onClick={() => onRowClick?.(call)}
              style={{
                borderBottom: "1px solid #EBEBEB",
              }}
            >
              <td className="px-6 py-3 text-sm font-mono text-gray-600 whitespace-nowrap">
                {formatTime(call.created_at)}
              </td>
              <td className="px-6 py-3 whitespace-nowrap">
                <ChannelBadge channel={call.channel} />
              </td>
              <td className="px-6 py-3 text-sm whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <span className="text-lg">{getTaskIcon(call.task_type)}</span>
                  <span className="font-mono text-xs uppercase text-gray-700">
                    {call.task_type || "UNKNOWN"}
                  </span>
                </div>
              </td>
              <td className="px-6 py-3 font-mono text-sm text-gray-600 whitespace-nowrap">
                {formatDuration(call.duration_seconds)}
              </td>
              <td className="px-6 py-3 whitespace-nowrap">
                <CallStatusBadge outcome={call.outcome} />
              </td>
              <td className="px-6 py-3 font-mono text-sm text-gray-600 whitespace-nowrap">
                {getDetailLabel(call)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
