from fastapi import FastAPI

from routers import clients, dashboard, filament_types, printers, prints, quotes, spool_models, spools

app = FastAPI(title="Print Manager 3D API")

app.include_router(printers.router, prefix="/api/v1/printers", tags=["printers"])
app.include_router(filament_types.router, prefix="/api/v1/filament-types", tags=["filament-types"])
app.include_router(spool_models.router, prefix="/api/v1/spool-models", tags=["spool-models"])
app.include_router(spools.router, prefix="/api/v1/spools", tags=["spools"])
app.include_router(clients.router, prefix="/api/v1/clients", tags=["clients"])
app.include_router(prints.router, prefix="/api/v1/prints", tags=["prints"])
app.include_router(quotes.router, prefix="/api/v1/quotes", tags=["quotes"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])


@app.get("/health")
def health_check():
    return {"status": "ok"}
