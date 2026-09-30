from fastapi import FastAPI, status

from app.api import jobs, users
from prometheus_fastapi_instrumentator import Instrumentator
app = FastAPI()

app.include_router(users.router)
app.include_router(jobs.router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}
Instrumentator().instrument(app).expose(app)
