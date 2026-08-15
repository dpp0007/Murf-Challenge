"use client";

import { useState } from "react";

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

interface CallDetailDrawerProps {
  call: CallRecord | null;
  onClose: () => void;
}

function formatDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  if (seconds < 60) return `${seconds} seconds`;
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${minutes} minutes ${secs} seconds`;
}

export function CallDetailDrawer({ call, onClose }: CallDetailDrawerProps) {
  if (!call) return null;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/40 z-40 transition-opacity"
        onClick={onClose}
        style={{ animation: "fadeIn 0.2s ease-out" }}
        role="presentation"
      />

      {/* Drawer */}
      <div
        className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-white shadow-2xl z-50 flex flex-col"
        style={{
          animation: "slideIn 0.3s ease-out",
          borderLeft: "1px solid #EBEBEB",
        }}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between flex-shrink-0">
          <h2 className="font-mono text-sm uppercase tracking-wider font-semibold">
            CALL DETAILS
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none p-1"
            aria-label="Close drawer"
          >
            ×
          </button>
        </div>

        {/* Content - scrollable */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          <div className="space-y-6">
            {/* Call ID */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Call ID
              </label>
              <p className="font-mono text-sm text-gray-900 break-all">{call.call_id}</p>
            </div>

            {/* Timestamp */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Started At
              </label>
              <p className="text-sm text-gray-900">{formatDate(call.created_at)}</p>
            </div>

            {/* Duration */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Duration
              </label>
              <p className="text-sm text-gray-900">{formatDuration(call.duration_seconds)}</p>
            </div>

            {/* Channel */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Channel
              </label>
              <p className="text-sm text-gray-900 capitalize">{call.channel}</p>
            </div>

            {/* Language */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Language
              </label>
              <p className="text-sm text-gray-900">{call.language || "—"}</p>
            </div>

            {/* Task Type */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Task Type
              </label>
              <p className="text-sm text-gray-900 capitalize">{call.task_type || "—"}</p>
            </div>

            {/* Outcome */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Outcome
              </label>
              <p className={`text-sm font-semibold ${call.outcome === "SUCCESS" ? "text-green-700" : "text-red-700"}`}>
                {call.outcome}
              </p>
            </div>

            {/* Outcome Reason */}
            {call.outcome_reason && (
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                  Outcome Reason
                </label>
                <p className="text-sm text-gray-900">{call.outcome_reason}</p>
              </div>
            )}

            {/* Tool Used */}
            {call.tool_used && (
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                  Tool Used
                </label>
                <p className="text-sm text-gray-900 font-mono">{call.tool_used}</p>
              </div>
            )}

            {/* Failure Type */}
            {call.failure_type && (
              <div>
                <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                  Failure Type
                </label>
                <p className="text-sm text-red-700 font-mono">{call.failure_type}</p>
              </div>
            )}

            {/* Escalation Status */}
            <div>
              <label className="block font-mono text-xs uppercase tracking-wider text-gray-600 mb-1">
                Escalation Status
              </label>
              <p className={`text-sm ${call.escalated ? "text-orange-700 font-semibold" : "text-gray-600"}`}>
                {call.escalated ? "ESCALATED" : "NOT ESCALATED"}
              </p>
            </div>
          </div>
        </div>

        <style>{`
          @keyframes fadeIn {
            from {
              opacity: 0;
            }
            to {
              opacity: 1;
            }
          }
          @keyframes slideIn {
            from {
              transform: translateX(100%);
            }
            to {
              transform: translateX(0);
            }
          }
        `}</style>
      </div>
    </>
  );
}
