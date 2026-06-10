from fastapi import FastAPI

from routers import filament_types, printers, spools

app = FastAPI(title="Print Manager 3D API")

app.include_router(printers.router, prefix="/api/v1/printers", tags=["printers"])
app.include_router(filament_types.router, prefix="/api/v1/filament-types", tags=["filament-types"])
app.include_router(spools.router, prefix="/api/v1/spools", tags=["spools"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
