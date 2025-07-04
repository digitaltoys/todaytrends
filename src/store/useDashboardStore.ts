import { create } from 'zustand';
import type { DashboardState } from '../types';
import { couchDBService } from '../services/couchdb';

interface DashboardStore extends DashboardState {
  // Actions
  fetchTweets: () => Promise<void>;
  fetchRecentTweets: () => Promise<void>;
  searchByHashtag: (hashtag: string) => Promise<void>;
  deleteTweet: (tweetId: string) => Promise<void>;
  clearError: () => void;
  refreshData: () => Promise<void>;
}

export const useDashboardStore = create<DashboardStore>((set, get) => ({
  // Initial state
  tweets: [],
  loading: false,
  error: null,
  totalCount: 0,
  lastUpdated: null,

  // Actions
  fetchTweets: async () => {
    set({ loading: true, error: null });
    
    try {
      const { tweets, total } = await couchDBService.getAllTweets(50);
      set({ 
        tweets,
        totalCount: total,
        loading: false,
        lastUpdated: new Date().toISOString()
      });
    } catch (error) {
      set({ 
        loading: false, 
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      });
    }
  },

  fetchRecentTweets: async () => {
    set({ loading: true, error: null });
    
    try {
      const tweets = await couchDBService.getRecentTweets(30);
      set({ 
        tweets,
        totalCount: tweets.length,
        loading: false,
        lastUpdated: new Date().toISOString()
      });
    } catch (error) {
      set({ 
        loading: false, 
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      });
    }
  },

  searchByHashtag: async (hashtag: string) => {
    set({ loading: true, error: null });
    
    try {
      const tweets = await couchDBService.getTweetsByHashtag(hashtag);
      set({ 
        tweets,
        totalCount: tweets.length,
        loading: false,
        lastUpdated: new Date().toISOString()
      });
    } catch (error) {
      set({ 
        loading: false, 
        error: error instanceof Error ? error.message : '알 수 없는 오류가 발생했습니다.'
      });
    }
  },

  deleteTweet: async (tweetId: string) => {
    try {
      await couchDBService.deleteTweet(tweetId);
      
      // 성공하면 로컬 상태에서도 제거
      const { tweets } = get();
      const updatedTweets = tweets.filter(tweet => tweet._id !== tweetId);
      set({ 
        tweets: updatedTweets,
        totalCount: updatedTweets.length 
      });
    } catch (error) {
      set({ 
        error: error instanceof Error ? error.message : '트윗 삭제에 실패했습니다.'
      });
    }
  },

  clearError: () => set({ error: null }),

  refreshData: async () => {
    const { fetchRecentTweets } = get();
    await fetchRecentTweets();
  }
}));