import multiprocessing
import uvicorn

def RunHTTP():
    uvicorn.run("main:app", host="0.0.0.0", port=8000)

if __name__ == "__main__":
    p1 = multiprocessing.Process(target=RunHTTP)
    p1.start()
    p1.join()