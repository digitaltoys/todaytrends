# src/collectors/twitter_collector.py

import tweepy
import os
import json
from datetime import datetime
from dotenv import load_dotenv # .env 파일 로드를 위해 추가

# .env 파일 로드
# 이 스크립트(twitter_collector.py)가 server/src/collectors/ 에 위치하고,
# .env 파일이 프로젝트 루트 (server 폴더의 부모)에 있다고 가정합니다.
# 즉, ../../.env 경로가 됩니다.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
else:
    # .env 파일이 현재 작업 디렉토리 또는 기본 경로에 있을 경우를 대비
    load_dotenv()


# src/collectors/twitter_collector.py

import tweepy
# import os # 이미 위에서 import 함
# import json # 이미 위에서 import 함
from datetime import datetime, timezone
import logging

# db_handler.py에서 CouchDBHandler 클래스를 가져옵니다.
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db_handler import CouchDBHandler

# 로거 설정
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TwitterCollector:
    def __init__(self, bearer_token, couchdb_url, couchdb_db_name, couchdb_user=None, couchdb_password=None):
        """
        Twitter API v2 인증 (Bearer Token 사용) 및 초기화
        CouchDB 핸들러 초기화
        """
        self.bearer_token = bearer_token

        try:
            # Tweepy Client for Twitter API v2
            self.client = tweepy.Client(
                bearer_token=self.bearer_token,
                wait_on_rate_limit=True
            )
            # API v1.1 접근을 위한 API 객체 (필요시) - search_tweets는 v1.1에 있음
            # OAuth 1.0a User Context 방식 또는 App-only 방식의 API 키/시크릿 필요
            # 여기서는 우선 v2 클라이언트만 초기화하고, 필요에 따라 v1.1 API 객체도 추가 가능
            # 만약 search_tweets를 계속 사용하려면, 이전과 같이 OAuthHandler 방식 사용 필요
            # 여기서는 API v2의 recent_search를 사용하도록 변경
            logger.info("Twitter API v2 클라이언트 인증 성공 (Bearer Token 방식)")
        except Exception as e:
            logger.error(f"Twitter API v2 클라이언트 인증 실패: {e}")
            raise

        try:
            self.db_handler = CouchDBHandler(couchdb_url, couchdb_db_name, username=couchdb_user, password=couchdb_password)
            if not self.db_handler.is_connected():
                # 연결 실패 시 로깅은 CouchDBHandler 내부에서 이미 수행됨
                raise ConnectionError(f"CouchDB ({couchdb_db_name}) 연결에 실패했습니다. TwitterCollector 초기화 중단.")
            logger.info(f"CouchDB 핸들러 초기화 성공 (DB: {couchdb_db_name})")
        except Exception as e:
            logger.error(f"CouchDB 핸들러 초기화 중 예상치 못한 오류: {e}")
            self.db_handler = None
            raise

    def search_recent_tweets(self, query, max_results=10, lang="ko"):
        """
        주어진 쿼리로 최근 트윗을 검색합니다 (Twitter API v2 사용).
        :param query: 검색할 키워드 또는 해시태그 (예: "#밈", "인기 밈")
        :param max_results: 가져올 트윗 수 (API v2에서는 10~100 사이)
        :param lang: 검색할 언어 (예: "ko"). API v2에서는 쿼리에 lang:ko 형태로 포함 가능
        :return: 검색된 트윗 데이터 리스트 (tweepy.Tweet 객체 리스트)
        """
        if not 10 <= max_results <= 100:
            logger.warning(f"max_results는 10에서 100 사이여야 합니다. 기본값 10으로 조정합니다.")
            max_results = 10

        # API v2의 경우 언어 필터는 쿼리에 직접 포함
        # query_with_lang = f"{query} lang:{lang}" if lang else query
        # tweepy.Client.search_recent_tweets 에서는 query에 lang을 넣지 않고, 별도 파라미터도 없음
        # 대신 tweet_fields 에서 lang 을 요청할 수 있음. 필터링은 직접 해야 함.

        try:
            # 사용 가능한 expansions 및 fields는 Twitter API v2 문서 참고
            # https://developer.twitter.com/en/docs/twitter-api/tweets/search/api-reference/get-tweets-search-recent
            # https://docs.tweepy.org/en/stable/client.html#tweepy.Client.search_recent_tweets
            response = self.client.search_recent_tweets(
                query=query,
                max_results=max_results,
                tweet_fields=[
                    'id', 'text', 'created_at', 'author_id', 'public_metrics',
                    'entities', 'lang', 'possibly_sensitive', 'source', 'geo'
                ],
                expansions=[
                    'author_id', 'attachments.media_keys', 'geo.place_id'
                ],
                media_fields=[
                    'media_key', 'type', 'url', 'preview_image_url', 'public_metrics', 'alt_text'
                ],
                user_fields=[
                    'id', 'name', 'username', 'profile_image_url', 'verified'
                ],
                # place_fields=['full_name', 'geo'] # geo.place_id expansion 시 사용 가능
            )

            tweets = response.data if response.data else []
            includes = response.includes if response.includes else {}

            # users와 media 딕셔너리 생성 시 tweepy 객체의 id와 media_key를 사용해야 함
            users = {user.id: user for user in includes.get("users", [])} if includes.get("users") else {}
            media = {m.media_key: m for m in includes.get("media", [])} if includes.get("media") else {}

            # 각 트윗에 사용자 정보와 미디어 정보를 병합
            enriched_tweets = []
            if tweets:
                for tweet_obj in tweets:
                    tweet_dict = tweet_obj.data.copy()

                    if users and tweet_obj.author_id in users:
                        tweet_dict['author'] = users[tweet_obj.author_id].data.copy()
                    else:
                        # author_id는 있지만 users include에 해당 유저 정보가 없는 경우 대비
                        tweet_dict['author'] = {} # 또는 None 처리 등 정책에 따라 결정

                    tweet_dict['attachments_media'] = []
                    if media and tweet_obj.attachments and 'media_keys' in tweet_obj.attachments:
                        for media_key in tweet_obj.attachments['media_keys']:
                            if media_key in media:
                                tweet_dict['attachments_media'].append(media[media_key].data.copy())
                    enriched_tweets.append(tweet_dict)

            logger.info(f"'{query}' 검색 결과 {len(enriched_tweets)}개 트윗 수집 (API v2)")
            return enriched_tweets
        except tweepy.TweepyException as e:
            logger.error(f"API v2 트윗 검색 중 오류 발생 (쿼리: {query}): {e}")
            return []
        except Exception as e:
            logger.error(f"알 수 없는 오류 발생 (API v2 트윗 검색 중, 쿼리: {query}): {e}", exc_info=True)
            return []

    def _is_meme_content(self, tweet):
        """
        트윗이 밈 관련 콘텐츠인지 판단하는 내부 로직 (개선 필요)
        - 이미지, 비디오, GIF 포함 여부
        - 특정 키워드 (예: "챌린지", "웃긴", "유머") 포함 여부
        - 리트윗/좋아요 수 등
        """
        # 1. 미디어 (이미지, 비디오, GIF) 포함 여부 확인
        if hasattr(tweet, 'extended_entities') and 'media' in tweet.extended_entities:
            for media in tweet.extended_entities['media']:
                if media['type'] in ['photo', 'video', 'animated_gif']:
                    return True

        # 2. 텍스트 내 특정 키워드 확인 (간단한 예시)
        meme_keywords = ["#meme", "#밈", "웃긴", "유머", "챌린지", "ㅋㅋㅋ"]
        text_to_check = ""
        if hasattr(tweet, 'full_text'):
            text_to_check = tweet.full_text.lower()
        elif hasattr(tweet, 'text'): # Retweet의 경우 full_text가 없을 수 있음
             text_to_check = tweet.text.lower()

        if any(keyword in text_to_check for keyword in meme_keywords):
            return True

        # 3. TODO: 리트윗/좋아요 수 기반 필터링 (임계값 설정 필요)
        # if tweet.retweet_count > 100 or tweet.favorite_count > 200:
        #     return True

        return False

    def collect_trending_tweets(self, count=100):
        """
        일반 트렌딩 트윗들을 수집합니다 (특정 키워드 필터링 없음).
        :param count: 수집할 트윗 수 (10-100)
        :return: 정규화된 트윗 데이터 리스트
        """
        max_results = count
        logger.info(f"트렌딩 트윗 수집 시작 (API v2, max_results={max_results})")

        # 인기 있는 트윗을 찾기 위한 일반적인 쿼리
        # 리트윗 제외, 한국어로 제한
        trending_query = "lang:ko -is:retweet"
        
        raw_tweets_enriched = self.search_recent_tweets(trending_query, max_results=max_results)
        trending_tweets_data = []

        if not raw_tweets_enriched:
            logger.warning("트렌딩 트윗에 대한 API v2 검색 결과가 없습니다.")
            return []

        for tweet_dict in raw_tweets_enriched:
            # 모든 트윗을 수집 (특정 콘텐츠 필터링 제거)
            normalized_tweet = self._normalize_tweet_data_v2(tweet_dict)
            if normalized_tweet:
                # CouchDB에 저장
                try:
                    success = self.db_handler.save_document(normalized_tweet)
                    if success:
                        trending_tweets_data.append(normalized_tweet)
                        logger.info(f"트렌딩 트윗 저장 성공: {normalized_tweet['_id']}")
                    else:
                        logger.warning(f"트렌딩 트윗 저장 실패: {normalized_tweet['_id']}")
                except Exception as e:
                    logger.error(f"트렌딩 트윗 저장 중 오류: {e}")

        logger.info(f"트렌딩 트윗 {len(trending_tweets_data)}개 최종 수집 (API v2)")
        return trending_tweets_data

    def _is_meme_content_v2(self, tweet_dict):
        """
        API v2 트윗 데이터(dict)가 밈 관련 콘텐츠인지 판단하는 내부 로직.
        - 미디어(이미지, 비디오) 포함 여부
        - 텍스트 내 특정 키워드 포함 여부
        - 공용 측정치(좋아요, 리트윗 등) 활용 (선택적)
        """
        # 1. 미디어 포함 여부 (attachments_media 필드 확인)
        if tweet_dict.get('attachments_media'):
            for media in tweet_dict['attachments_media']:
                if media.get('type') in ['photo', 'video', 'animated_gif']: # animated_gif는 API v2에서 video로 처리될 수 있음
                    return True

        # 2. 텍스트 내 특정 키워드 확인 (엔터테인먼트/문화 콘텐츠)
        trend_keywords = [
            # 심리 테스트 관련
            "심리테스트", "MBTI", "성격테스트", "심리", "성격", "테스트",
            # 놀이 문화 관련  
            "챌린지", "게임", "퀴즈", "놀이", "재미", "장난",
            # 밈/유머 관련
            "#meme", "#밈", "웃긴", "유머", "ㅋㅋ", "짤", "개웃김",
            # 트렌드 관련
            "트렌드", "유행", "인기", "핫한", "화제"
        ]
        text_to_check = tweet_dict.get('text', "").lower()
        if any(keyword.lower() in text_to_check for keyword in trend_keywords):
            return True

        # 3. 공용 측정치 기반 필터링 (예시, 임계값은 조정 필요)
        public_metrics = tweet_dict.get('public_metrics', {})
        # if public_metrics.get('retweet_count', 0) > 50 or public_metrics.get('like_count', 0) > 100:
        #     return True

        return False

    def _categorize_content(self, text_content, hashtags):
        """
        트윗 내용을 기반으로 콘텐츠 카테고리를 분류합니다.
        """
        text_lower = text_content.lower()
        hashtags_lower = [tag.lower() for tag in hashtags]
        all_text = text_lower + " " + " ".join(hashtags_lower)
        
        categories = []
        
        # 심리/성격 테스트 관련
        psychology_keywords = ["심리테스트", "mbti", "성격테스트", "심리", "성격", "테스트", "엠비티아이"]
        if any(keyword in all_text for keyword in psychology_keywords):
            categories.append("psychology")
            
        # 게임/놀이 관련
        game_keywords = ["게임", "퀴즈", "놀이", "챌린지", "미니게임", "플레이"]
        if any(keyword in all_text for keyword in game_keywords):
            categories.append("game")
            
        # 밈/유머 관련
        meme_keywords = ["밈", "meme", "웃긴", "유머", "짤", "개웃김", "ㅋㅋ"]
        if any(keyword in all_text for keyword in meme_keywords):
            categories.append("meme")
            
        # 트렌드/문화 관련
        trend_keywords = ["트렌드", "유행", "인기", "핫한", "화제", "viral"]
        if any(keyword in all_text for keyword in trend_keywords):
            categories.append("trend")
            
        return categories if categories else ["general"]

    def _normalize_tweet_data_v2(self, tweet_dict):
        """
        Twitter API v2의 트윗 데이터(dict)를 CouchDB에 저장할 형태로 정규화합니다.
        'docs/data_collection_design.md'의 공통 데이터 모델을 참고합니다.
        """
        try:
            tweet_id = tweet_dict.get('id')
            if not tweet_id:
                logger.warning("트윗 ID가 없어 정규화할 수 없습니다.")
                return None

            doc_id = f"twitter:{tweet_id}" # CouchDB 문서 ID

            # 'author' 필드는 search_recent_tweets에서 이미 병합된 dict 형태를 기대
            author_info_dict = tweet_dict.get('author', {})
            author_id = author_info_dict.get('id')
            author_username = author_info_dict.get('username')
            author_name = author_info_dict.get('name')
            author_profile_image_url = author_info_dict.get('profile_image_url')

            # created_at을 UTC로 명시하고 ISO 형식으로 변환
            created_at_str = tweet_dict.get('created_at')
            created_at_iso = None
            if created_at_str:
                # API v2 created_at은 이미 ISO 8601 형식이지만, datetime 객체로 변환 후 다시 포맷팅
                # created_at_dt = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                # created_at_iso = created_at_dt.astimezone(timezone.utc).isoformat()
                created_at_iso = created_at_str # API v2는 이미 UTC ISO8601임

            media_list = []
            # 'attachments_media' 필드는 search_recent_tweets에서 이미 병합된 list of dicts 형태를 기대
            attachments_media_list = tweet_dict.get('attachments_media', [])
            if attachments_media_list:
                for m_dict in attachments_media_list: # 각 미디어는 이미 dict 형태
                    media_entry = {
                        "type": m_dict.get('type'),
                        "url": m_dict.get('url') or m_dict.get('preview_image_url'),
                        "thumbnail_url": m_dict.get('preview_image_url')
                    }
                    media_list.append(media_entry)

            hashtags = []
            mentions = []
            entities_dict = tweet_dict.get('entities', {})
            if entities_dict:
                if entities_dict.get('hashtags'):
                    hashtags = [tag['tag'] for tag in entities_dict['hashtags']]
                if entities_dict.get('mentions'):
                    mentions = [mention['username'] for mention in entities_dict['mentions']]

            public_metrics_dict = tweet_dict.get('public_metrics', {})
            
            # 콘텐츠 카테고리 분류
            text_content = tweet_dict.get('text', '')
            content_categories = self._categorize_content(text_content, hashtags)

            normalized_data = {
                "_id": doc_id,
                "platform": "X",
                "url": f"https://twitter.com/{author_username}/status/{tweet_id}" if author_username and tweet_id else None,
                "text_content": text_content,
                "author_id": author_id,
                "author_name": author_name,
                "author_username": author_username,
                "author_profile_image_url": author_profile_image_url,
                "created_at": created_at_iso,
                "collected_at": datetime.now(timezone.utc).isoformat(),
                "media": media_list,
                "hashtags": hashtags,
                "mentions": mentions,
                "engagement_metrics": {
                    "likes_count": public_metrics_dict.get('like_count', 0),
                    "comments_count": public_metrics_dict.get('reply_count', 0),
                    "shares_count": public_metrics_dict.get('retweet_count', 0),
                    "views_count": public_metrics_dict.get('impression_count', 0),
                    "quote_count": public_metrics_dict.get('quote_count', 0)
                },
                "location": None,
                "language": tweet_dict.get('lang'),
                "is_sensitive_content": tweet_dict.get('possibly_sensitive', False),
                "content_categories": content_categories,  # 새로 추가된 카테고리 필드
                "raw_data": tweet_dict
            }
            return normalized_data
        except Exception as e:
            logger.error(f"API v2 트윗 데이터 정규화 중 오류 발생 (트윗 ID: {tweet_dict.get('id', 'N/A')}): {e}", exc_info=True)
            return None

    def save_tweets_to_db(self, tweets_data_list):
        """
        정규화된 트윗 데이터 리스트를 CouchDB에 저장합니다.
        """
        if not self.db_handler or not self.db_handler.is_connected():
            logger.error("CouchDB 핸들러가 초기화되지 않았거나 연결되지 않아 저장을 스킵합니다.")
            return 0

        saved_count = 0
        skipped_count = 0
        # CouchDB의 _bulk_docs 사용을 고려해볼 수 있으나, 여기서는 개별 저장으로 단순화
        for tweet_doc in tweets_data_list:
            if not tweet_doc or not tweet_doc.get('_id'):
                logger.warning("잘못된 트윗 데이터 또는 ID가 없어 저장할 수 없습니다.")
                skipped_count +=1
                continue
            try:
                # 중복 저장을 피하기 위해 먼저 해당 ID의 문서가 있는지 확인 (선택적)
                # if self.db_handler.get_doc(tweet_doc['_id']):
                #     logger.info(f"트윗 {tweet_doc['_id']}은(는) 이미 DB에 존재합니다. 업데이트하지 않고 스킵합니다.")
                #     skipped_count += 1
                #     continue

                # save_doc은 존재하면 업데이트, 없으면 생성
                doc_id, doc_rev = self.db_handler.save_doc(tweet_doc) # save_doc은 _id와 _rev를 반환
                if doc_id and doc_rev:
                    logger.info(f"트윗 {doc_id} DB 저장/업데이트 성공 (Rev: {doc_rev})")
                    saved_count += 1
                else:
                    # save_doc 내부에서 오류 발생 시 None 반환 가능성 있음 (또는 예외 발생)
                    logger.error(f"트윗 {tweet_doc['_id']} DB 저장 실패 (save_doc에서 유효한 응답 없음)")
                    skipped_count += 1
            except couchdb.http.ResourceConflict: # couchdb 라이브러리 사용 시
                 logger.warning(f"트윗 {tweet_doc['_id']} 저장 중 충돌 발생 (이미 존재하며 revision 불일치). 스킵 또는 업데이트 로직 필요.")
                 # 필요시 문서를 가져와 _rev를 설정하고 다시 시도하는 로직 추가
                 skipped_count += 1
            except Exception as e:
                logger.error(f"트윗 {tweet_doc['_id']} DB 저장 중 알 수 없는 오류: {e}", exc_info=True)
                skipped_count += 1

        logger.info(f"총 {len(tweets_data_list)}개 중 {saved_count}개 트윗 DB 저장/업데이트, {skipped_count}개 스킵/실패.")
        return saved_count

