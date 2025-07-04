import { useEffect, useState } from 'react';
import { useDashboardStore } from '../store/useDashboardStore';
import { KeywordStats } from './KeywordStats';
import { DashboardHeader } from './sections/DashboardHeader';
import { TabNavigation } from './sections/TabNavigation';
import { TweetContent } from './sections/TweetContent';
import { Layout, HeaderSection, ContentSection, Stack } from './layout';

export function Dashboard() {
  const {
    tweets,
    loading,
    error,
    totalCount,
    lastUpdated,
    fetchRecentTweets,
    searchByHashtag,
    clearError,
    refreshData
  } = useDashboardStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'recent' | 'hashtag' | 'category'>('recent');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'tweets' | 'keywords'>('keywords');

  useEffect(() => {
    fetchRecentTweets();
  }, [fetchRecentTweets]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchTerm.trim()) {
      setViewMode('hashtag');
      searchByHashtag(searchTerm.trim());
    }
  };

  const handleViewRecent = () => {
    setViewMode('recent');
    setSearchTerm('');
    setSelectedCategory('');
    fetchRecentTweets();
  };

  const handleCategoryFilter = (category: string) => {
    setViewMode('category');
    setSelectedCategory(category);
    setSearchTerm('');
    // 카테고리별 필터링은 클라이언트 사이드에서 처리
    fetchRecentTweets();
  };

  return (
    <Layout data-name="dashboard-layout">
      {/* 헤더 */}
      <HeaderSection data-name="header-section">
        <Stack spacing="lg" data-name="header-stack">
          <DashboardHeader
            lastUpdated={lastUpdated}
            loading={loading}
            refreshData={refreshData}
          />

          {/* 탭 네비게이션 */}
          <TabNavigation 
            activeTab={activeTab}
            setActiveTab={setActiveTab}
          />
        </Stack>
      </HeaderSection>

      {/* 메인 콘텐츠 */}
      <ContentSection data-name="dashboard-content">
        {/* 키워드 통계 탭 */}
        {activeTab === 'keywords' && <KeywordStats />}

        {/* 트윗 피드 탭 */}
        {activeTab === 'tweets' && (
          <TweetContent
            loading={loading}
            error={error}
            tweets={tweets}
            viewMode={viewMode}
            selectedCategory={selectedCategory}
            totalCount={totalCount}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            clearError={clearError}
            onViewRecent={handleViewRecent}
            onSearch={handleSearch}
            onCategoryFilter={handleCategoryFilter}
          />
        )}
      </ContentSection>
    </Layout>
  );
}