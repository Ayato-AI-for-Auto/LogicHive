import json
import logging
from datetime import datetime

from core.database import get_db_connection
from hub.orchestrator import do_archive_impl

logger = logging.getLogger(__name__)


class RetentionScorer:
    """
    Calculates the 'survival value' of a function based on usage and quality.
    """

    def __init__(self, threshold: float = 0.5, grace_days: int = 14):
        self.threshold = threshold
        self.grace_days = grace_days

    def calculate(self, func_data: dict) -> float:
        # Avoid division by zero
        days_active = self._days_since(func_data.get("created_at")) + 1
        usage_frequency = func_data.get("call_count", 0) / days_active

        # Normalize quality score (0.0 to 1.0)
        quality = func_data.get("quality_score", 50) / 100.0

        # Heuristic: Combination of usage frequency and base quality
        # High usage density or high quality will keep it above threshold.
        # A draft (calls=0, qs=10) will quickly drop below 0.5.
        return (usage_frequency * 5.0) + (quality * 1.0)

    def _days_since(self, date_str: str) -> int:
        if not date_str:
            return 0
        try:
            # Handle both ISO format and simple space format
            date_clean = date_str.replace(" ", "T")
            dt = datetime.fromisoformat(date_clean)
            delta = datetime.now() - dt
            return max(0, delta.days)
        except Exception as e:
            logger.debug(f"Scorer: Date parse failed for '{date_str}': {e}")
            return 0


def run_forget_cleanup() -> str:
    """
    Identifies and removes low-value functions that have not been used recently.
    Target: AI-generated 'trash' or one-off snippets that didn't stick.
    """
    scorer = RetentionScorer()
    logger.info("Forget Logic: Starting cleanup cycle...")

    candidates = []
    conn = get_db_connection(read_only=True)
    try:
        # Load all functions for evaluation
        rows = conn.execute("""
            SELECT name, created_at, last_called_at, call_count, tags, metadata 
            FROM functions 
            WHERE status NOT IN ('deleted', 'archived')
        """).fetchall()

        for r in rows:
            name, created, last_call, calls, tags_json, meta_json = r
            tags = json.loads(tags_json) if tags_json else []

            # Zero-Friction Protection: Explicitly protected tags
            if any(t in ["protected", "core", "stable"] for t in tags):
                continue

            metadata = json.loads(meta_json) if meta_json else {}
            qs = metadata.get("quality_score", 50)

            score = scorer.calculate(
                {"created_at": created, "call_count": calls, "quality_score": qs}
            )

            # Decay: If inactive for more than grace_days AND score is low
            days_inactive = scorer._days_since(last_call or created)

            if days_inactive >= scorer.grace_days and score < scorer.threshold:
                logger.info(
                    f"Forget Logic: Candidate '{name}' (Score: {score:.2f}, Inactive: {days_inactive}d)"
                )
                candidates.append(name)
    except Exception as e:
        import traceback

        err_msg = traceback.format_exc()
        logger.error(f"Forget Logic: Scanning failed: {e}\n{err_msg}")
        return f"ERROR: Scanning failed: {e}"
    finally:
        conn.close()

    # Phase 2: Deletion (outside of the read connection)
    if not candidates:
        return "SUCCESS: No functions identified for removal in this cycle."

    archived_count = 0
    for name in candidates:
        try:
            res = do_archive_impl(name)
            if "SUCCESS" in res:
                archived_count += 1
        except Exception as e:
            logger.error(f"Forget Logic: Failed to archive '{name}': {e}")

    logger.info(f"Forget Logic: Successfully archived {archived_count} functions.")
    return f"SUCCESS: Forget Cycle archived {archived_count} low-value functions."
