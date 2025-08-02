# BackEnd 디렉토리 구조

```plaintext
BackEnd/
│
├── Application/
│   ├── main.py # Web Application entry point
│   │
│   ├── api/  # Endpoints
│   │    ├── auth/ # Authentication Module (회원가입, 로그인, 로그아웃, 토큰 재발급, 회원탈퇴)
│   │    │    ├── __init__.py
│   │    │    ├── schemas.py    # Pydantic Request/Response Schemas
│   │    │    ├── router.py     # Only!! HTTPS Endpoints !!
│   │    │    ├── service.py    # Business logic for Authentication
│   │    │    ├── repository.py # Authentication-related database operations
│   │    │    └── exceptions.py # Define classes for errors
│   │    │
│   │    └──  dashboard/  # Dashboard Module
│   │         ├── __init__.py
│   │         ├── schemas.py    # Pydantic Request/Response Schemas
│   │         ├── router.py     # Only!! HTTPS Endpoints !!
│   │         ├── service.py    # Business logic for Authentication
│   │         ├── repository.py # Authentication-related database operations
│   │         └── exceptions.py # Define classes for errors in Dashboard
│   │
│   │ 
│   ├── core/  # 공통 설정, JWT(보안), 의존성 등 ...
│   │    ├── config.py
│   │    ├── database.py    # 비동기 DB Session Maker
│   │    ├── deps.py        # 의존성
│   │    ├── security.py    # JWT 로직
│   │    ├── repository.py  # RTR : database operations
│   │    └── exceptions.py  # Define classes for errors
│   │ 
│   │ 
│   ├── models/  # ORM models, DB table 구조
│   │    ├── db.py
│   │    ├── score.py
│   │    ├── security.py
│   │    └── users.py
│   │ 
```
