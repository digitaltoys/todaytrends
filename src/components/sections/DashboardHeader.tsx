interface DashboardHeaderProps {
  lastUpdated: string | null;
  loading: boolean;
  refreshData: () => Promise<void>;
}

export function DashboardHeader({ lastUpdated, loading, refreshData }: DashboardHeaderProps) {
  const formatLastUpdated = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="flex items-center justify-between mb-6" data-name="dashboard-header">
      <div data-name="header-title">
        <h1 className="text-3xl font-bold text-gray-900">TodayTrends</h1>
        <p className="text-gray-600 mt-1">실시간 SNS 트렌드 대시보드</p>
      </div>
      <div className="flex items-center space-x-4" data-name="header-actions">
        {lastUpdated && (
          <span className="text-sm text-gray-500" data-name="last-updated">
            마지막 업데이트: {formatLastUpdated(lastUpdated)}
          </span>
        )}
        <button
          onClick={refreshData}
          disabled={loading}
          className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
          data-name="refresh-button"
        >
          <span>🔄</span>
          <span>{loading ? '새로고침 중...' : '새로고침'}</span>
        </button>
      </div>
    </div>
  );
}