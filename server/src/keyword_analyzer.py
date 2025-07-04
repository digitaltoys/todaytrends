# src/keyword_analyzer.py

import re
from collections import Counter
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class KeywordAnalyzer:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        # 제외할 불용어들
        self.stopwords = {
            '이', '그', '저', '것', '수', '있', '하', '되', '같', '등', '더', '또', '및',
            '그리고', '하지만', '그러나', '따라서', '그래서', '때문에', '위해', '통해',
            '에서', '에게', '에대해', '에대한', '에관해', '에관한', '으로', '로',
            '이다', '있다', '없다', '한다', '된다', '안다', '모르다', '같다', '다르다',
            '많다', '적다', '크다', '작다', '좋다', '나쁘다', '새롭다', '오래되다',
            '너무', '아주', '정말', '매우', '조금', '많이', '자주', '가끔', '항상',
            '결국', '처음', '마지막', '다시', '또다시', '계속', '항상', '절대',
            '사실', '정말', '진짜', '거짓', '가짜', '완전', '전혀', '별로',
            'RT', 'https', 'http', 'www', 'com', 'co', 'kr', 'net', 'org'
        }
        
    def extract_keywords_from_tweets(self, tweets, days_back=7):
        """
        트윗 데이터에서 키워드를 추출하고 빈도를 분석합니다.
        """
        logger.info(f"키워드 분석 시작: {len(tweets)}개 트윗 대상")
        
        # 최근 n일 이내 트윗 필터링
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        recent_tweets = []
        
        for tweet in tweets:
            collected_at = tweet.get('collected_at', '')
            if collected_at:
                try:
                    # Z를 +00:00으로 변경하여 ISO 형식 맞춤
                    if collected_at.endswith('Z'):
                        collected_at = collected_at[:-1] + '+00:00'
                    tweet_date = datetime.fromisoformat(collected_at)
                    if tweet_date > cutoff_date:
                        recent_tweets.append(tweet)
                except:
                    # 날짜 파싱 실패 시 최근 트윗으로 간주
                    recent_tweets.append(tweet)
        
        logger.info(f"최근 {days_back}일 이내 트윗: {len(recent_tweets)}개")
        
        # 키워드 추출
        all_keywords = []
        hashtag_counter = Counter()
        mention_counter = Counter()
        
        for tweet in recent_tweets:
            # 텍스트에서 키워드 추출
            text_keywords = self._extract_keywords_from_text(tweet.get('text_content', ''))
            all_keywords.extend(text_keywords)
            
            # 해시태그 분석
            hashtags = tweet.get('hashtags', [])
            for hashtag in hashtags:
                hashtag_counter[hashtag] += 1
                
            # 멘션 분석
            mentions = tweet.get('mentions', [])
            for mention in mentions:
                mention_counter[mention] += 1
        
        # 키워드 빈도 분석
        keyword_counter = Counter(all_keywords)
        
        # 결과 정리
        analysis_result = {
            'total_tweets': len(tweets),
            'recent_tweets': len(recent_tweets),
            'analysis_date': datetime.now().isoformat(),
            'days_analyzed': days_back,
            'top_keywords': keyword_counter.most_common(50),
            'top_hashtags': hashtag_counter.most_common(20),
            'top_mentions': mention_counter.most_common(10),
            'keyword_trends': self._analyze_keyword_trends(recent_tweets)
        }
        
        logger.info(f"키워드 분석 완료: 상위 키워드 {len(analysis_result['top_keywords'])}개 추출")
        return analysis_result
    
    def _extract_keywords_from_text(self, text):
        """
        텍스트에서 의미있는 키워드를 추출합니다.
        """
        if not text:
            return []
            
        # 특수문자 제거, 공백으로 분리
        text = re.sub(r'[^\w\s가-힣]', ' ', text)
        words = text.split()
        
        # 키워드 필터링
        keywords = []
        for word in words:
            word = word.strip().lower()
            if (len(word) >= 2 and 
                word not in self.stopwords and 
                not word.isdigit() and
                not re.match(r'^[a-zA-Z]{1,2}$', word)):  # 1-2글자 영어 제외
                keywords.append(word)
        
        return keywords
    
    def _analyze_keyword_trends(self, tweets):
        """
        키워드의 트렌드를 분석합니다 (시간대별, 카테고리별).
        """
        trends = {
            'categories': {},
            'hourly': {},
            'engagement': {}
        }
        
        for tweet in tweets:
            # 카테고리별 키워드 분석
            categories = tweet.get('content_categories', ['general'])
            for category in categories:
                if category not in trends['categories']:
                    trends['categories'][category] = Counter()
                
                keywords = self._extract_keywords_from_text(tweet.get('text_content', ''))
                for keyword in keywords:
                    trends['categories'][category][keyword] += 1
            
            # 시간대별 키워드 분석
            created_at = tweet.get('created_at', '')
            if created_at:
                try:
                    hour = datetime.fromisoformat(created_at.replace('Z', '+00:00')).hour
                    if hour not in trends['hourly']:
                        trends['hourly'][hour] = Counter()
                    
                    keywords = self._extract_keywords_from_text(tweet.get('text_content', ''))
                    for keyword in keywords:
                        trends['hourly'][hour][keyword] += 1
                except:
                    pass
            
            # 참여도 기반 키워드 분석
            engagement = tweet.get('engagement_metrics', {})
            total_engagement = (
                engagement.get('likes_count', 0) + 
                engagement.get('comments_count', 0) + 
                engagement.get('shares_count', 0)
            )
            
            keywords = self._extract_keywords_from_text(tweet.get('text_content', ''))
            for keyword in keywords:
                if keyword not in trends['engagement']:
                    trends['engagement'][keyword] = {'total': 0, 'count': 0}
                trends['engagement'][keyword]['total'] += total_engagement
                trends['engagement'][keyword]['count'] += 1
        
        # 참여도 평균 계산
        for keyword in trends['engagement']:
            if trends['engagement'][keyword]['count'] > 0:
                trends['engagement'][keyword]['avg'] = (
                    trends['engagement'][keyword]['total'] / 
                    trends['engagement'][keyword]['count']
                )
        
        return trends
    
    def save_analysis_to_db(self, analysis_result):
        """
        분석 결과를 CouchDB에 저장합니다.
        """
        doc_id = f"keyword_analysis:{analysis_result['analysis_date']}"
        
        analysis_doc = {
            '_id': doc_id,
            'type': 'keyword_analysis',
            **analysis_result
        }
        
        try:
            success = self.db_handler.save_doc(analysis_doc, doc_id)
            if success:
                logger.info(f"키워드 분석 결과 저장 성공: {doc_id}")
                return True
            else:
                logger.warning(f"키워드 분석 결과 저장 실패: {doc_id}")
                return False
        except Exception as e:
            logger.error(f"키워드 분석 결과 저장 중 오류: {e}")
            return False
    
    def get_recent_analysis(self, days_back=1):
        """
        최근 키워드 분석 결과를 가져옵니다.
        """
        try:
            # 모든 문서 가져오기
            all_docs = self.db_handler.get_all_documents()
            
            # 키워드 분석 문서 필터링
            analysis_docs = [
                doc for doc in all_docs 
                if doc.get('type') == 'keyword_analysis'
            ]
            
            # 최근 문서 필터링
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_analysis = []
            
            for doc in analysis_docs:
                try:
                    analysis_date = datetime.fromisoformat(doc.get('analysis_date', ''))
                    if analysis_date > cutoff_date:
                        recent_analysis.append(doc)
                except:
                    continue
            
            # 날짜순 정렬
            recent_analysis.sort(key=lambda x: x.get('analysis_date', ''), reverse=True)
            
            return recent_analysis
        except Exception as e:
            logger.error(f"최근 키워드 분석 결과 조회 중 오류: {e}")
            return []