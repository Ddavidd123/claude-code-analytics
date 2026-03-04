"""
Minimal FastAPI service exposing processed telemetry data and insights.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
from pathlib import Path

import pandas as pd
from .data_processor import process_telemetry
from .analytics import generate_insights

app = FastAPI(
    title="Claude Code Telemetry API",
    description="Programmatic access to processed telemetry and analytics",
    version="0.1",
)

# load data on startup (could be refreshed via endpoint)
DATA_DIR = Path("output")
TELEMETRY_FILE = DATA_DIR / "telemetry_logs.jsonl"
EMPLOYEES_FILE = DATA_DIR / "employees.csv"

_events_df: Optional[pd.DataFrame] = None
_users_df: Optional[pd.DataFrame] = None
_insights: Optional[Dict] = None


class EventFilter(BaseModel):
    user_id: Optional[str]
    event_type: Optional[str]
    tool_name: Optional[str]
    model: Optional[str]


@app.on_event("startup")
def load_data():
    global _events_df, _users_df, _insights
    if not TELEMETRY_FILE.exists() or not EMPLOYEES_FILE.exists():
        raise RuntimeError("Telemetry files not found. Generate data before starting API.")
    _events_df, _users_df = process_telemetry(str(TELEMETRY_FILE), str(EMPLOYEES_FILE))
    _insights = generate_insights(_events_df, _users_df)


@app.get("/events", response_model=List[Dict])
def get_events(filter: EventFilter = None):
    """Return raw/normalized events, optionally filtered."""
    df = _events_df.copy()
    if filter is not None:
        if filter.user_id:
            df = df[df["user_id"] == filter.user_id]
        if filter.event_type:
            df = df[df["event_type"] == filter.event_type]
        if filter.tool_name:
            df = df[df["tool_name"] == filter.tool_name]
        if filter.model:
            df = df[df["model"] == filter.model]
    return df.to_dict(orient="records")


@app.get("/users", response_model=List[Dict])
def get_users():
    """Return aggregated user metrics."""
    return _users_df.to_dict(orient="records")


@app.get("/insights", response_model=Dict)
def get_insights():
    """Return precomputed analytics insights."""
    return _insights


@app.post("/refresh")
def refresh_data():
    """Reload raw telemetry and recompute analytics."""
    global _events_df, _users_df, _insights
    _events_df, _users_df = process_telemetry(str(TELEMETRY_FILE), str(EMPLOYEES_FILE))
    _insights = generate_insights(_events_df, _users_df)
    return {"status": "ok"}
