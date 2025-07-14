interface ViewStatusProps {
  viewMode: 'recent' | 'hashtag' | 'category' | '24hours';
  searchTerm: string;
  selectedCategory: string;
}

export function ViewStatus({ viewMode, searchTerm, selectedCategory }: ViewStatusProps) {
  return (
    <div className="mb-4">
      {viewMode === 'recent' && (
        <p className="text-gray-600">📱 최근 수집된 트윗을 표시하고 있습니다</p>
      )}
      {viewMode === 'hashtag' && (
        <p className="text-gray-600">🔍 '{searchTerm}' 해시태그 검색 결과</p>
      )}
      {viewMode === 'category' && (
        <p className="text-gray-600">🏷️ '{selectedCategory}' 카테고리 필터 결과</p>
      )}
      {viewMode === '24hours' && (
        <p className="text-gray-600">⏰ 최근 24시간 동안 수집된 트윗</p>
      )}
    </div>
  );
}