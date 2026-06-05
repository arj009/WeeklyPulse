from fastapi import FastAPI, BackgroundTasks, HTTPException
from typing import Dict, Any
import subprocess
import os

app = FastAPI(title="WeeklyPulse API", description="Railway Backend for WeeklyPulse")

def run_pipeline_task():
    """Background task to run the weekly pulse pipeline."""
    try:
        # Assuming run is fully implemented for headless orchestration
        subprocess.run(["python", "-m", "weeklypulse", "run"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Pipeline failed: {e}")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "WeeklyPulse"}

@app.post("/trigger")
def trigger_run(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger the WeeklyPulse pipeline manually."""
    # In production, require API key authentication here
    background_tasks.add_task(run_pipeline_task)
    return {"status": "accepted", "message": "Pipeline run triggered in background."}