# --- 사용 예시 (테스트용) ---
if __name__ == '__main__':
    # 로깅 기본 설정 (파일 실행 시에만 적용되도록)
    if not logger.hasHandlers(): # 중복 핸들러 방지
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # !!! Twitter API v2 Bearer Token을 사용해야 합니다 !!!
    # 환경 변수에서 로드: TWITTER_BEARER_TOKEN
    # 예: COUCHDB_URL (형식: http://user:pass@host:port/), COUCHDB_DB_NAME

    BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    COUCHDB_URL = os.getenv("COUCHDB_URL", "http://admin:password@localhost:5984/")
    COUCHDB_DB_NAME = os.getenv("COUCHDB_MEME_DB_NAME", "meme_trends_db") # DB 이름 변경

    if not BEARER_TOKEN:
        logger.error("!!! 중대한 오류: Twitter API Bearer Token이 환경 변수에 설정되지 않았습니다 !!!")
        logger.error("TWITTER_BEARER_TOKEN 환경 변수를 설정해주세요.")
        exit(1)

    if "YOUR_BEARER_TOKEN" in BEARER_TOKEN: # 기본값 체크
        logger.warning("!!! 경고: 트위터 Bearer Token이 기본값('YOUR_BEARER_TOKEN')으로 설정되어 있습니다. 실제 값으로 변경해주세요. !!!")

    logger.info(f"CouchDB 접속 정보: URL='{COUCHDB_URL}', DB_NAME='{COUCHDB_DB_NAME}'")

    try:
        collector = TwitterCollector(
            bearer_token=BEARER_TOKEN,
            couchdb_url=COUCHDB_URL,
            couchdb_db_name=COUCHDB_DB_NAME
        )

        if collector.db_handler is None or not collector.db_handler.is_connected():
            logger.error("CouchDB 핸들러 초기화 실패 또는 연결되지 않아 스크립트를 종료합니다.")
            exit(1)

        # 1. 일반 트렌딩 트윗 수집 (API v2 사용)
        logger.info(f"\n일반 트렌딩 트윗 수집 중 (API v2)...")

        # collect_trending_tweets 메소드 호출 - 특정 키워드 없이 인기 트윗 수집
        trending_tweets_normalized = collector.collect_trending_tweets(count=30)

        if trending_tweets_normalized:
            logger.info(f"총 {len(trending_tweets_normalized)}개의 트렌딩 트윗을 정규화했습니다.")
            for i, tweet_data in enumerate(trending_tweets_normalized[:2]): # 처음 2개만 상세 로깅
                logger.info(f"\n--- 정규화된 트렌딩 트윗 {i+1} ---")
                logger.info(f"DB ID: {tweet_data.get('_id')}")
                logger.info(f"사용자: @{tweet_data.get('author_username')}")
                logger.info(f"내용: {tweet_data.get('text_content', '')[:100]}...")
                logger.info(f"미디어: {tweet_data.get('media')}")
                logger.info(f"해시태그: {tweet_data.get('hashtags')}")
                logger.info(f"생성 시간: {tweet_data.get('created_at')}")
                logger.info(f"수집 시간: {tweet_data.get('collected_at')}")
                logger.info(f"원본 URL: {tweet_data.get('url')}")

            logger.info("\n정규화된 트윗을 CouchDB에 저장 완료 (collect_trending_tweets 메소드 내부에서 처리)")
            logger.info(f"{len(trending_tweets_normalized)}개의 트윗이 성공적으로 DB에 저장되었습니다.")
        else:
            logger.info(f"트렌딩 트윗을 찾지 못했거나 정규화하지 못했습니다.")

    except tweepy.TweepyException as te:
        logger.error(f"Twitter API 관련 오류 발생: {te}", exc_info=True)
    except ConnectionError as ce: # CouchDBHandler에서 발생시키는 예외
        logger.error(f"DB 연결 오류 발생: {ce}", exc_info=True)
    except Exception as e:
        logger.error(f"스크립트 실행 중 알 수 없는 오류 발생: {e}", exc_info=True)

