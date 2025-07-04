import { Stack } from '../layout';

interface TabNavigationProps {
  activeTab: 'tweets' | 'keywords';
  setActiveTab: (tab: 'tweets' | 'keywords') => void;
}

export function TabNavigation({ activeTab, setActiveTab }: TabNavigationProps) {
  return (
    <Stack direction="horizontal" spacing="sm" data-name="tab-navigation">
      <button
        onClick={() => setActiveTab('keywords')}
        className={`px-6 py-3 rounded-lg font-medium transition-colors ${
          activeTab === 'keywords'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
        data-name="keywords-tab"
      >
        📊 키워드 통계
      </button>
      <button
        onClick={() => setActiveTab('tweets')}
        className={`px-6 py-3 rounded-lg font-medium transition-colors ${
          activeTab === 'tweets'
            ? 'bg-blue-500 text-white'
            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
        }`}
        data-name="tweets-tab"
      >
        📱 트윗 피드
      </button>
    </Stack>
  );
}