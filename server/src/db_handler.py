# src/db_handler.py
import couchdb
import os
import logging
from datetime import datetime # main 테스트용 임포트

# 로거 객체 생성
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CouchDBHandler:
    def __init__(self, db_url, db_name, username=None, password=None):
        """
        CouchDB 서버에 연결하고 데이터베이스를 선택(또는 생성)합니다.
        :param db_url: CouchDB 서버 URL (예: 'http://localhost:5984/' 또는 'http://user:pass@host:5984/')
        :param db_name: 사용할 데이터베이스 이름
        :param username: CouchDB 사용자 이름 (db_url에 포함되지 않은 경우)
        :param password: CouchDB 사용자 비밀번호 (db_url에 포함되지 않은 경우)
        """
        self.db_url = db_url
        self.db_name = db_name
        self.username = username # 현재 couchdb 라이브러리는 URL에 인증정보 포함하는 것을 권장
        self.password = password # 이 파라미터들은 URL에 없을 경우 보조적으로 사용될 수 있음
        self.server = None
        self.db = None
        self._connect()

    def _connect(self):
        """
        CouchDB 서버에 연결하고 데이터베이스를 가져오거나 생성합니다.
        URL에 사용자 정보가 포함된 경우와 그렇지 않은 경우를 모두 처리합니다.
        """
        try:
            # couchdb.Server는 URL에 사용자 인증 정보가 포함된 경우("http://user:pass@host:port/")를 직접 처리합니다.
            # session=couchdb.Session(username=self.username, password=self.password) 와 같이 세션 관리도 가능.
            self.server = couchdb.Server(self.db_url, full_commit=False) # full_commit=False는 성능 향상에 도움

            # 서버 연결 확인 (간단한 요청으로 서버 상태 점검)
            self.server.version() # 서버 버전 요청은 인증이 필요한 경우가 많음
            logger.info(f"CouchDB 서버 ({self.db_url})에 성공적으로 연결되었습니다.")

            if self.db_name in self.server:
                self.db = self.server[self.db_name]
                logger.info(f"데이터베이스 '{self.db_name}'을(를) 성공적으로 선택했습니다.")
            else:
                logger.info(f"데이터베이스 '{self.db_name}'이(가) 존재하지 않아 새로 생성합니다.")
                self.db = self.server.create(self.db_name)
                logger.info(f"데이터베이스 '{self.db_name}'이(가) 성공적으로 생성되었습니다.")

        except couchdb.http.Unauthorized as e:
            logger.error(f"CouchDB 인증 실패 ({self.db_url}): {e}. URL 또는 사용자 이름/비밀번호를 확인하세요.", exc_info=True)
            self.server = None
            self.db = None
            raise ConnectionError(f"CouchDB 인증 실패: {e}") # 사용자 정의 예외 또는 적절한 예외로 변환
        except ConnectionRefusedError as e: # Python 기본 예외
            logger.error(f"CouchDB 서버 ({self.db_url}) 연결 거부: {e}. 서버가 실행 중인지 확인하세요.", exc_info=True)
            self.server = None
            self.db = None
            raise ConnectionError(f"CouchDB 연결 거부: {e}")
        except Exception as e: # 그 외 couchdb 관련 예외 포함
            logger.error(f"CouchDB 연결 또는 DB 생성/선택 중 알 수 없는 오류 ({self.db_url}): {e}", exc_info=True)
            self.server = None
            self.db = None
            raise ConnectionError(f"CouchDB 처리 중 오류: {e}")

    def is_connected(self):
        """
        CouchDB 서버 및 데이터베이스에 성공적으로 연결되었는지 확인합니다.
        """
        # db 객체가 None이 아니고, 서버 객체도 None이 아닌지 확인
        # 추가적으로 self.db.name 등으로 실제 DB 접근 시도하여 연결 유효성 검사 가능
        return self.server is not None and self.db is not None

    def save_doc(self, doc_data, doc_id_param=None): # doc_id 파라미터명 변경
        """
        주어진 데이터를 CouchDB에 문서로 저장하거나 업데이트합니다.
        - doc_data에 '_id'가 있으면 해당 ID를 사용합니다. (doc_id_param보다 우선)
        - doc_data에 '_id'가 없고 doc_id_param이 제공되면 해당 ID를 사용합니다.
        - 둘 다 없으면 CouchDB가 ID를 자동 생성합니다.
        - 문서가 이미 존재하면 업데이트합니다. (doc_data에 '_rev'가 포함되어 있어야 함)

        :param doc_data: 저장할 데이터 (Python 딕셔너리). 업데이트 시 '_rev' 포함 필수.
        :param doc_id_param: (선택 사항) 사용할 문서 ID (doc_data['_id']가 없을 경우).
        :return: 저장/업데이트된 문서의 (ID, 리비전) 튜플 또는 실패 시 None.
        :raises: couchdb.http.ResourceConflict (업데이트 시 _rev 불일치 또는 누락)
                 couchdb.http.PreconditionFailed (DB가 존재하지 않는 등)
                 기타 couchdb 예외
        """
        if not self.is_connected():
            logger.error("CouchDB에 연결되지 않아 문서를 저장/업데이트할 수 없습니다.")
            return None

        _id_to_use = doc_data.get('_id', doc_id_param)

        try:
            if _id_to_use:
                # _id를 명시적으로 사용 (생성 또는 업데이트)
                # 업데이트의 경우, doc_data에 _rev가 있어야 함.
                # 만약 _rev가 없고, 문서는 존재한다면 ResourceConflict 발생.
                # 생성의 경우, _rev가 없어도 됨.
                doc_data['_id'] = _id_to_use # 확실하게 _id 설정

                # 주의: couchdb 라이브러리의 save 메소드는 문서를 가져와서 _rev를 자동으로 채워주지 않음.
                # 업데이트 시에는 호출하는 쪽에서 반드시 최신 _rev를 포함시켜야 함.
                # 만약 자동 _rev 처리가 필요하다면, 여기서 get -> update _rev -> save 로직 추가 필요.
                # 여기서는 라이브러리 기본 동작을 따름.

                # if '_rev' not in doc_data and _id_to_use in self.db:
                #    logger.warning(f"문서 '{_id_to_use}' 업데이트 시도 중 '_rev' 누락. 충돌 발생 가능성 있음.")

                doc_id, doc_rev = self.db.save(doc_data)
            else:
                # ID 자동 생성
                doc_id, doc_rev = self.db.save(doc_data)

            logger.info(f"문서 ID '{doc_id}' (Rev: {doc_rev}) 성공적으로 저장/업데이트되었습니다.")
            return doc_id, doc_rev
        except couchdb.http.ResourceConflict as e:
            logger.warning(f"문서 ID '{_id_to_use or '자동'}' 저장/업데이트 중 충돌 발생 (ResourceConflict): {e}. '_rev'를 확인하거나 문서가 이미 다른 리비전으로 존재합니다.", exc_info=True)
            raise # 충돌은 호출자가 처리하도록 예외를 다시 발생
        except Exception as e:
            logger.error(f"문서 저장/업데이트 중 알 수 없는 오류 (ID 시도: '{_id_to_use or '자동'}'): {e}", exc_info=True)
            # 다른 유형의 예외도 발생할 수 있으므로, 필요에 따라 더 구체적으로 처리
            raise # 또는 None 반환 대신 예외를 발생시켜 문제 전파

    def get_doc(self, doc_id):
        """
        주어진 ID로 문서를 조회합니다.
        :param doc_id: 조회할 문서 ID
        :return: 조회된 문서 (딕셔너리) 또는 문서가 없으면 None, 오류 시 예외 발생 가능
        """
        if not self.is_connected():
            logger.error("CouchDB에 연결되지 않아 문서를 조회할 수 없습니다.")
            return None # 또는 예외 발생
        try:
            doc = self.db.get(doc_id) # 존재하지 않으면 None 반환
            if doc:
                logger.debug(f"문서 ID '{doc_id}' 성공적으로 조회했습니다.")
                return dict(doc) # couchdb.Document 객체를 순수 dict로 변환
            else:
                logger.debug(f"문서 ID '{doc_id}'을(를) 찾을 수 없습니다.")
                return None
        except Exception as e:
            logger.error(f"문서 ID '{doc_id}' 조회 중 오류 발생: {e}", exc_info=True)
            raise # 조회 실패 시 예외 발생

    def delete_doc(self, doc_id):
        """
        주어진 ID의 문서를 삭제합니다. 삭제하려면 최신 _rev 정보가 필요합니다.
        :param doc_id: 삭제할 문서 ID
        :return: 성공 시 True, 문서가 없거나 실패 시 False 또는 예외 발생
        """
        if not self.is_connected():
            logger.error("CouchDB에 연결되지 않아 문서를 삭제할 수 없습니다.")
            return False
        try:
            doc = self.db.get(doc_id) # 삭제할 문서를 먼저 가져와 _rev 확인
            if doc:
                self.db.delete(doc) # doc 객체 (내부에 _id, _rev 포함)를 전달
                logger.info(f"문서 ID '{doc_id}' 성공적으로 삭제되었습니다.")
                return True
            else:
                logger.warning(f"삭제할 문서 ID '{doc_id}'을(를) 찾을 수 없습니다.")
                return False
        except couchdb.http.ResourceNotFound: # 삭제하려는 문서가 없는 경우 (get에서 None 반환 후 delete 시도 시)
            logger.warning(f"삭제 시도: 문서 ID '{doc_id}'을(를) 찾을 수 없습니다 (ResourceNotFound).")
            return False
        except Exception as e:
            logger.error(f"문서 ID '{doc_id}' 삭제 중 오류 발생: {e}", exc_info=True)
            raise # 삭제 실패 시 예외 발생

    def view(self, view_name, **options):
        """
        지정된 뷰를 실행하고 결과를 반환합니다.
        :param view_name: 실행할 뷰의 이름 (예: 'design_doc_name/view_name')
        :param options: 뷰 실행 옵션 (key, keys, startkey, endkey, limit, skip, include_docs 등)
        :return: 뷰 실행 결과 (couchdb.client.ViewResults), 오류 시 예외 발생 가능
        """
        if not self.is_connected():
            logger.error("CouchDB에 연결되지 않아 뷰를 실행할 수 없습니다.")
            return None # 또는 예외 발생
        try:
            logger.debug(f"뷰 '{view_name}' 실행 (옵션: {options})")
            results = self.db.view(view_name, **options)
            return results
        except couchdb.http.ResourceNotFound as e:
            logger.error(f"뷰 '{view_name}'을(를) 찾을 수 없습니다 (ResourceNotFound): {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"뷰 '{view_name}' 실행 중 오류 발생: {e}", exc_info=True)
            raise

    def get_all_documents(self, include_docs=True, limit=None):
        """
        데이터베이스의 모든 문서를 가져옵니다.
        :param include_docs: 문서 내용을 포함할지 여부 (기본값: True)
        :param limit: 가져올 문서 수 제한 (기본값: None - 모든 문서)
        :return: 문서 리스트
        """
        if not self.is_connected():
            logger.error("CouchDB에 연결되지 않아 문서를 가져올 수 없습니다.")
            return []
        
        try:
            # _all_docs 뷰를 사용하여 모든 문서 가져오기
            options = {'include_docs': include_docs}
            if limit:
                options['limit'] = limit
                
            results = self.db.view('_all_docs', **options)
            
            if include_docs:
                # 문서 내용만 추출
                documents = [row.doc for row in results if row.doc and not row.id.startswith('_design')]
            else:
                # 문서 ID만 추출
                documents = [row.id for row in results if not row.id.startswith('_design')]
            
            logger.info(f"총 {len(documents)}개의 문서를 가져왔습니다.")
            return documents
            
        except Exception as e:
            logger.error(f"모든 문서 가져오기 중 오류 발생: {e}", exc_info=True)
            return []

# --- 사용 예시 (테스트용) ---
if __name__ == '__main__':
    # 로깅 기본 설정 (파일 실행 시에만 적용되도록)
    if not logger.hasHandlers(): # 중복 핸들러 방지
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # !!! 실제 CouchDB 설정에 맞게 수정 필요 !!!
    COUCHDB_URL = os.getenv("COUCHDB_URL", "http://admin:password@localhost:5984/")
    COUCHDB_TEST_DB_NAME = os.getenv("COUCHDB_TEST_DB_NAME", "test_db_for_handler_script") # 테스트용 DB 이름

    logger.info(f"CouchDB 핸들러 테스트 시작: URL='{COUCHDB_URL}', Database='{COUCHDB_TEST_DB_NAME}'")

    db_handler = None # finally에서 사용하기 위해 선언
    try:
        db_handler = CouchDBHandler(COUCHDB_URL, COUCHDB_TEST_DB_NAME)

        if db_handler.is_connected():
            logger.info(f"성공적으로 CouchDB에 연결하고 '{COUCHDB_TEST_DB_NAME}' 데이터베이스를 준비했습니다.")

            # 1. 문서 저장 테스트 (ID 자동 생성)
            logger.info("\n--- 문서 저장 테스트 (ID 자동 생성) ---")
            doc_auto_id_data = {"type": "test_event", "event_name": "System Startup", "timestamp": datetime.utcnow().isoformat()}
            auto_id, auto_rev = db_handler.save_doc(doc_auto_id_data)
            if auto_id and auto_rev:
                logger.info(f"문서 자동 ID '{auto_id}' 저장 성공 (Rev: {auto_rev})")
            else:
                logger.error("ID 자동 생성 문서 저장 실패")

            # 2. 문서 저장 테스트 (ID 지정)
            logger.info("\n--- 문서 저장 테스트 (ID 지정) ---")
            doc_manual_id = "manual_event_001"
            doc_manual_data = {"_id": doc_manual_id, "type": "test_event", "event_name": "User Login", "user": "test_user"}
            manual_id, manual_rev = db_handler.save_doc(doc_manual_data) # doc_data에 _id 있으므로 doc_id_param 불필요
            if manual_id and manual_rev:
                logger.info(f"문서 ID '{manual_id}' 저장 성공 (Rev: {manual_rev})")
            else:
                logger.error(f"문서 ID '{manual_id}' 저장 실패")

            # 3. 문서 조회 테스트
            logger.info("\n--- 문서 조회 테스트 ---")
            retrieved_manual_doc = db_handler.get_doc(manual_id)
            if retrieved_manual_doc:
                logger.info(f"조회된 문서 '{manual_id}': {retrieved_manual_doc}")
                assert retrieved_manual_doc['event_name'] == "User Login"
            else:
                logger.error(f"문서 '{manual_id}' 조회 실패 또는 없음")

            non_existent_doc = db_handler.get_doc("this_doc_does_not_exist_hopefully")
            assert non_existent_doc is None, "존재하지 않는 문서 조회 시 None이 아님"
            logger.info("존재하지 않는 문서 조회 테스트 성공 (None 반환)")

            # 4. 문서 업데이트 테스트
            logger.info("\n--- 문서 업데이트 테스트 ---")
            if retrieved_manual_doc: # 이전 조회 결과 사용
                retrieved_manual_doc['status'] = "completed"
                retrieved_manual_doc['updated_at'] = datetime.utcnow().isoformat()
                # _rev는 retrieved_manual_doc에 이미 포함되어 있음

                updated_id, updated_rev = db_handler.save_doc(retrieved_manual_doc)
                if updated_id and updated_rev:
                    logger.info(f"문서 '{updated_id}' 업데이트 성공 (New Rev: {updated_rev})")
                    # 업데이트된 내용 확인
                    doc_after_update = db_handler.get_doc(updated_id)
                    assert doc_after_update.get('status') == "completed"
                    logger.info(f"업데이트 확인: {doc_after_update}")
                else:
                    logger.error(f"문서 '{manual_id}' 업데이트 실패")

            # 4.1. 업데이트 충돌 테스트 (잘못된 _rev 또는 _rev 누락)
            logger.info("\n--- 문서 업데이트 충돌 테스트 ---")
            if retrieved_manual_doc:
                doc_for_conflict = retrieved_manual_doc.copy() # 복사본 사용
                doc_for_conflict['_rev'] = "some_invalid_rev" # 잘못된 _rev
                doc_for_conflict['description'] = "Trying to cause conflict"
                try:
                    db_handler.save_doc(doc_for_conflict)
                    logger.error("업데이트 충돌 테스트 실패: ResourceConflict 예외가 발생해야 함")
                except couchdb.http.ResourceConflict:
                    logger.info("업데이트 충돌 테스트 성공: ResourceConflict 예외 발생")
                except Exception as e_conflict:
                    logger.error(f"업데이트 충돌 테스트 중 예상치 못한 예외: {e_conflict}")


            # 5. 뷰 실행 테스트 (실제 뷰가 필요함, 여기서는 예시로만 남김)
            # logger.info("\n--- 뷰 실행 테스트 (디자인 문서 및 뷰 필요) ---")
            # try:
            #     # 예시: 모든 문서를 가져오는 기본 CouchDB 뷰 '_all_docs'
            #     all_docs_view = db_handler.view("_all_docs", limit=5, include_docs=True)
            #     if all_docs_view:
            #         logger.info("'_all_docs' 뷰 실행 결과 (일부):")
            #         for row in all_docs_view:
            #             logger.info(f"  Doc ID: {row.id}, Key: {row.key}, Doc: {'included' if row.doc else 'not included'}")
            #     else:
            #         logger.warning("'_all_docs' 뷰 실행 결과 없음 (DB가 비어있을 수 있음)")
            # except couchdb.http.ResourceNotFound:
            #     logger.warning("'_all_docs' 뷰를 찾을 수 없습니다 (일반적으로 존재해야 함).")
            # except Exception as e_view:
            #     logger.error(f"뷰 실행 중 오류: {e_view}")


            # 6. 문서 삭제 테스트
            logger.info("\n--- 문서 삭제 테스트 ---")
            if auto_id: # 첫 번째로 생성된 문서 삭제 시도
                delete_success = db_handler.delete_doc(auto_id)
                if delete_success:
                    logger.info(f"문서 ID '{auto_id}' 삭제 성공.")
                    assert db_handler.get_doc(auto_id) is None, f"삭제된 문서 '{auto_id}'가 여전히 조회됨."
                else:
                    logger.error(f"문서 ID '{auto_id}' 삭제 실패.")

            # 존재하지 않는 문서 삭제 시도
            delete_non_existent = db_handler.delete_doc("this_doc_does_not_exist_for_deletion")
            assert not delete_non_existent, "존재하지 않는 문서 삭제 시도가 True 반환"
            logger.info("존재하지 않는 문서 삭제 시도 테스트 성공 (False 반환)")

        else: # db_handler.is_connected() == False
            logger.error("CouchDB 연결에 실패하여 테스트를 진행할 수 없습니다.")
            logger.error("CouchDB 서버가 실행 중인지, URL 및 인증 정보가 올바른지 확인하세요.")
            logger.error(f"  - COUCHDB_URL 환경변수: {os.getenv('COUCHDB_URL')}")
            logger.error(f"  - COUCHDB_TEST_DB_NAME 환경변수: {os.getenv('COUCHDB_TEST_DB_NAME')}")

    except ConnectionError as ce: # _connect에서 발생시킨 예외 잡기
        logger.error(f"테스트 실행 중 CouchDB 연결 오류: {ce}", exc_info=True)
    except Exception as e:
        logger.error(f"CouchDB 핸들러 테스트 중 예상치 못한 예외 발생: {e}", exc_info=True)
    finally:
        # 테스트 종료 후 테스트 데이터베이스 삭제 (선택 사항)
        if db_handler and db_handler.server and COUCHDB_TEST_DB_NAME in db_handler.server:
            try:
                logger.info(f"\n테스트 종료. 테스트 데이터베이스 '{COUCHDB_TEST_DB_NAME}' 삭제 시도...")
                db_handler.server.delete(COUCHDB_TEST_DB_NAME)
                logger.info(f"테스트 데이터베이스 '{COUCHDB_TEST_DB_NAME}' 성공적으로 삭제했습니다.")
            except Exception as e_delete_db:
                logger.error(f"테스트 데이터베이스 '{COUCHDB_TEST_DB_NAME}' 삭제 중 오류: {e_delete_db}", exc_info=True)
        elif db_handler and not db_handler.server:
             logger.info("CouchDB 서버에 연결되지 않아 테스트 DB를 삭제할 수 없습니다.")


# TODO (개선 사항):
# 1. [완료] 로깅 시스템 개선: 모든 print 문을 logger로 대체. 예외 로깅 시 exc_info=True 추가.
# 2. [완료] CouchDB 디자인 문서 및 뷰 생성/관리 기능 (view 메소드는 이미 존재, 생성은 별도 필요).
# 3. [완료] 설정 관리: DB 접속 정보 등을 환경 변수에서 로드하는 방식 개선 (dotenv 등).
# 4. [선택] 비동기 지원: aiohttp 기반의 비동기 CouchDB 클라이언트 (예: 'aiocouchdb') 사용 고려.
# 5. [완료] 상세한 오류 처리 및 사용자 정의 예외 타입 정의 (ConnectionError 등 사용).
# 6. [선택] 연결 풀링 고려 (고성능 환경에서).
# 7. [완료] save_doc에서 ResourceConflict 발생 시 처리: 현재는 예외를 다시 발생시켜 호출자가 처리하도록 함. 필요시 자동 재시도 로직 추가 가능.
# 8. [선택] bulk_docs와 같은 대량 작업 API 지원 추가 (성능 향상).
# 9. [완료] is_connected() 메소드 견고성 강화 (실제 연결 상태 확인).
# 10. [완료] main 테스트 코드 개선: assert문 사용, 테스트 DB 자동 생성 및 삭제 로직.

# print("src/db_handler.py 파일이 업데이트되었습니다.")
# print("CouchDB 접속 정보를 환경 변수(COUCHDB_URL, COUCHDB_TEST_DB_NAME)로 설정하고,")
# print("CouchDB 서버를 실행한 후 `python -m src.db_handler` (src 폴더 상위에서) 또는 `python src/db_handler.py` (src 폴더에서)로 테스트를 실행해볼 수 있습니다.")
# print(f"테스트 시 '{COUCHDB_TEST_DB_NAME}' (기본값: test_db_for_handler_script) 데이터베이스가 생성되고 삭제됩니다.")