# TODO (API v2 마이그레이션 및 개선):
# 1. [완료] `__init__`: Bearer Token 사용하도록 변경 (tweepy.Client)
# 2. [완료] `search_recent_tweets`: API v2의 `client.search_recent_tweets` 사용하도록 구현.
#    - [완료] `tweet_fields`, `expansions`, `media_fields`, `user_fields` 등 활용하여 필요한 정보 요청.
#    - [완료] 응답에서 `includes` 데이터를 활용하여 트윗-사용자-미디어 정보 병합.
# 3. [완료] `_is_meme_content_v2`: API v2 응답 구조 (dict)에 맞춰 밈 판단 로직 수정.
#    - `tweet_dict.get('attachments_media')`, `tweet_dict.get('text')`, `tweet_dict.get('public_metrics')` 등 사용.
# 4. [완료] `_normalize_tweet_data_v2`: API v2 응답 구조 (dict) 및 `docs/data_collection_design.md`의 공통 모델에 맞춰 정규화.
#    - `created_at` UTC 변환 및 ISO 포맷팅.
#    - `media` 필드 구조화.
#    - `engagement_metrics` 필드 매핑 (like_count, reply_count, retweet_count, impression_count, quote_count).
#    - `platform`을 "X"로 변경.
# 5. [완료] `collect_meme_tweets`: 내부적으로 API v2 관련 메소드 (`search_recent_tweets`, `_is_meme_content_v2`, `_normalize_tweet_data_v2`) 호출하도록 수정.
# 6. [완료] `save_tweets_to_db`: CouchDB 저장 로직은 대체로 유지, 로깅 및 오류 처리 강화. `couchdb.http.ResourceConflict` 예외 처리 추가.
# 7. [완료] `if __name__ == '__main__':` 테스트 코드:
#    - [완료] Bearer Token 사용하도록 수정.
#    - [완료] API v2 기반의 수집 및 저장 테스트.
# 8. [진행중] 로깅 강화: 모든 print 문을 logger로 대체, 예외 발생 시 `exc_info=True` 추가.
# 9. [필요] 환경 변수 이름 일관성 있게 변경 (예: `COUCHDB_DB_NAME` 등).
# 10. [필요] `data_collection_design.md`의 공통 데이터 모델과 최종 정규화 필드가 일치하는지 다시 한번 검토 및 필요시 문서 업데이트.
#     - 특히 `engagement_metrics`의 필드명 (예: `shares_count` vs `retweet_count`)
#     - `media` 내부 구조 (type, url, thumbnail_url)
# 11. [필요] API Rate Limit 상세 처리: tweepy의 `wait_on_rate_limit=True` 외에 수동으로 Rate Limit 정보 확인 및 대응 로직 (현재는 tweepy에 의존).
# 12. [필요] 오류 처리 및 재시도 로직 강화 (예: 네트워크 오류 시).
# 13. [선택] 스케줄러 연동 부분은 주석 처리 유지 또는 별도 스크립트로 분리.
# 14. [선택] 단위 테스트 및 통합 테스트 작성 (pytest 권장).

# print("src/collectors/twitter_collector.py 파일이 업데이트 되었습니다 (API v2 기준).")
# print("TWITTER_BEARER_TOKEN 환경변수를 설정하고, CouchDB 서버를 실행한 후 테스트 코드를 실행해볼 수 있습니다.")
# print("DB 이름은 COUCHDB_MEME_DB_NAME 환경변수로 설정 가능합니다 (기본값: meme_trends_db).")
