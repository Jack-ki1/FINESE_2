import json
import os
import threading
import uuid
import traceback
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class JobRecord:
    id: str
    created_at: str
    updated_at: str
    status: str  # queued | running | succeeded | failed
    name: str
    progress: float
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    trace: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InProcessJobQueue:
    """
    Lightweight in-process async job runner:
    - Creates job records in a JSON file on disk
    - Runs each job in a background thread
    - Exposes status/result via readers
    """

    def __init__(self, store_path: str = "instance/jobs"):
        self.store_path = store_path
        os.makedirs(self.store_path, exist_ok=True)

        self._lock = threading.Lock()
        self._threads: Dict[str, threading.Thread] = {}

    def _job_file(self, job_id: str) -> str:
        return os.path.join(self.store_path, f"{job_id}.json")

    def _write_job(self, job: JobRecord) -> None:
        tmp_path = self._job_file(job.id) + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(job.to_dict(), f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, self._job_file(job.id))

    def _read_job(self, job_id: str) -> JobRecord:
        with open(self._job_file(job_id), "r", encoding="utf-8") as f:
            data = json.load(f)
        return JobRecord(**data)

    def create_job(self, name: str) -> JobRecord:
        now = datetime.utcnow().isoformat() + "Z"
        job_id = uuid.uuid4().hex[:12]

        job = JobRecord(
            id=job_id,
            created_at=now,
            updated_at=now,
            status="queued",
            name=name,
            progress=0.0,
            result=None,
            error=None,
            trace=None,
        )

        with self._lock:
            self._write_job(job)

        return job

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        try:
            return self._read_job(job_id)
        except FileNotFoundError:
            return None
        except Exception:
            logger.exception("Failed reading job %s", job_id)
            return None

    def submit(self, job: JobRecord, fn: Callable[[], Dict[str, Any]]) -> str:
        """
        Submit a job record to be executed in the background thread.
        Returns the job id.
        """

        def runner() -> None:
            try:
                with self._lock:
                    job.status = "running"
                    job.updated_at = datetime.utcnow().isoformat() + "Z"
                    job.progress = 0.0
                    job.error = None
                    job.trace = None
                    self._write_job(job)

                # Execute
                res = fn()

                with self._lock:
                    job.status = "succeeded"
                    job.updated_at = datetime.utcnow().isoformat() + "Z"
                    job.progress = 1.0
                    job.result = res
                    job.error = None
                    job.trace = None
                    self._write_job(job)

            except Exception as e:
                trace = traceback.format_exc()
                msg = str(e)

                with self._lock:
                    job.status = "failed"
                    job.updated_at = datetime.utcnow().isoformat() + "Z"
                    job.progress = 1.0
                    job.result = None
                    job.error = msg
                    job.trace = trace
                    self._write_job(job)

        t = threading.Thread(target=runner, daemon=True)
        with self._lock:
            self._threads[job.id] = t

        t.start()
        return job.id


# Global instance
job_queue = InProcessJobQueue()
