# src/analyze_keywords.py

import os
import logging
from dotenv import load_dotenv
from db_handler import CouchDBHandler
from keyword_analyzer import KeywordAnalyzer

# .env 파일 로드
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    수집된 트윗 데이터에서 키워드를 분석하고 결과를 저장합니다.
    """
    try:
        # 환경변수에서 CouchDB 설정 읽기
        COUCHDB_URL = os.getenv('COUCHDB_URL', 'http://localhost:5984')
        COUCHDB_DB_NAME = os.getenv('COUCHDB_DB_NAME', 'todaytrend')
        COUCHDB_USERNAME = os.getenv('COUCHDB_USERNAME')
        COUCHDB_PASSWORD = os.getenv('COUCHDB_PASSWORD')
        
        logger.info("키워드 분석 스크립트 시작")
        logger.info(f"CouchDB URL: {COUCHDB_URL}")
        logger.info(f"DB 이름: {COUCHDB_DB_NAME}")
        
        # CouchDB 연결
        db_handler = CouchDBHandler(
            COUCHDB_URL, 
            COUCHDB_DB_NAME, 
            username=COUCHDB_USERNAME, 
            password=COUCHDB_PASSWORD
        )
        
        if not db_handler.is_connected():
            logger.error("CouchDB 연결 실패")
            return
        
        # 키워드 분석기 초기화
        analyzer = KeywordAnalyzer(db_handler)
        
        # 모든 트윗 데이터 가져오기
        logger.info("트윗 데이터 가져오는 중...")
        all_docs = db_handler.get_all_documents()
        
        # 트윗 문서만 필터링 (twitter: 접두사를 가진 문서)
        tweets = [
            doc for doc in all_docs 
            if doc.get('_id', '').startswith('twitter:')
        ]
        
        logger.info(f"분석할 트윗 수: {len(tweets)}개")
        
        if not tweets:
            logger.warning("분석할 트윗이 없습니다.")
            return
        
        # 키워드 분석 실행
        logger.info("키워드 분석 시작...")
        analysis_result = analyzer.extract_keywords_from_tweets(tweets, days_back=7)
        
        # 결과 출력
        logger.info("\n=== 키워드 분석 결과 ===")
        logger.info(f"총 트윗 수: {analysis_result['total_tweets']}")
        logger.info(f"분석 대상 트윗 수: {analysis_result['recent_tweets']}")
        logger.info(f"분석 기간: 최근 {analysis_result['days_analyzed']}일")
        
        logger.info("\n--- 상위 키워드 (Top 20) ---")
        for i, (keyword, count) in enumerate(analysis_result['top_keywords'][:20], 1):
            logger.info(f"{i:2d}. {keyword}: {count}회")
        
        logger.info("\n--- 상위 해시태그 (Top 10) ---")
        for i, (hashtag, count) in enumerate(analysis_result['top_hashtags'][:10], 1):
            logger.info(f"{i:2d}. #{hashtag}: {count}회")
        
        logger.info("\n--- 카테고리별 상위 키워드 ---")
        trends = analysis_result['keyword_trends']
        for category, keywords in trends['categories'].items():
            logger.info(f"\n[{category}]")
            for keyword, count in keywords.most_common(5):
                logger.info(f"  {keyword}: {count}회")
        
        # 결과를 DB에 저장
        logger.info("\n키워드 분석 결과를 DB에 저장 중...")
        save_success = analyzer.save_analysis_to_db(analysis_result)
        
        if save_success:
            logger.info("키워드 분석 완료 및 저장 성공!")
        else:
            logger.warning("키워드 분석은 완료되었으나 저장에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"키워드 분석 중 오류 발생: {e}", exc_info=True)

if __name__ == '__main__':
    main()