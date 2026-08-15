"use client";

interface ErrorStateProps {
  title: string;
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ title, message, onRetry }: ErrorStateProps) {
  return (
    <div className="bg-orange-50 border border-orange-200 rounded-sm p-8 max-w-2xl mx-auto my-8">
      <div className="text-center">
        <h3 className="font-mono text-xs uppercase tracking-wider text-orange-700 mb-2">
          ⚠ {title}
        </h3>
        <p className="text-sm text-orange-900 mb-4">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="px-4 py-2 bg-black text-white font-mono text-xs uppercase tracking-wider hover:bg-gray-900 transition"
            style={{ borderRadius: "4px" }}
          >
            ↻ RETRY
          </button>
        )}
      </div>
    </div>
  );
}
