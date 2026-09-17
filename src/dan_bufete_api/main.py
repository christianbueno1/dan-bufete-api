# src/dan_bufete_api/main.py

from fastapi import FastAPI

from dan_bufete_api.routes import router

app = FastAPI(
    title="Dan Bufete API",
    version="0.1.0",
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Dan Bufete API"}
