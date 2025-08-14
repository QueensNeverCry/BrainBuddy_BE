import multiprocessing
import uvicorn

# keyfile 경로는 테스트 용 keyfile

def RunHTTP():
    uvicorn.run("Application.main:app", host="0.0.0.0", port=9000)

def RunHTTPS():
    uvicorn.run("Application.main:app",
                host="0.0.0.0",
                port=8443,
                ssl_keyfile="../Test/SSL/dev.key",
                ssl_certfile="../Test/SSL/cert.pem")

def RunHTTP_1():
    uvicorn.run("Application.main:app", host="0.0.0.0", port=9000)
def RunHTTP_2():
    uvicorn.run("Application.main:app", host="0.0.0.0", port=9001)
def RunHTTP_3():
    uvicorn.run("Application.main:app", host="0.0.0.0", port=9002)

if __name__ == "__main__":
    # p1 = multiprocessing.Process(target=RunHTTP)
    # p2 = multiprocessing.Process(target=RunHTTPS)
    # p1.start()
    # p2.start()
    # p1.join()
    # p2.join()
    p1 = multiprocessing.Process(target=RunHTTP_1)
    p2 = multiprocessing.Process(target=RunHTTP_2)
    p3 = multiprocessing.Process(target=RunHTTP_3)
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()