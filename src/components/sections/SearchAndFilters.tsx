import type { Tweet } from '../../types';

interface SearchAndFiltersProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  viewMode: 'recent' | 'hashtag' | 'category';
  selectedCategory: string;
  loading: boolean;
  tweets: Tweet[];
  onSearch: (e: React.FormEvent) => void;
  onViewRecent: () => void;
  onCategoryFilter: (category: string) => void;
}

export function SearchAndFilters({
  searchTerm,
  setSearchTerm,
  viewMode,
  selectedCategory,
  loading,
  tweets,
  onSearch,
  onViewRecent,
  onCategoryFilter
}: SearchAndFiltersProps) {
  // 카테고리별 개수 계산
  const getCategoryCounts = () => {
    const counts = {
      psychology: 0,
      game: 0,
      meme: 0,
      trend: 0
    };

    tweets.forEach(tweet => {
      if ((tweet as any).content_categories) {
        (tweet as any).content_categories.forEach((category: string) => {
          if (category in counts) {
            counts[category as keyof typeof counts]++;
          }
        });
      }
    });

    return counts;
  };

  return (
    <div className="flex flex-col gap-4 mb-6">
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <form onSubmit={onSearch} className="flex gap-2">
            <input
              type="text"
              placeholder="해시태그로 검색... (예: 밈, 유머)"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <button
              type="submit"
              disabled={loading}
              className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
            >
              검색
            </button>
          </form>
        </div>
        <div className="flex gap-2">
          <button
            onClick={onViewRecent}
            className={`px-4 py-2 rounded-lg font-medium ${
              viewMode === 'recent'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            최근 트윗
          </button>
        </div>
      </div>
      
      {/* 카테고리 필터 */}
      <div className="flex flex-wrap gap-2">
        <span className="text-sm text-gray-600 font-medium self-center">카테고리:</span>
        {(() => {
          const categoryCounts = getCategoryCounts();
          return [
            { key: 'psychology', label: '🧠 심리테스트', color: 'bg-purple-100 text-purple-800 hover:bg-purple-200' },
            { key: 'game', label: '🎮 게임', color: 'bg-green-100 text-green-800 hover:bg-green-200' },
            { key: 'meme', label: '🎭 밈/유머', color: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200' },
            { key: 'trend', label: '📈 트렌드', color: 'bg-pink-100 text-pink-800 hover:bg-pink-200' }
          ].map((category) => {
            const count = categoryCounts[category.key as keyof typeof categoryCounts];
            return (
              <button
                key={category.key}
                onClick={() => onCategoryFilter(category.key)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                  viewMode === 'category' && selectedCategory === category.key
                    ? category.color.replace('100', '200')
                    : category.color
                }`}
              >
                {category.label} ({count})
              </button>
            );
          });
        })()}
      </div>
    </div>
  );
}