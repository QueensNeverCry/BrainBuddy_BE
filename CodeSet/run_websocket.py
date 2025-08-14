import multiprocessing
import uvicorn

def RunWS_1():
    uvicorn.run("WebSocket.main:ws_app", host="0.0.0.0", port=9003)
def RunWS_2():
    uvicorn.run("WebSocket.main:ws_app", host="0.0.0.0", port=9004)
def RunWS_3():
    uvicorn.run("WebSocket.main:ws_app", host="0.0.0.0", port=9005)

if __name__ == "__main__":
    # uvicorn.run("WebSocket.main:ws_app",
    #             host="0.0.0.0",
    #             port=9001, # Host 서버 구현시, 9001 로 변경할 것
    #             ssl_keyfile="../Test/SSL/dev.key",
    #             ssl_certfile="../Test/SSL/cert.pem")
    p1 = multiprocessing.Process(target=RunWS_1)
    p2 = multiprocessing.Process(target=RunWS_2)
    p3 = multiprocessing.Process(target=RunWS_3)
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()