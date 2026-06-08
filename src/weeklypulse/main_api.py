from fastapi import FastAPI, BackgroundTasks, HTTPException
from typing import Dict, Any
import subprocess
import os
import logging

# Configure logging to show in Render logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="WeeklyPulse API", description="Railway Backend for WeeklyPulse")

def run_pipeline_task():
    """Background task to run the weekly pulse pipeline."""
    logger.info("=" * 60)
    logger.info("STARTING WEEKLYPULSE PIPELINE")
    logger.info("=" * 60)
    
    try:
        result = subprocess.run(
            ["python", "-m", "weeklypulse", "run"],
            check=True,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        # Log stdout
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                logger.info(f"PIPELINE: {line}")
        
        # Log stderr
        if result.stderr:
            for line in result.stderr.strip().split('\n'):
                logger.error(f"PIPELINE ERROR: {line}")
        
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except subprocess.TimeoutExpired:
        logger.error("PIPELINE TIMEOUT: Pipeline took more than 10 minutes")
    except subprocess.CalledProcessError as e:
        logger.error(f"PIPELINE FAILED with exit code {e.returncode}")
        if e.stdout:
            for line in e.stdout.strip().split('\n'):
                logger.error(f"PIPELINE OUTPUT: {line}")
        if e.stderr:
            for line in e.stderr.strip().split('\n'):
                logger.error(f"PIPELINE ERROR OUTPUT: {line}")
    except Exception as e:
        logger.error(f"UNEXPECTED ERROR: {e}")
        import traceback
        logger.error(traceback.format_exc())

@app.get("/")
def health_check():
    return {"status": "ok", "service": "WeeklyPulse"}

@app.post("/trigger")
def trigger_run(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """Trigger the WeeklyPulse pipeline manually."""
    # In production, require API key authentication here
    background_tasks.add_task(run_pipeline_task)
    return {"status": "accepted", "message": "Pipeline run triggered in background."}
