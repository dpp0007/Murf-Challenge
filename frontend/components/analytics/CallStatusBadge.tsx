"use client";

interface CallStatusBadgeProps {
  outcome: string;
  compact?: boolean;
}

export function CallStatusBadge({ outcome, compact = false }: CallStatusBadgeProps) {
  const statusConfig = {
    SUCCESS: {
      bgColor: "bg-cyan-50",
      textColor: "text-cyan-700",
      borderColor: "border-cyan-200",
      icon: "✓",
      label: "SUCCESS",
    },
    FAILED: {
      bgColor: "bg-orange-50",
      textColor: "text-orange-700",
      borderColor: "border-orange-200",
      icon: "✗",
      label: "FAILED",
    },
    PENDING: {
      bgColor: "bg-gray-50",
      textColor: "text-gray-700",
      borderColor: "border-gray-200",
      icon: "●",
      label: "PENDING",
    },
  };

  const config = statusConfig[outcome as keyof typeof statusConfig] || statusConfig.PENDING;

  if (compact) {
    return (
      <span
        className={`${config.textColor} font-mono text-xs`}
      >
        {config.icon} {outcome}
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 ${config.bgColor} ${config.textColor} border ${config.borderColor} font-mono text-xs uppercase tracking-wider`}
      style={{ borderRadius: "4px" }}
    >
      {config.icon}
      <span>{outcome}</span>
    </span>
  );
}
