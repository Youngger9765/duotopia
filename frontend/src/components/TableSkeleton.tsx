interface TableSkeletonProps {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}

export default function TableSkeleton({
  rows = 5,
  columns = 6,
  showHeader = true
}: TableSkeletonProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm border animate-pulse">
      {showHeader && (
        <div className="border-b bg-gray-50 px-6 py-3">
          <div className="flex space-x-4">
            {Array.from({ length: columns }).map((_, i) => (
              <div key={i} className="h-4 bg-gray-200 rounded flex-1"></div>
            ))}
          </div>
        </div>
      )}

      <div className="divide-y divide-gray-200">
        {Array.from({ length: rows }).map((_, rowIndex) => (
          <div key={rowIndex} className="px-6 py-4">
            <div className="flex space-x-4">
              {Array.from({ length: columns }).map((_, colIndex) => (
                <div
                  key={colIndex}
                  className="flex-1"
                >
                  <div
                    className="h-4 bg-gray-200 rounded"
                    style={{
                      width: `${Math.random() * 40 + 60}%`,
                      animationDelay: `${(rowIndex * columns + colIndex) * 50}ms`
                    }}
                  ></div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
