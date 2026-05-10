from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse
import uvicorn
import os

from api import router

# Create the FastAPI app instance
app = FastAPI(
    title="FINESE - Smart Data Explorer Pro API",
    description="API for the FINESE data analysis platform",
    version="1.0.0"
)

# Add CORS middleware to allow requests from frontend
# In production, replace "*" with specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to your actual frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Allow credentials to be passed
    allow_credentials=True,
    # Expose headers to the client
    expose_headers=["Access-Control-Allow-Origin"]
)

# Include the main API router
app.include_router(router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to FINESE API - Smart Data Explorer Pro"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "FINESE API"}

# Mount the frontend static files if the directory exists
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "build")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="static")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)