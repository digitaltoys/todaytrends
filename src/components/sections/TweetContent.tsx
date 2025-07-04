import type { Tweet } from '../../types';
import { TweetCard } from '../TweetCard';
import { StatisticsCards } from './StatisticsCards';
import { SearchAndFilters } from './SearchAndFilters';
import { ViewStatus } from './ViewStatus';
import { Stack } from '../layout';

interface TweetContentProps {
  loading: boolean;
  error: string | null;
  tweets: Tweet[];
  viewMode: 'recent' | 'hashtag' | 'category';
  selectedCategory: string;
  totalCount: number;
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  clearError: () => void;
  onViewRecent: () => void;
  onSearch: (e: React.FormEvent) => void;
  onCategoryFilter: (category: string) => void;
}

export function TweetContent({
  loading,
  error,
  tweets,
  viewMode,
  selectedCategory,
  totalCount,
  searchTerm,
  setSearchTerm,
  clearError,
  onViewRecent,
  onSearch,
  onCategoryFilter
}: TweetContentProps) {
  return (
    <Stack spacing="lg" data-name="tweet-content">
      {/* 통계 카드 */}
      <StatisticsCards 
        totalCount={totalCount}
        tweetsLength={tweets.length}
      />

      {/* 검색 및 필터 */}
      <SearchAndFilters
        searchTerm={searchTerm}
        setSearchTerm={setSearchTerm}
        viewMode={viewMode}
        selectedCategory={selectedCategory}
        loading={loading}
        tweets={tweets}
        onSearch={onSearch}
        onViewRecent={onViewRecent}
        onCategoryFilter={onCategoryFilter}
      />

      {/* 현재 보기 상태 */}
      <ViewStatus
        viewMode={viewMode}
        searchTerm={searchTerm}
        selectedCategory={selectedCategory}
      />

      {/* 트윗 콘텐츠 */}
      <div data-name="tweet-list-container">
        {renderTweetContent()}
      </div>
    </Stack>
  );

  function renderTweetContent() {
    // 에러 메시지
    if (error) {
      return (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6 flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button onClick={clearError} className="text-red-500 hover:text-red-700">
            ✕
          </button>
        </div>
      );
    }

    // 로딩 상태
    if (loading) {
      return (
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-600">데이터를 불러오는 중...</p>
        </div>
      );
    }

    // 트윗 리스트
    if (tweets.length > 0) {
      const filteredTweets = tweets.filter((tweet) => {
        if (viewMode === 'category' && selectedCategory) {
          return (tweet as any).content_categories?.includes(selectedCategory);
        }
        return true;
      });

      if (filteredTweets.length > 0) {
        return (
          <div className="space-y-6">
            {filteredTweets.map((tweet) => (
              <TweetCard key={tweet._id} tweet={tweet} />
            ))}
          </div>
        );
      }

      // 필터링된 결과가 없을 때
      return (
        <div className="text-center py-12">
          <div className="text-6xl mb-4">🔍</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            선택한 카테고리에 해당하는 트윗이 없습니다
          </h3>
          <p className="text-gray-500 mb-4">다른 카테고리를 선택하거나 전체 트윗을 확인해보세요</p>
          <button
            onClick={onViewRecent}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            전체 트윗 보기
          </button>
        </div>
      );
    }

    // 데이터 없음
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📭</div>
        <h3 className="text-xl font-semibold text-gray-700 mb-2">
          {viewMode === 'recent' ? '수집된 데이터가 없습니다' : '검색 결과가 없습니다'}
        </h3>
        <p className="text-gray-500 mb-4">
          {viewMode === 'recent' 
            ? '데이터 수집기를 실행하여 트윗을 수집해보세요'
            : '다른 해시태그로 검색해보세요'
          }
        </p>
        {viewMode === 'hashtag' && (
          <button
            onClick={onViewRecent}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            최근 트윗 보기
          </button>
        )}
      </div>
    );
  }
}