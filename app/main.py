from fastapi import FastAPI, status

from app.api import jobs

app = FastAPI()

app.include_router(jobs.router)


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "ok"}
