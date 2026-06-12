from fastapi import FastAPI

from routers import clients, filament_types, printers, prints, spool_models, spools

app = FastAPI(title="Print Manager 3D API")

app.include_router(printers.router, prefix="/api/v1/printers", tags=["printers"])
app.include_router(filament_types.router, prefix="/api/v1/filament-types", tags=["filament-types"])
app.include_router(spool_models.router, prefix="/api/v1/spool-models", tags=["spool-models"])
app.include_router(spools.router, prefix="/api/v1/spools", tags=["spools"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(prints.router, prefix="/api/v1/prints", tags=["prints"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
