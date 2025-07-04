import type { Tweet } from '../types';
import { useDashboardStore } from '../store/useDashboardStore';
import { useState } from 'react';

interface TweetCardProps {
  tweet: Tweet;
}

export function TweetCard({ tweet }: TweetCardProps) {
  const { deleteTweet } = useDashboardStore();
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    if (confirm('이 트윗을 삭제하시겠습니까?')) {
      setIsDeleting(true);
      try {
        await deleteTweet(tweet._id);
      } catch (error) {
        console.error('삭제 실패:', error);
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4 hover:shadow-lg transition-shadow relative">
      {/* 사용자 정보 */}
      <div className="flex items-center mb-3">
        {tweet.author_profile_image_url && (
          <img 
            src={tweet.author_profile_image_url} 
            alt={tweet.author_name}
            className="w-10 h-10 rounded-full mr-3"
          />
        )}
        <div className="flex-1 pr-12">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900">{tweet.author_name}</h3>
          </div>
          <div className="flex items-center gap-2">
            <p className="text-sm text-gray-500">@{tweet.author_username}</p>
            <span className="inline-block bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-medium">
              {tweet.platform}
            </span>
          </div>
        </div>
      </div>

      {/* 삭제 버튼 */}
      <button
        onClick={handleDelete}
        disabled={isDeleting}
        className="absolute top-4 right-4 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        title="트윗 삭제"
      >
        {isDeleting ? (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
        ) : (
          <span className="text-sm font-bold">×</span>
        )}
      </button>

      {/* 트윗 내용 */}
      <div className="mb-4">
        <p className="text-gray-800 leading-relaxed mb-3">{tweet.text_content}</p>
        
        {/* 카테고리 */}
        {tweet.content_categories && tweet.content_categories.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {tweet.content_categories.map((category: string, index: number) => {
              const categoryConfig = {
                psychology: { label: '🧠 심리테스트', color: 'bg-purple-100 text-purple-800' },
                game: { label: '🎮 게임', color: 'bg-green-100 text-green-800' },
                meme: { label: '🎭 밈/유머', color: 'bg-yellow-100 text-yellow-800' },
                trend: { label: '📈 트렌드', color: 'bg-pink-100 text-pink-800' },
                general: { label: '📝 일반', color: 'bg-gray-100 text-gray-800' }
              };
              const config = categoryConfig[category as keyof typeof categoryConfig] || categoryConfig.general;
              
              return (
                <span 
                  key={index}
                  className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${config.color}`}
                >
                  {config.label}
                </span>
              );
            })}
          </div>
        )}

        {/* 해시태그 */}
        {tweet.hashtags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {tweet.hashtags.slice(0, 5).map((hashtag, index) => (
              <span 
                key={index}
                className="inline-block bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs"
              >
                #{hashtag}
              </span>
            ))}
            {tweet.hashtags.length > 5 && (
              <span className="text-xs text-gray-500">+{tweet.hashtags.length - 5} more</span>
            )}
          </div>
        )}

        {/* 미디어 */}
        {tweet.media.length > 0 && (
          <div className="grid grid-cols-2 gap-2 mb-3">
            {tweet.media.slice(0, 4).map((media, index) => (
              <div key={index} className="relative">
                {media.thumbnail_url || media.url ? (
                  <img 
                    src={media.thumbnail_url || media.url || ''} 
                    alt="미디어"
                    className="w-full h-32 object-cover rounded"
                  />
                ) : (
                  <div className="w-full h-32 bg-gray-200 rounded flex items-center justify-center">
                    <span className="text-gray-500 text-sm">{media.type}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 참여 지표 */}
      <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
        <div className="flex space-x-4">
          <span>❤️ {formatNumber(tweet.engagement_metrics.likes_count)}</span>
          <span>💬 {formatNumber(tweet.engagement_metrics.comments_count)}</span>
          <span>🔄 {formatNumber(tweet.engagement_metrics.shares_count)}</span>
          {tweet.engagement_metrics.views_count > 0 && (
            <span>👁️ {formatNumber(tweet.engagement_metrics.views_count)}</span>
          )}
        </div>
        <div className="text-xs">
          {tweet.language && <span className="mr-2">🌐 {tweet.language}</span>}
          {tweet.is_sensitive_content && <span className="text-red-500">⚠️</span>}
        </div>
      </div>

      {/* 타임스탬프와 링크 */}
      <div className="flex items-center justify-between text-xs text-gray-400 pt-3 border-t">
        <div>
          <div>생성: {formatDate(tweet.created_at)}</div>
          <div>수집: {formatDate(tweet.collected_at)}</div>
        </div>
        {tweet.url && (
          <a 
            href={tweet.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-500 hover:text-blue-700 underline"
          >
            원본 보기 →
          </a>
        )}
      </div>
    </div>
  );
}