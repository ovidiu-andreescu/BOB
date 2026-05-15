from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import trips

app = FastAPI(title="Mini Travel Planner API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(trips.router, prefix="/api", tags=["trips"])


@app.get("/")
def read_root():
    return {"message": "Mini Travel Planner API"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}

# Made with Bob
