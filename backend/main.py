# backend/main.py - COMPLETELY REPLACE THIS FILE
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.assets import router as assets_router

app = FastAPI(
    title="Blacksmith Atlas API",
    description="Asset Library Management System",
    version="1.0.0"
)

# CORS for frontend - including all possible ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(assets_router)

@app.get("/")
async def root():
    return {
        "message": "Blacksmith Atlas API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}