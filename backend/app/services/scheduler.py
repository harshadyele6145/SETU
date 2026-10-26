import asyncio
import time
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Callable
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.config import settings
from backend.app.core.database import SessionLocal
from backend.app.models.job import JobExecution
from backend.app.models.base import utc_now
from backend.app.services.alert_service import AlertService

logger = logging.getLogger("setu.scheduler")


class SchedulerService:
    """
    Background Task Scheduler and Persistent Job Execution Ledger.
    Tracks recurring SLA evaluations, document expiry scans, outbox dispatching,
    and missed job catch-up recovery.
    """

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None

    def record_job_start(self, db: Session, job_name: str) -> JobExecution:
        job = JobExecution(
            job_name=job_name,
            started_at=utc_now(),
            status="RUNNING",
            items_processed=0,
            execution_time_ms=0.0
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def record_job_complete(
        self,
        db: Session,
        job_id: str,
        status: str,
        items_processed: int,
        execution_time_ms: float,
        error_message: Optional[str] = None
    ) -> JobExecution:
        job = db.query(JobExecution).filter(JobExecution.id == job_id).first()
        if job:
            job.status = status
            job.completed_at = utc_now()
            job.items_processed = items_processed
            job.execution_time_ms = execution_time_ms
            job.error_message = error_message
            db.commit()
            db.refresh(job)
        return job

    def execute_job(self, job_name: str, runner: Callable[[Session], int]) -> JobExecution:
        """
        Executes a job synchronously within its own database session and persists
        the execution details into the JobExecution ledger.
        """
        db = SessionLocal()
        job = self.record_job_start(db, job_name)
        start_time = time.perf_counter()

        try:
            processed_count = runner(db)
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            completed_job = self.record_job_complete(
                db=db,
                job_id=job.id,
                status="SUCCESS",
                items_processed=processed_count or 0,
                execution_time_ms=round(elapsed_ms, 2)
            )
            logger.info(f"Job {job_name} completed in {elapsed_ms:.2f}ms. Processed: {processed_count}")
            return completed_job
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Job {job_name} failed: {e}", exc_info=True)
            completed_job = self.record_job_complete(
                db=db,
                job_id=job.id,
                status="FAILED",
                items_processed=0,
                execution_time_ms=round(elapsed_ms, 2),
                error_message=str(e)
            )
            return completed_job
        finally:
            db.close()

    def run_sla_and_alert_evaluation(self, db: Session) -> int:
        summary = AlertService.evaluate_and_generate_alerts(db)
        return summary.get("total_candidates_evaluated", 0)

    def run_outbox_dispatch(self, db: Session) -> int:
        result = AlertService.dispatch_notifications(db, max_retries=settings.MAX_NOTIFICATION_RETRIES)
        return result.get("processed", 0)

    def check_missed_jobs_and_recover(self, db: Session) -> List[Dict[str, Any]]:
        """
        Detects if expected jobs missed execution due to system downtime or restart.
        If a job's last successful execution exceeds 2x interval, schedules immediate recovery.
        """
        recovery_log = []
        interval_threshold = timedelta(seconds=max(60, settings.SCHEDULER_INTERVAL_SECONDS * 2))
        now = utc_now()

        tracked_jobs = [
            ("SLA_DEADLINE_EVALUATION", self.run_sla_and_alert_evaluation),
            ("NOTIFICATION_OUTBOX_DISPATCH", self.run_outbox_dispatch),
        ]

        for job_name, runner in tracked_jobs:
            last_run = db.query(JobExecution).filter(
                JobExecution.job_name == job_name,
                JobExecution.status == "SUCCESS"
            ).order_by(desc(JobExecution.completed_at)).first()

            needs_catchup = False
            if not last_run or not last_run.completed_at:
                needs_catchup = True
                reason = "No prior recorded successful execution found."
            else:
                last_time = last_run.completed_at
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                if now - last_time > interval_threshold:
                    needs_catchup = True
                    reason = f"Last execution was {(now - last_time).total_seconds():.0f}s ago (threshold: {interval_threshold.total_seconds()}s)."

            if needs_catchup:
                logger.warning(f"Missed job recovery triggered for {job_name}: {reason}")
                # Execute immediate catch-up run
                recovered_job = self.execute_job(f"{job_name}_CATCHUP_RECOVERY", runner)
                recovery_log.append({
                    "job_name": job_name,
                    "recovered": True,
                    "reason": reason,
                    "execution_id": recovered_job.id if recovered_job else None
                })
            else:
                recovery_log.append({
                    "job_name": job_name,
                    "recovered": False,
                    "reason": "Within expected schedule cadence."
                })

        return recovery_log

    def get_job_history(self, db: Session, limit: int = 50) -> List[JobExecution]:
        return db.query(JobExecution).order_by(desc(JobExecution.started_at)).limit(limit).all()

    async def _scheduler_loop(self):
        logger.info(f"SETU Background Scheduler loop active (interval={settings.SCHEDULER_INTERVAL_SECONDS}s).")
        while self._running and self._stop_event and not self._stop_event.is_set():
            try:
                # 1. Run SLA and alert evaluation
                self.execute_job("SLA_DEADLINE_EVALUATION", self.run_sla_and_alert_evaluation)

                # 2. Run Outbox dispatch
                self.execute_job("NOTIFICATION_OUTBOX_DISPATCH", self.run_outbox_dispatch)
            except Exception as e:
                logger.error(f"Error in scheduler background iteration: {e}")

            try:
                if self._stop_event:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=settings.SCHEDULER_INTERVAL_SECONDS)
                else:
                    await asyncio.sleep(settings.SCHEDULER_INTERVAL_SECONDS)
                break
            except asyncio.TimeoutError:
                continue

    def start(self):
        if self._running:
            return
        self._running = True
        try:
            loop = asyncio.get_running_loop()
            self._stop_event = asyncio.Event()
            self._task = loop.create_task(self._scheduler_loop())
        except RuntimeError:
            # No running event loop (e.g., during synchronous test execution)
            pass

    def stop(self):
        self._running = False
        if self._stop_event:
            self._stop_event.set()
        if self._task and not self._task.done():
            self._task.cancel()


scheduler_service = SchedulerService()
