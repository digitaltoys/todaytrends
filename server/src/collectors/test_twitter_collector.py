import unittest
from unittest.mock import MagicMock, patch
import os
from datetime import datetime, timezone

# 테스트 대상 클래스 임포트
# PYTHONPATH가 'server' 디렉토리를 포함하거나, 실행 위치가 'server' 디렉토리의 부모라고 가정합니다.
# 예: python -m unittest server.src.collectors.test_twitter_collector (프로젝트 루트에서 실행)
from server.src.collectors.twitter_collector import TwitterCollector
from server.src.db_handler import CouchDBHandler # 의존성 주입을 위해 필요할 수 있음
import tweepy # tweepy.TweepyException을 사용하기 위해 임포트
import unittest
from unittest.mock import MagicMock, patch
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# .env 파일 로드 (테스트 실행 시 환경 변수 설정을 위해)
# 이 테스트 파일(test_twitter_collector.py)은 server/src/collectors/ 에 위치.
# .env 파일은 프로젝트 루트 (server 폴더의 부모)에 있다고 가정 (../../.env).
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    print(f"Test: Loaded .env from {dotenv_path}") # 로드 확인용 로그 (테스트 시에만)
else:
    load_dotenv() # 기본 경로에서 찾기
    print("Test: .env file not found at specific path, attempting default load_dotenv().")


