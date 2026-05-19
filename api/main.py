import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from src.data_loader import load_all, DataStore
from src.scoring_engine import compute_scores
from src.outcome_logger import init_db

load_dotenv()

# App-wide shared state
_store: DataStore = None
_scores = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _store, _scores
    print("[startup] Loading datasets...")
    _store = load_all()
    print("[startup] Computing priority scores...")
    _scores = compute_scores(_store)
    _store.priority_scores = _scores
    print("[startup] Initialising outcome database...")
    init_db()
    print("[startup] Ready.")
    yield


app = FastAPI(
    title="Syngenta Field Co-pilot API",
    version="1.0.0",
    lifespan=lifespan,
)


def get_store() -> DataStore:
    return _store


from api.routers import daily_plan, nba, alerts, outcomes, analytics, rep_profile

app.include_router(rep_profile.router, prefix="/api")
app.include_router(daily_plan.router,  prefix="/api")
app.include_router(nba.router,         prefix="/api")
app.include_router(alerts.router,      prefix="/api")
app.include_router(outcomes.router,    prefix="/api")
app.include_router(analytics.router,   prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "entities_scored": len(_scores) if _scores is not None else 0}
