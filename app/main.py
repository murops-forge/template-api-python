import logging
import time

from fastapi import FastAPI, Query, Request

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("app")

app = FastAPI(title="app")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    if request.url.path != "/healthz":
        elapsed = (time.perf_counter() - start) * 1000
        log.info("%s %s %d %.1fms", request.method, request.url.path, response.status_code, elapsed)
    return response


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/hello")
def hello(name: str = Query(default="world", max_length=64)) -> dict[str, str]:
    return {"message": f"hello, {name}"}
