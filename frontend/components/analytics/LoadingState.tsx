"use client";

export function LoadingState() {
  return (
    <div className="bg-white p-8 max-w-7xl mx-auto">
      <div className="space-y-6">
        {/* Skeleton KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-gray-100 p-8"
              style={{ borderRadius: "4px", border: "1px solid #EBEBEB" }}
            >
              <div className="h-3 bg-gray-300 rounded w-24 mb-4"></div>
              <div className="h-10 bg-gray-300 rounded w-16"></div>
            </div>
          ))}
        </div>

        {/* Skeleton Table */}
        <div
          className="bg-white border border-gray-200 p-6"
          style={{ borderRadius: "4px" }}
        >
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <div
                key={i}
                className="h-12 bg-gray-100 rounded"
                style={{ borderRadius: "4px" }}
              ></div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes shimmer {
          0% { opacity: 0.6; }
          50% { opacity: 1; }
          100% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
}
