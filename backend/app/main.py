from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.routes import auth, payments, calendar, summary, settings, export, import_statement, statements

settings_config = get_settings()

app = FastAPI(
    title=settings_config.app_name,
    description="Personal Payment Tracking Application",
    version="1.0.0"
)

# CORS middleware - allow all origins for self-hosted deployment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
app.include_router(calendar.router, prefix="/api/calendar", tags=["Calendar"])
app.include_router(summary.router, prefix="/api/summary", tags=["Summary"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])
app.include_router(export.router, prefix="/api/export", tags=["Export"])
app.include_router(import_statement.router, prefix="/api/import", tags=["Import"])
app.include_router(statements.router, prefix="/api/statements", tags=["Statements"])


@app.get("/")
async def root():
    return {"message": "PayTrack API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
