# API WorkFlow

## refresh API

### 1. Front 에서 HTTPS 통신으로 Access & Refresh 토큰을 쿠키에 담아 재발급 요청

- credentials: 'include' 옵션을 클라이언트에 꼭 적용해야 쿠키가 누락되지 않습니다...?

### 2. 서버는 요청에서 Access 와 Refresh 토큰 추출

- Access Token을 decode할 때 ignore_exp 옵션을 사용해야 합니다.
- Refresh 도 decode할 때 ignore_exp 옵션을 사용...?

### 3. 토큰 검증

- Access 와 Refresh 를 decode
- Access 와 Refresh 의 claim 유효성
  - 각 토큰 별 claim 들의 존재 여부 및 유효성 확인
    - 결측된 claim 존재 시, 403 FORBIDDEN (공격자임을 안내) 반환
      - iss, aud, typ, alg 등 표준 클레임도 함께 검증해 JWT 헤더·페이로드 위변조를 방지
    - 이때, claim 전부 존재 시, Access 와 Refresh 의 user_id 가 일치하는지 확인
      - 다른 경우 탈취된 것으로 간주하여 Access 는 blacklist 에 등록, Refresh 토큰은 해당 record 가 있다면, revoked = True 설정, 403 FORBIDDEN (탈취자임을 안내) 반환
  - Refresh Token 은 exp 만료 여부 확인
    - 만료된 Refresh 인 경우, 401 UnAuthorized (재로그인으로 안내 필요) 반환
      - 반드시 DB 에서 해당 Refresh Token 의 record 를 revoked = True 설정
- 지금 까지 정상인 경우, Refresh Token 을 DB 에서 상태 조회 하여 revoked 된 토큰인 경우 Access 는 blacklist 에 등록
  - 공격자/탈취자로 간주하여 403 FORBIDDEN (공격자임을 안내) 반환

### 4. 검증 통과시, 기존 Refresh token의 revoked = True 설정

### 5. 새로운 Access Token, Refresh Token 생성 및 새로운 Refresh Token DB에 저장

### 6. cookie 에 새로운 토큰들 등록

### 7. 응답 반환

## 회원탈퇴 API

### 1. Front 에서 HTTPS 통신으로 cookie & request.body = {user_id, user_pw} 전송

### 2. Dependency - get_user_id 로 Access Token 검증 및 Access Token 내의 user_id 추출

### 3. pydantic 모델로 requeset.body 검증

### 4. body 의 user_id 와 AccessToken에서 추출한 user_id 일치 확인

### 5. DB 에서 user_id record 존재 확인 (user.status == "active" 확인 필수)

### 6. DB 에서 해당 record 삭제

### 7. Response 에서 cookie 의 AccessToken, RefreshToken 삭제

### 8. 응답 반환