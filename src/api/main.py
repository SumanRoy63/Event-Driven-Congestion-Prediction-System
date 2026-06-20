from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from src.api.routers import events, predictions, hotspots, recommendations, ingest, admin
from src.api.services.model_manager import ModelOutOfBoundsException
from fastapi.middleware.cors import CORSMiddleware
from src.api.db.database import engine
from src.api.db import models

# Auto-Initialize the SQLite Database on Startup
# This creates the traffic_events.db file automatically when the server runs
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Traffic Intelligence API",
    description="API for predicting traffic congestion and road closures due to events.",
    version="1.0.0"
)

# Enable CORS for frontend applications
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events.router, prefix="/api/v1", tags=["Events (Combined Workflow)"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(hotspots.router, prefix="/api/v1", tags=["Hotspots"])
app.include_router(recommendations.router, prefix="/api/v1", tags=["Recommendations"])
app.include_router(ingest.router, prefix="/api/v1", tags=["Data Ingestion & Training"])
app.include_router(admin.router, prefix="/api/v1", tags=["Admin & System Management"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Traffic Intelligence API"}

@app.exception_handler(ModelOutOfBoundsException)
async def model_out_of_bounds_handler(request: Request, exc: ModelOutOfBoundsException):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "code": "MODEL_OUT_OF_BOUNDS",
            "message": exc.message
        }
    )

