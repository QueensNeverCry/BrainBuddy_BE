# BackEnd 디렉토리 구조 입니다. by.Karina

```plaintext
BackEnd/
│
├── src/
│   ├── main.py # uvicorn 실행파일
│   │
│   ├── api/  # 엔드포인트(라우터) 묶음
│   │    ├── users/  # "회원" 관련 모든 API
│   │    │    ├── __init__.py
│   │    │    ├── router.py   # 회원정보, 프로필, 내정보 등 엔드포인트
│   │    │    └── schemas.py  # 회원 관련 pydantic
│   │    │
│   │    ├── auth/  # "인증" (회원가입, 로그인, JWT 등)
│   │    │    ├── __init__.py
│   │    │    ├── router.py   # 회원가입, 로그인, 로그아웃 엔드포인트 (ACCESS 토큰 재발급 엔드포인트 해야함)
│   │    │    ├── schemas.py  # 인증 관련 pydantic (LogOutResponse 는 src/schemas/security.py 에 구현)
│   │    │    └── service.py  # 인증(회원가입/로그인/로그아웃/JWT 등) 관련 로직 구현
│   │    │
│   │    └── feedback/  # "피드백" 등 기타 주요 도메인
│   │         ├── __init__.py
│   │         ├── router.py
│   │         └── schemas.py
│   │ 
│   ├── core/  # 공통 설정, 미들웨어, JWT, 의존성, 예외 등
│   │    ├── config.py
│   │    ├── security.py
│   │    ├── middleware.py
│   │    └── exceptions.py
│   │ 
│   ├── schemas/  # API 입출력 데이터 구조 정의 (pydantic 클래스)
│   │    └── security.py  # LogOutResponse 구현 (인증 관련 공통 pydantic)
│   │ 
│   ├── models/  # ORM models, DB table 구조 정의...
│   │ 
│   ├── services/  # 각 도메인별 핵심 비즈니스 로직
│   │    ├── user_service.py
│   │    ├── auth_service.py
│   │    └── feedback_service.py
│   │ 
│   ├── utils/  # 공통 함수, 헬퍼, 기타 유틸
│   │ 
│   └── __init__.py
│
├── migrations/
├── tests/
├── scripts/
├── requirements.txt
├── Dockerfile
├── .env
└── README.md
```
