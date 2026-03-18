import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from app.db.session import SessionLocal
from app.models.index_job import IndexJob

jobs: Dict[str, Dict] = {}


def _save_job(job_id: str, **updates) -> None:
    db = SessionLocal()
    try:
        record = db.get(IndexJob, job_id)
        if record is None:
            record = IndexJob(id=job_id, status=updates.get("status", "created"))
            db.add(record)
        for key, value in updates.items():
            setattr(record, key, value)
        db.commit()
    finally:
        db.close()


def _run_build_command(cmd: list[str], job_id: str) -> None:
    jobs[job_id] = {
        "status": "running",
        "detail": f"command={' '.join(cmd)}",
    }
    _save_job(
        job_id,
        status="running",
        detail=f"command={' '.join(cmd)}",
        started_at=datetime.now(timezone.utc),
    )
    try:
        project_root = Path(__file__).resolve().parents[2]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        if proc.returncode == 0:
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["detail"] = stdout or "Build finished successfully"
            _save_job(
                job_id,
                status="completed",
                detail=jobs[job_id]["detail"],
                return_code=proc.returncode,
                finished_at=datetime.now(timezone.utc),
            )
        else:
            jobs[job_id]["status"] = "failed"
            details = [
                f"returncode={proc.returncode}",
                f"command={' '.join(cmd)}",
            ]
            if stdout:
                details.append(f"stdout:\n{stdout}")
            if stderr:
                details.append(f"stderr:\n{stderr}")
            jobs[job_id]["detail"] = "\n\n".join(details)
            _save_job(
                job_id,
                status="failed",
                detail=jobs[job_id]["detail"],
                return_code=proc.returncode,
                finished_at=datetime.now(timezone.utc),
            )
    except Exception as exc:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["detail"] = str(exc)
        _save_job(
            job_id,
            status="failed",
            detail=str(exc),
            finished_at=datetime.now(timezone.utc),
        )


def start_build(input_path: str, out_csv: str, faiss_out: str, batch: int = 100) -> str:
    job_id = str(uuid.uuid4())
    cmd = [
        sys.executable,
        "scripts/build_embeddings.py",
        "--input",
        input_path,
        "--out-csv",
        out_csv,
        "--faiss-out",
        faiss_out,
        "--batch",
        str(batch),
    ]
    thread = threading.Thread(target=_run_build_command, args=(cmd, job_id), daemon=True)
    thread.start()
    jobs[job_id] = {"status": "started", "detail": None}
    _save_job(job_id, status="started", detail=None)
    return job_id


def get_status(job_id: str) -> Dict:
    in_memory = jobs.get(job_id)
    if in_memory:
        return in_memory

    db = SessionLocal()
    try:
        record = db.get(IndexJob, job_id)
        if record is None:
            return {"status": "not_found", "detail": None}
        return {"status": record.status, "detail": record.detail}
    finally:
        db.close()
