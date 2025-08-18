import multiprocessing
import uvicorn


def RUN_WS() -> None:
    uvicorn.run(app="main:ws_app", host="0.0.0.0", port=9000)


if __name__ == "__main__":
    p = multiprocessing.Process(target=RUN_WS)
    p.start()
    p.join()