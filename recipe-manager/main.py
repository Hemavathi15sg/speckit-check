"""
FlavorHub Recipe Manager - Main Application

Minimal FastAPI app for workshop demonstration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

# Create FastAPI app
app = FastAPI(
    title="FlavorHub Recipe Manager",
    description="Legacy recipe search API with bugs for workshop",
    version="2.3.1"
)

# CORS (wide open for workshop)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api", tags=["search"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "FlavorHub Recipe Manager",
        "version": "2.3.1",
        "status": "running",
    
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting FlavorHub Recipe Manager...")
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print()
    print("Known Issue: Search crashes for users without dietary preferences")
    print("Follow workshop exercises to fix using GitHub agents")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
