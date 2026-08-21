import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from supabase import Client

logger = logging.getLogger(__name__)

class PipelineStage(ABC):
    """
    Base class for all idempotent pipeline stages in the new artifact-driven architecture.
    """
    
    name: str = "UnnamedStage"
    input_types: List[str] = []
    output_type: str = "UnknownType"
    
    def __init__(self, sb: Client, video_id: str):
        self.sb = sb
        self.video_id = video_id

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> BaseModel:
        """
        Execute the core logic of the stage. 
        Returns a Pydantic artifact model (e.g., PromiseContract, StoryScript).
        """
        pass

    def run(self, inputs: Dict[str, Any]) -> Optional[BaseModel]:
        """
        Wrapper to handle idempotency, retries, and database logging.
        """
        logger.info(f"[{self.name}] Starting stage for video {self.video_id}")
        
        # 1. Idempotency Check
        # Have we already successfully generated this artifact for this video?
        try:
            res = self.sb.table("artifacts").select("*")\
                .eq("video_id", self.video_id)\
                .eq("artifact_type", self.output_type)\
                .order("revision", desc=True)\
                .limit(1).execute()
            
            if res.data:
                logger.info(f"[{self.name}] Artifact {self.output_type} already exists. Skipping execution.")
                # We would ideally reconstruct the Pydantic model here and return it,
                # but for now we just return the raw payload or None to indicate skip.
                return res.data[0].get("payload")
        except Exception as e:
            logger.warning(f"[{self.name}] Failed idempotency check: {e}")

        # 2. Log run start
        run_id = None
        try:
            run_res = self.sb.table("pipeline_runs").insert({
                "video_id": self.video_id,
                "stage_name": self.name,
                "status": "running"
            }).execute()
            if run_res.data:
                run_id = run_res.data[0]["id"]
        except Exception as e:
            logger.warning(f"[{self.name}] Could not create pipeline_runs record: {e}")

        # 3. Execute with basic retries
        max_attempts = 3
        last_error = None
        artifact = None
        
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    logger.info(f"[{self.name}] Attempt {attempt} of {max_attempts}...")
                
                # Core Execution
                artifact = self.execute(inputs)
                
                # Output Validation is implicitly handled if execute() returns a valid Pydantic model
                if not isinstance(artifact, BaseModel):
                    raise ValueError(f"[{self.name}] execute() did not return a valid Pydantic BaseModel.")
                
                logger.info(f"[{self.name}] Execution successful.")
                break
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"[{self.name}] Error on attempt {attempt}: {e}")
                
                if run_id:
                    self._log_event(run_id, "warning", f"Attempt {attempt} failed", {"error": last_error})
                    
                time.sleep(2 ** attempt) # Exponential backoff
                
        # 4. Handle Failure
        if not artifact:
            logger.error(f"[{self.name}] Stage failed after {max_attempts} attempts. Last error: {last_error}")
            if run_id:
                self.sb.table("pipeline_runs").update({
                    "status": "failed",
                    "ended_at": "now()",
                    "error_log": last_error
                }).eq("id", run_id).execute()
            raise RuntimeError(f"Stage {self.name} failed: {last_error}")

        # 5. Persist Artifact
        try:
            # Determine revision (next available)
            rev_res = self.sb.table("artifacts").select("revision")\
                .eq("video_id", self.video_id)\
                .eq("artifact_type", self.output_type)\
                .order("revision", desc=True)\
                .limit(1).execute()
            
            next_rev = 1
            if rev_res.data:
                next_rev = rev_res.data[0]["revision"] + 1

            payload = artifact.model_dump()
            
            art_res = self.sb.table("artifacts").insert({
                "video_id": self.video_id,
                "artifact_type": self.output_type,
                "revision": next_rev,
                "payload": payload
            }).execute()
            
            art_id = None
            if art_res.data:
                art_id = art_res.data[0]["id"]
                
            # Update run record to success
            if run_id:
                self.sb.table("pipeline_runs").update({
                    "status": "success",
                    "ended_at": "now()",
                    "output_artifact_id": art_id
                }).eq("id", run_id).execute()
                
            logger.info(f"[{self.name}] Artifact {self.output_type} (rev {next_rev}) saved to DB.")
            return artifact
            
        except Exception as e:
            logger.error(f"[{self.name}] Failed to save artifact to DB: {e}")
            raise

    def _log_event(self, run_id: str, event_type: str, message: str, details: Dict = None):
        try:
            self.sb.table("pipeline_events").insert({
                "video_id": self.video_id,
                "run_id": run_id,
                "event_type": event_type,
                "message": message,
                "details": details or {}
            }).execute()
        except Exception:
            pass # Non-fatal
