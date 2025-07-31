import multiprocessing
import uvicorn

# 07.31 기준 keyfile 경로는 테스트 용 keyfile

def RunHTTP():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)

def RunHTTPS():
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8443,
        ssl_keyfile="../Test/SSL/key.pem",
        ssl_certfile="../Test/SSL/cert.pem",
    )

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=RunHTTP)
    p2 = multiprocessing.Process(target=RunHTTPS)
    p1.start()
    p2.start()
    p1.join()
    p2.join()