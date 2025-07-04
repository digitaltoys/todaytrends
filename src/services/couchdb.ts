import type { Tweet, CouchDBResponse } from '../types';

// CouchDB 설정 - 개발 시에는 Vite 프록시 사용
const COUCHDB_BASE_URL = '/api';
const DATABASE_NAME = import.meta.env.VITE_COUCHDB_DB_NAME || 'todaytrend';

class CouchDBService {
  private baseUrl: string;
  private dbName: string;

  constructor() {
    this.baseUrl = COUCHDB_BASE_URL;
    this.dbName = DATABASE_NAME;
  }

  // 모든 트윗 가져오기
  async getAllTweets(limit = 50, skip = 0): Promise<{ tweets: Tweet[], total: number }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/${this.dbName}/_all_docs?include_docs=true&limit=${limit}&skip=${skip}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: CouchDBResponse = await response.json();
      
      const tweets = data.rows
        .filter(row => row.doc && row.id.startsWith('twitter:'))
        .map(row => row.doc as Tweet);

      return {
        tweets,
        total: data.total_rows
      };
    } catch (error) {
      console.error('CouchDB 연결 오류:', error);
      throw new Error('데이터를 가져오는데 실패했습니다.');
    }
  }

  // 최근 트윗 가져오기 (수집 시간 기준)
  async getRecentTweets(limit = 20): Promise<Tweet[]> {
    try {
      const response = await fetch(
        `${this.baseUrl}/${this.dbName}/_all_docs?include_docs=true&limit=${limit}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: CouchDBResponse = await response.json();
      
      const tweets = data.rows
        .filter(row => row.doc && row.id.startsWith('twitter:'))
        .map(row => row.doc as Tweet)
        .sort((a, b) => new Date(b.collected_at).getTime() - new Date(a.collected_at).getTime());

      return tweets;
    } catch (error) {
      console.error('최근 트윗 가져오기 오류:', error);
      throw new Error('최근 트윗을 가져오는데 실패했습니다.');
    }
  }

  // 데이터베이스 정보 가져오기
  async getDatabaseInfo() {
    try {
      const response = await fetch(`${this.baseUrl}/${this.dbName}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('데이터베이스 정보 가져오기 오류:', error);
      throw new Error('데이터베이스 정보를 가져오는데 실패했습니다.');
    }
  }

  // 해시태그별 트윗 검색
  async getTweetsByHashtag(hashtag: string, limit = 20): Promise<Tweet[]> {
    try {
      const { tweets } = await this.getAllTweets(100); // 더 많은 데이터를 가져와서 필터링
      
      return tweets
        .filter(tweet => 
          tweet.hashtags.some(tag => 
            tag.toLowerCase().includes(hashtag.toLowerCase())
          )
        )
        .slice(0, limit);
    } catch (error) {
      console.error('해시태그 검색 오류:', error);
      throw new Error('해시태그 검색에 실패했습니다.');
    }
  }

  // 트윗 삭제
  async deleteTweet(tweetId: string): Promise<boolean> {
    try {
      // 먼저 문서를 가져와서 _rev 확인
      const response = await fetch(`${this.baseUrl}/${this.dbName}/${tweetId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`트윗을 찾을 수 없습니다: ${response.status}`);
      }

      const tweet = await response.json();

      // 문서 삭제
      const deleteResponse = await fetch(`${this.baseUrl}/${this.dbName}/${tweetId}?rev=${tweet._rev}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!deleteResponse.ok) {
        throw new Error(`삭제 실패: ${deleteResponse.status}`);
      }

      return true;
    } catch (error) {
      console.error('트윗 삭제 오류:', error);
      throw new Error('트윗 삭제에 실패했습니다.');
    }
  }

  // 키워드 분석 결과 가져오기
  async getKeywordAnalysis(): Promise<any> {
    try {
      const response = await fetch(
        `${this.baseUrl}/${this.dbName}/_all_docs?include_docs=true&startkey="keyword_analysis:"&endkey="keyword_analysis:\ufff0"`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: CouchDBResponse = await response.json();
      
      const analyses = data.rows
        .filter(row => row.doc && row.id.startsWith('keyword_analysis:'))
        .map(row => row.doc!)
        .sort((a, b) => new Date((b as any).analysis_date || '').getTime() - new Date((a as any).analysis_date || '').getTime());

      return analyses.length > 0 ? analyses[0] : null;
    } catch (error) {
      console.error('키워드 분석 데이터 가져오기 오류:', error);
      throw new Error('키워드 분석 데이터를 가져오는데 실패했습니다.');
    }
  }
}

export const couchDBService = new CouchDBService();