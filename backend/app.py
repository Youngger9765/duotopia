from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Duotopia Backend API", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "duotopia-backend"}

@app.get("/api/health")
def api_health():
    return {"status": "healthy", "version": "1.0.0"}