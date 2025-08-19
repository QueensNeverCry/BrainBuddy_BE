# WebServer by. Nginx

## Directory

```plain
WebServer/
├─ nginx/                          # Nginx 전용 영역 (configs, 재사용 스니펫)
│  ├─ nginx.conf                   # 메인 설정(main/global)
│  ├─ http.d/                      # HTTP 서버블록(server blocks)
│  │  └─ app.conf                  # 정적 서빙 + 리버스 프록시(proxy_pass)
│  ├─ stream.conf.d/               # (옵션) TCP/UDP(L4) 프록시(stream)
│  │  └─ tcp.conf
│  └─ snippets/                    # 재사용 스니펫(snippets)
│     ├─ gzip.conf                 # gzip(압축, gzip)
│     └─ security.conf             # 보안 헤더(security headers)
│
├─ docker/                         # Docker 빌드 정의(이미지, Dockerfile)
│  └─ Dockerfile                   # 이미지 파일(Dockerfile, build-time)
│
├─ compose/                        # 컨테이너 오케스트레이션(Docker Compose)
│  ├─ docker-compose.dev.yml       # 개발(dev)용(바인드 마운트, bind mount)
│  └─ docker-compose.prod.yml      # 운영(prod)용(불변 이미지, immutable)
│
├─ html/                           # 정적 리소스(static assets)
│  ├─ index.html
│  └─ 404.html
│
├─ certs/
│  └─ dev/                         # 로컬 개발용 인증서(TLS cert for dev)
│
├─ scripts/                        # 자동화 스크립트(automation)
│  ├─ mkcert.sh                    # self-signed cert 생성 스크립트
│  └─ reload.sh                    # nginx -t & 무중단 재적용(reload)
│
├─ logs/                           # (로컬 디버깅용) 파일 로그
├─ .dockerignore                   # 빌드 컨텍스트 정리(.dockerignore)
└─ README.md                       # 최상위 요약
```

- Docker version : 28.3.3
- Docker Compose version v2.38.2-desktop.1
