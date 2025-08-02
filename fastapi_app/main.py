from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def hello():
    return {"message": "Hello from FastAPI"}

@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}