from fastapi import FastAPI
from src.api.routers import events
from fastapi.middleware.cors import CORSMiddleware

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

app.include_router(events.router, prefix="/api/v1", tags=["Events"])

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "Traffic Intelligence API"}
