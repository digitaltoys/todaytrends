import { useEffect, useState } from 'react';
import { couchDBService } from '../services/couchdb';
import { Card, Grid } from './layout';

interface KeywordAnalysis {
  total_tweets: number;
  recent_tweets: number;
  analysis_date: string;
  days_analyzed: number;
  top_keywords: [string, number][];
  top_hashtags: [string, number][];
  top_mentions: [string, number][];
  keyword_trends: {
    categories: Record<string, Record<string, number>>;
    hourly: Record<number, Record<string, number>>;
    engagement: Record<string, { total: number; count: number; avg?: number }>;
  };
}

export function KeywordStats() {
  const [analysis, setAnalysis] = useState<KeywordAnalysis | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<'keywords' | 'hashtags' | 'engagement'>('keywords');

  useEffect(() => {
    fetchKeywordAnalysis();
  }, []);

  const fetchKeywordAnalysis = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await couchDBService.getKeywordAnalysis();
      setAnalysis(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : '키워드 분석 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEngagementKeywords = () => {
    if (!analysis?.keyword_trends.engagement) return [];
    
    return Object.entries(analysis.keyword_trends.engagement)
      .map(([keyword, data]) => ({
        keyword,
        avgEngagement: data.avg || 0,
        count: data.count
      }))
      .filter(item => item.count >= 2) // 최소 2회 이상 언급된 키워드만
      .sort((a, b) => b.avgEngagement - a.avgEngagement)
      .slice(0, 20);
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-12">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <p className="mt-4 text-gray-600">키워드 분석 데이터를 불러오는 중...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">오류 발생</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <button
            onClick={fetchKeywordAnalysis}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center py-12">
          <div className="text-6xl mb-4">📊</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">분석 데이터 없음</h3>
          <p className="text-gray-500">키워드 분석 결과가 없습니다. 데이터 수집 후 분석을 실행해주세요.</p>
        </div>
      </div>
    );
  }

  const engagementKeywords = getEngagementKeywords();

  return (
    <div data-name="keyword-stats">

      {/* 통계 카드 */}
      <Grid cols={3} className="mb-6">
        <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
          <h3 className="text-lg font-semibold mb-2">전체 트윗</h3>
          <p className="text-3xl font-bold">{analysis.total_tweets.toLocaleString()}</p>
        </Card>
        <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
          <h3 className="text-lg font-semibold mb-2">분석 대상</h3>
          <p className="text-3xl font-bold">{analysis.recent_tweets.toLocaleString()}</p>
        </Card>
        <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
          <h3 className="text-lg font-semibold mb-2">상위 키워드</h3>
          <p className="text-3xl font-bold">{analysis.top_keywords.length}</p>
        </Card>
      </Grid>

      {/* 뷰 선택 */}
      <div className="flex space-x-2 mb-6">
        <button
          onClick={() => setSelectedView('keywords')}
          className={`px-4 py-2 rounded-lg font-medium ${
            selectedView === 'keywords'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          인기 키워드
        </button>
        <button
          onClick={() => setSelectedView('hashtags')}
          className={`px-4 py-2 rounded-lg font-medium ${
            selectedView === 'hashtags'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          인기 해시태그
        </button>
        <button
          onClick={() => setSelectedView('engagement')}
          className={`px-4 py-2 rounded-lg font-medium ${
            selectedView === 'engagement'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
          }`}
        >
          참여도 높은 키워드
        </button>
      </div>

      {/* 키워드 리스트 */}
      <div className="space-y-4">
        {selectedView === 'keywords' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">🔥 인기 키워드 Top 20</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysis.top_keywords.slice(0, 20).map(([keyword, count], index) => (
                <div key={keyword} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-bold text-blue-500">#{index + 1}</span>
                    <span className="font-medium">{keyword}</span>
                  </div>
                  <span className="text-sm text-gray-600">{count}회</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedView === 'hashtags' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">#️⃣ 인기 해시태그 Top 20</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysis.top_hashtags.slice(0, 20).map(([hashtag, count], index) => (
                <div key={hashtag} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-bold text-green-500">#{index + 1}</span>
                    <span className="font-medium">#{hashtag}</span>
                  </div>
                  <span className="text-sm text-gray-600">{count}회</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {selectedView === 'engagement' && (
          <div>
            <h3 className="text-lg font-semibold mb-4">⚡ 참여도 높은 키워드 Top 20</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {engagementKeywords.map((item, index) => (
                <div key={item.keyword} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <span className="text-lg font-bold text-purple-500">#{index + 1}</span>
                    <span className="font-medium">{item.keyword}</span>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-600">평균 {Math.round(item.avgEngagement)}회</div>
                    <div className="text-xs text-gray-500">{item.count}회 언급</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* 카테고리별 키워드 */}
      <div className="mt-8">
        <h3 className="text-lg font-semibold mb-4">📂 카테고리별 인기 키워드</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {Object.entries(analysis.keyword_trends.categories).map(([category, keywords]) => {
            const categoryConfig = {
              psychology: { label: '🧠 심리테스트', color: 'border-purple-200 bg-purple-50' },
              game: { label: '🎮 게임', color: 'border-green-200 bg-green-50' },
              meme: { label: '🎭 밈/유머', color: 'border-yellow-200 bg-yellow-50' },
              trend: { label: '📈 트렌드', color: 'border-pink-200 bg-pink-50' },
              general: { label: '📝 일반', color: 'border-gray-200 bg-gray-50' }
            };
            const config = categoryConfig[category as keyof typeof categoryConfig] || categoryConfig.general;
            
            const topKeywords = Object.entries(keywords)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5);

            return (
              <div key={category} className={`p-4 border rounded-lg ${config.color}`}>
                <h4 className="font-semibold mb-3">{config.label}</h4>
                <div className="space-y-2">
                  {topKeywords.map(([keyword, count]) => (
                    <div key={keyword} className="flex justify-between text-sm">
                      <span className="truncate">{keyword}</span>
                      <span className="text-gray-600">{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}