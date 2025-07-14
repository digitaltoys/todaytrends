# TodayTrends - SNS 트렌드 분석 웹 애플리케이션

SNS의 최신 트렌드를 분석하여 보여주는 웹 애플리케이션입니다.

## 기술 스택

- **프론트엔드**: Vite + React + TypeScript + Tailwind CSS + Zustand
- **백엔드**: Python + CouchDB
- **데이터 수집**: Twitter API v2

## 서버 실행 방법

### 1. 환경변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 변수들을 설정하세요:

```env
# 백엔드용 (Python 데이터 수집기)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here
COUCHDB_URL=http://username:password@your-couchdb-host:5984/
COUCHDB_MEME_DB_NAME=your_database_name

# 프론트엔드용 (React 대시보드) - VITE_ 접두사 필요
VITE_COUCHDB_HOST=your-couchdb-host.com
VITE_COUCHDB_USERNAME=your_username
VITE_COUCHDB_PASSWORD=your_password
VITE_COUCHDB_DB_NAME=your_database_name
```

⚠️ **주의**: `.env` 파일은 Git에 커밋하지 마세요!

### 2. 프론트엔드 실행

```bash
# 프로젝트 루트에서
npm install
npm run dev
```

#### 📝 문제 해결

만약 rollup 관련 오류가 발생하면:
```bash
# node_modules와 package-lock.json 삭제 후 재설치
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### 3. 백엔드 데이터 수집기 실행

#### 필요한 Python 패키지 설치
```bash
# 시스템 Python3에 필요한 패키지 설치
python3 -m pip install tweepy python-dotenv couchdb
```

#### Twitter 데이터 수집
```bash
# 프로젝트 루트에서
cd server
python3 -m src.collectors.twitter_collector
```

#### CouchDB 연결 테스트
```bash
# 프로젝트 루트에서
cd server
python3 -m src.db_handler
```

#### Twitter 수집기 단위 테스트
```bash
# 프로젝트 루트에서
cd server
python3 -m unittest src.collectors.test_twitter_collector
```

## 현재 구현 상태

### ✅ 완료된 기능
- Twitter API v2를 통한 밈 관련 트윗 수집
- CouchDB 데이터베이스 연동
- 데이터 정규화 및 저장
- 단위 테스트

### 🚧 개발 중인 기능
- 웹 API 서버 (Flask/FastAPI)
- 프론트엔드 대시보드
- 다른 SNS 플랫폼 연동 (인스타그램, 틱톡, 유튜브 쇼츠)
- 트렌드 분석 및 시각화
- 주기적 데이터 수집 스케줄러

## 프로젝트 구조

```
todaytrends/
├── src/                    # React 프론트엔드
├── server/                 # Python 백엔드
│   └── src/
│       ├── collectors/     # 데이터 수집 모듈
│       └── db_handler.py   # CouchDB 핸들러
├── docs/                   # 설계 문서
└── .env                    # 환경변수 설정 (Git 제외)
```

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      ...tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      ...tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      ...tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default tseslint.config([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
