# src/dan_bufete_api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dan_bufete_api.routes import router

app = FastAPI(
    title="Dan Bufete API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Dan Bufete API"}
