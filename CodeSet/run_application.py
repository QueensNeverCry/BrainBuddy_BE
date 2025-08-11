import multiprocessing
import uvicorn

# keyfile 경로는 테스트 용 keyfile

def RunHTTP():
    uvicorn.run("Application.main:app", host="0.0.0.0", port=9000)

# def RunHTTPS():
#     uvicorn.run("Application.main:app",
#                 host="0.0.0.0",
#                 port=8443,
#                 ssl_keyfile="../Test/SSL/dev.key",
#                 ssl_certfile="../Test/SSL/cert.pem")

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=RunHTTP)
    # p2 = multiprocessing.Process(target=RunHTTPS)
    p1.start()
    # p2.start()
    p1.join()
    # p2.join()
