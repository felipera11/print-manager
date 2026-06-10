from fastapi import FastAPI

app = FastAPI(title="Print Manager 3D API")


@app.get("/health")
def health_check():
    return {"status": "ok"}
