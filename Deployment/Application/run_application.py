import os
import uvicorn

def _default_workers() -> int:
    try:
        return max(2, (os.cpu_count() or 2) * 2)
    except Exception:
        return 2

if __name__ == "__main__":
    host = os.environ.get("WAS_BIND_HOST")
    port = int(os.environ.get("WAS_BIND_PORT"))
    workers = _default_workers()
    log_level = os.environ.get("WAS_LOG_LEVEL", "info")

    # - proxy_headers: 리버스 프록시 뒤(X-Forwarded-For 등) 헤더 신뢰
    # - forwarded_allow_ips: 프록시의 IP만 신뢰 (동일 인스턴스 Nginx면 127.0.0.1)
    # - timeout-keep-alive: Keep-Alive 튜닝 (기본 5s → 15s 예시)
    # - no-server-header: 서버 식별 헤더 제거 (보안 강화)
    uvicorn.run(app="Application.main:app",
                host=host,
                port=port,
                workers=workers,
                log_level=log_level,
                proxy_headers=True,
                forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS"),
                timeout_keep_alive=int(os.environ.get("WAS_KEEPALIVE_SEC", "15")),
                server_header=False)