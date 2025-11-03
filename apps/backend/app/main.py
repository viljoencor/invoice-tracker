from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .middleware import TraceIdMiddleware
from .routers import auth, clients, invoices, payments, dash

API_PREFIX = "/api/v1"

app = FastAPI(title="Invoice Tracker API", version="0.1.0")

# Trace-id on every response
app.add_middleware(TraceIdMiddleware)

# CORS: be explicit (don't use "*" with credentials)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://localhost",
    "http://127.0.0.1"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # includes Authorization, Content-Type
)

@app.get("/healthz")
async def health():
    return {"status": "ok"}

@app.get("/readiness")
async def readiness():
    return {"ready": True}

# Mount API under /api/v1
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(clients.router, prefix=API_PREFIX)
app.include_router(invoices.router, prefix=API_PREFIX)
app.include_router(payments.router, prefix=API_PREFIX)
app.include_router(dash.router, prefix=API_PREFIX)
