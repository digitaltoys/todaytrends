// 트윗 데이터 타입 정의
export interface Tweet {
  _id: string;
  _rev?: string;
  platform: string;
  url: string | null;
  text_content: string;
  author_id: string;
  author_name: string;
  author_username: string;
  author_profile_image_url: string | null;
  created_at: string;
  collected_at: string;
  media: MediaItem[];
  hashtags: string[];
  mentions: string[];
  engagement_metrics: EngagementMetrics;
  location: Location | null;
  language: string;
  is_sensitive_content: boolean;
  content_categories: string[];  // 새로 추가: 콘텐츠 카테고리
  raw_data: any;
}

export interface MediaItem {
  type: string;
  url: string | null;
  thumbnail_url: string | null;
}

export interface EngagementMetrics {
  likes_count: number;
  comments_count: number;
  shares_count: number;
  views_count: number;
  quote_count?: number;
}

export interface Location {
  name: string;
  coordinates: {
    latitude: number;
    longitude: number;
  };
}

// CouchDB 응답 타입
export interface CouchDBResponse {
  total_rows: number;
  offset: number;
  rows: CouchDBRow[];
}

export interface CouchDBRow {
  id: string;
  key: string;
  value: any;
  doc?: Tweet;
}

// 대시보드 상태 타입
export interface DashboardState {
  tweets: Tweet[];
  loading: boolean;
  error: string | null;
  totalCount: number;
  lastUpdated: string | null;
}