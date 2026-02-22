from fastapi import FastAPI

from .api import router
from .store import init_db

app = FastAPI(title="AI & Science/Tech News Digest API")


@app.on_event("startup")
def startup() -> None:
    init_db()


app.include_router(router)
