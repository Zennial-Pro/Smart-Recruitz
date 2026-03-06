from fastapi import FastAPI
from .api.v1.interview_validation import router as validation_router

app = FastAPI(title="Smart Recruitz POC 5 API")

app.include_router(validation_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to Smart Recruitz API"}
