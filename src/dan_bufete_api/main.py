# src/dan_bufete_api/main.py

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from dan_bufete_api import models  # noqa: F401  (registra los modelos en Base.metadata)
from dan_bufete_api.database import Base, engine
from dan_bufete_api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Dan Bufete API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/files", StaticFiles(directory="data/uploads"), name="files")
app.include_router(router)


@app.get("/")
def root():
    return {"message": "Dan Bufete API"}