class TestTwitterCollector(unittest.TestCase):

    def setUp(self):
        """테스트 시작 전 실행되는 메소드"""
        # .env 파일이나 실제 환경 변수에서 값을 가져오도록 시도하고, 없으면 기본 모의 값 사용
        self.mock_bearer_token = os.getenv("TWITTER_BEARER_TOKEN", "test_bearer_token_default")
        self.mock_couchdb_url = os.getenv("COUCHDB_URL", "http://fakecouch:5984/")
        self.mock_couchdb_db_name = os.getenv("COUCHDB_MEME_DB_NAME", "test_memes_db_default")

        # CouchDBHandler 모의 객체 생성
        self.mock_db_handler_instance = MagicMock(spec=CouchDBHandler)
        self.mock_db_handler_instance.is_connected.return_value = True
        self.mock_db_handler_instance.save_doc.return_value = ("mock_doc_id", "mock_doc_rev")
        self.mock_db_handler_instance.get_doc.return_value = None

        # tweepy.Client 모의 객체 생성
        self.mock_tweepy_client_instance = MagicMock(spec=tweepy.Client)

        # os.environ을 직접 설정하는 부분은 .env 로드로 대체되었으므로 주석 처리 또는 삭제 가능.
        # 테스트의 일관성을 위해 명시적으로 테스트용 값을 사용할 수도 있으나,
        # .env 로드 테스트를 겸한다면 실제 로드된 값을 사용하거나,
        # 테스트별로 필요한 환경변수를 patch.dict(os.environ, {...})로 설정하는 것이 좋음.
        # 여기서는 setUp에서 os.getenv를 사용하므로, 아래 os.environ 설정은 제거합니다.
        # os.environ["TWITTER_BEARER_TOKEN"] = self.mock_bearer_token
        # os.environ["COUCHDB_URL"] = self.mock_couchdb_url
        # os.environ["COUCHDB_MEME_DB_NAME"] = self.mock_couchdb_db_name

        # Patching 경로 수정: 실제 코드가 위치한 경로를 기준으로 패치
        self.patcher_db_handler = patch('server.src.collectors.twitter_collector.CouchDBHandler', return_value=self.mock_db_handler_instance)
        self.patcher_tweepy_client = patch('server.src.collectors.twitter_collector.tweepy.Client', return_value=self.mock_tweepy_client_instance)

        self.MockCouchDBHandler = self.patcher_db_handler.start()
        self.MockTweepyClient = self.patcher_tweepy_client.start()

        # 테스트 대상 Collector 인스턴스 생성
        self.collector = TwitterCollector(
            bearer_token=self.mock_bearer_token,
            couchdb_url=self.mock_couchdb_url,
            couchdb_db_name=self.mock_couchdb_db_name
        )

    def tearDown(self):
        """테스트 종료 후 실행되는 메소드"""
        self.patcher_db_handler.stop()
        self.patcher_tweepy_client.stop()
        # .env 파일 로드로 변경했으므로 tearDown에서 os.environ을 직접 삭제할 필요가 없습니다.
        # 만약 특정 테스트 케이스에서만 환경 변수를 임시로 설정하고 싶다면
        # unittest.mock.patch.dict를 사용하는 것이 좋습니다.
        # 아래 del 라인들은 주석 처리하거나 삭제합니다.
        # del os.environ["TWITTER_BEARER_TOKEN"]
        # del os.environ["COUCHDB_URL"]
        # del os.environ["COUCHDB_MEME_DB_NAME"]

    def test_initialization(self):
        """TwitterCollector 초기화 테스트"""
        # TwitterCollector 생성자에 전달된 값 (os.getenv 결과)으로 호출되는지 확인
        self.MockTweepyClient.assert_called_once_with(bearer_token=self.mock_bearer_token, wait_on_rate_limit=True)
        self.MockCouchDBHandler.assert_called_once_with(self.mock_couchdb_url, self.mock_couchdb_db_name, username=None, password=None)
        self.assertIsNotNone(self.collector.client)
        self.assertIsNotNone(self.collector.db_handler)
        self.assertTrue(self.collector.db_handler.is_connected())

    def test_search_recent_tweets_success(self):
        """최근 트윗 검색 성공 테스트 (API v2)"""
        mock_api_response = MagicMock(spec=tweepy.Response)
        mock_tweet_api_obj = MagicMock(spec=tweepy.Tweet)
        mock_tweet_api_obj.author_id = 'user1' # tweepy.Tweet 객체의 author_id
        mock_tweet_api_obj.data = { # tweepy.Tweet.data는 dict
            'id': '123', 'text': 'Test tweet #meme', 'created_at': '2023-01-01T12:00:00.000Z',
            'author_id': 'user1', # data 내부의 author_id (일관성을 위해)
            'public_metrics': {'like_count': 10, 'retweet_count': 5},
            'entities': {'hashtags': [{'tag': 'meme'}]}
        }
        mock_tweet_api_obj.attachments = None

        mock_user_api_obj = MagicMock(spec=tweepy.User)
        mock_user_api_obj.id = 'user1' # tweepy.User 객체의 id (users 딕셔너리 키로 사용됨)
        mock_user_api_obj.data = { # tweepy.User.data는 dict
            'id': 'user1', # data 내부의 id (일관성을 위해)
            'username': 'testuser',
            'name': 'Test User',
            'profile_image_url': 'http://example.com/user.jpg'
        }

        mock_api_response.data = [mock_tweet_api_obj] # API 응답의 data는 Tweet 객체 리스트
        mock_api_response.includes = {'users': [mock_user_api_obj]} # includes의 users는 User 객체 리스트

        self.mock_tweepy_client_instance.search_recent_tweets.return_value = mock_api_response

        query = "#meme"
        tweets_result = self.collector.search_recent_tweets(query, max_results=10) # 이 메소드가 enriched_dict 리스트 반환

        self.mock_tweepy_client_instance.search_recent_tweets.assert_called_once()
        self.assertEqual(len(tweets_result), 1, f"Expected 1 tweet, got {len(tweets_result)}")

        processed_tweet = tweets_result[0]
        self.assertEqual(processed_tweet['text'], 'Test tweet #meme')
        self.assertIn('author', processed_tweet, "Author information should be merged.")
        # self.assertEqual(processed_tweet['author']['username'], 'testuser') # 이 부분은 KeyError 발생 지점
        # KeyError: 'username'이 발생하는 이유는 mock_user_api_obj.data에 'username'이 없기 때문이 아니라,
        # processed_tweet['author'] 자체가 비어있을 수 있기 때문입니다.
        # users[tweet_obj.author_id] 접근이 실패하면 author: {} 가 됩니다.
        self.assertTrue(processed_tweet.get('author'), "Author field should exist and not be empty.")
        self.assertEqual(processed_tweet.get('author', {}).get('username'), 'testuser', "Username not found or incorrect in author info.")
        self.assertIn('attachments_media', processed_tweet)
        self.assertEqual(len(processed_tweet['attachments_media']), 0)


    def test_search_recent_tweets_api_error(self):
        """최근 트윗 검색 시 API 오류 발생 테스트"""
        self.mock_tweepy_client_instance.search_recent_tweets.side_effect = tweepy.TweepyException("API Error")

        query = "#error"
        tweets = self.collector.search_recent_tweets(query, max_results=10)

        self.assertEqual(len(tweets), 0)
        # 로그에 에러가 기록되었는지 확인할 수도 있습니다 (logging 모듈 mock 사용 필요)

    def test_is_meme_content_v2_with_media(self):
        """밈 콘텐츠 판단 테스트 (미디어 포함)"""
        tweet_dict = {'attachments_media': [{'type': 'photo'}]}
        self.assertTrue(self.collector._is_meme_content_v2(tweet_dict))

        tweet_dict_video = {'attachments_media': [{'type': 'video'}]}
        self.assertTrue(self.collector._is_meme_content_v2(tweet_dict_video))

        tweet_dict_gif = {'attachments_media': [{'type': 'animated_gif'}]}
        self.assertTrue(self.collector._is_meme_content_v2(tweet_dict_gif))

    def test_is_meme_content_v2_with_keyword(self):
        """밈 콘텐츠 판단 테스트 (키워드 포함)"""
        tweet_dict = {'text': '이거 완전 웃긴 밈 ㅋㅋㅋ #유머'}
        self.assertTrue(self.collector._is_meme_content_v2(tweet_dict))

    def test_is_meme_content_v2_not_meme(self):
        """밈 콘텐츠 판단 테스트 (밈 아님)"""
        tweet_dict = {'text': '일반적인 내용의 트윗입니다.'}
        self.assertFalse(self.collector._is_meme_content_v2(tweet_dict))

    def test_normalize_tweet_data_v2(self):
        """API v2 트윗 데이터 정규화 테스트"""
        now_iso = datetime.now(timezone.utc).isoformat()
        tweet_dict = {
            'id': 'tweet123',
            'text': 'Hello #world 밈이다!',
            'created_at': '2023-10-26T10:20:30.000Z',
            'author_id': 'user456',
            'author': { # search_recent_tweets에서 병합된 사용자 정보
                'id': 'user456',
                'username': 'testuser',
                'name': 'Test User Name',
                'profile_image_url': 'http://example.com/profile.jpg'
            },
            'public_metrics': {
                'like_count': 15, 'retweet_count': 5, 'reply_count': 2,
                'impression_count': 100, 'quote_count': 1
            },
            'entities': {
                'hashtags': [{'start': 6, 'end': 12, 'tag': 'world'}],
                'mentions': [{'start': 0, 'end': 5, 'username': 'anotheruser', 'id': 'user789'}]
            },
            'attachments_media': [{
                'media_key': 'media1', 'type': 'photo', 'url': 'http://example.com/image.jpg',
                'preview_image_url': 'http://example.com/preview.jpg'
            }],
            'lang': 'ko',
            'possibly_sensitive': False
        }

        normalized_data = self.collector._normalize_tweet_data_v2(tweet_dict)

        self.assertIsNotNone(normalized_data)
        self.assertEqual(normalized_data['_id'], 'twitter:tweet123')
        self.assertEqual(normalized_data['platform'], 'X')
        self.assertEqual(normalized_data['text_content'], 'Hello #world 밈이다!')
        self.assertEqual(normalized_data['author_username'], 'testuser')
        self.assertEqual(normalized_data['created_at'], '2023-10-26T10:20:30.000Z') # UTC ISO 형식 유지
        self.assertTrue(abs(datetime.fromisoformat(normalized_data['collected_at'].replace('Z', '+00:00')) - datetime.now(timezone.utc)).total_seconds() < 5) # 수집 시간 근사치 확인
        self.assertEqual(len(normalized_data['media']), 1)
        self.assertEqual(normalized_data['media'][0]['type'], 'photo')
        self.assertEqual(normalized_data['media'][0]['url'], 'http://example.com/image.jpg')
        self.assertIn('world', normalized_data['hashtags'])
        self.assertIn('anotheruser', normalized_data['mentions'])
        self.assertEqual(normalized_data['engagement_metrics']['likes_count'], 15)
        self.assertEqual(normalized_data['language'], 'ko')
        self.assertFalse(normalized_data['is_sensitive_content'])
        self.assertEqual(normalized_data['raw_data'], tweet_dict) # 원본 데이터 저장 확인

    def test_save_tweets_to_db(self):
        """DB 저장 테스트"""
        normalized_tweets = [{'_id': 'twitter:tweet1', 'text_content': 'Test 1'}]

        self.collector.save_tweets_to_db(normalized_tweets)

        # CouchDBHandler.save_doc이 호출되었는지 확인
        self.mock_db_handler_instance.save_doc.assert_called_once_with(normalized_tweets[0])

    def test_collect_meme_tweets_flow(self):
        """밈 트윗 수집 전체 흐름 테스트"""
        mock_api_response_flow = MagicMock(spec=tweepy.Response)

        mock_tweet_api_obj_flow = MagicMock(spec=tweepy.Tweet)
        mock_tweet_api_obj_flow.author_id = 'user2' # author_id 설정
        mock_tweet_api_obj_flow.data = {
            'id': 'tweet789', 'text': '웃긴 밈입니다! #meme', 'created_at': '2023-01-02T10:00:00.000Z',
            'author_id': 'user2', # tweet.data 내부에도 author_id가 있어야 함 (일관성)
            'public_metrics': {'like_count': 20},
            'entities': {'hashtags': [{'tag': 'meme'}]}
        }
        mock_tweet_api_obj_flow.attachments = {'media_keys': ['media_key_123']}

        mock_user_api_obj_flow = MagicMock(spec=tweepy.User)
        mock_user_api_obj_flow.id = 'user2' # User 객체의 id 속성
        mock_user_api_obj_flow.data = {
            'id': 'user2', # User.data 내부의 id
            'username': 'meme_lover', 'name': 'Meme Lover',
            'profile_image_url': 'http://example.com/user2.jpg'
        }

        mock_media_api_obj_flow = MagicMock(spec=tweepy.Media)
        mock_media_api_obj_flow.media_key = 'media_key_123' # Media 객체의 media_key 속성
        mock_media_api_obj_flow.data = {
            'media_key': 'media_key_123', # Media.data 내부의 media_key
            'type': 'photo', 'url': 'http://example.com/meme.jpg'
        }

        mock_api_response_flow.data = [mock_tweet_api_obj_flow]
        mock_api_response_flow.includes = {
            'users': [mock_user_api_obj_flow],
            'media': [mock_media_api_obj_flow]
        }
        self.mock_tweepy_client_instance.search_recent_tweets.return_value = mock_api_response_flow

        query = "#meme"
        collected_and_normalized_tweets = self.collector.collect_meme_tweets(query, count=10)

        self.mock_tweepy_client_instance.search_recent_tweets.assert_called_with(
            query=query, max_results=10,
            tweet_fields=unittest.mock.ANY, expansions=unittest.mock.ANY,
            media_fields=unittest.mock.ANY, user_fields=unittest.mock.ANY
        )
        self.assertEqual(len(collected_and_normalized_tweets), 1)

        processed_tweet = collected_and_normalized_tweets[0]
        self.assertEqual(processed_tweet['_id'], 'twitter:tweet789')
        # self.assertIn('author', processed_tweet, "Author info should be in normalized tweet") # data_collection_design.md 에는 author 객체가 없음
        # self.assertTrue(processed_tweet.get('author'), "Author field should exist and not be empty.")
        # self.assertEqual(processed_tweet.get('author', {}).get('username'), 'meme_lover')
        self.assertEqual(processed_tweet.get('author_username'), 'meme_lover', "author_username mismatch")
        self.assertEqual(processed_tweet.get('author_id'), 'user2', "author_id mismatch")
        self.assertIn('media', processed_tweet, "Media info should be in normalized tweet")
        self.assertEqual(len(processed_tweet['media']), 1)
        self.assertEqual(processed_tweet['media'][0]['type'], 'photo')
        self.assertEqual(processed_tweet['media'][0]['url'], 'http://example.com/meme.jpg')

        self.collector.save_tweets_to_db(collected_and_normalized_tweets)
        self.mock_db_handler_instance.save_doc.assert_called_with(processed_tweet)


if __name__ == '__main__':

    unittest.main(argv=['first-arg-is-ignored'], exit=False)
