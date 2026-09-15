from fastapi import FastAPI

app = FastAPI(
    title="Dan Bufete API",
    version="0.1.0",
)


@app.get("/")
def root():
    return {"message": "Dan Bufete API"}