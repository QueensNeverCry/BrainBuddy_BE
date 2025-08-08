import uvicorn

if __name__ == "__main__":
    uvicorn.run("WebSocket.main:ws_app",
                host="0.0.0.0",
                port=8443, # Host 서버 구현시, 9001 로 변경할 것
                ssl_keyfile="../Test/SSL/dev.key",
                ssl_certfile="../Test/SSL/cert.pem")