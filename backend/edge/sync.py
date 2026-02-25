import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx
import git
from core import config
from core.database import DBWriteLock, get_db_connection

logger = logging.getLogger(__name__)


class GitHubSyncEngine:
    """
    Sync Engine that treats a GitHub Public Repository as a Serverless Database.
    Now using GitPython for robust git operations.
    """

    def __init__(self):
        self.repo_url = config.SYNC_REPO_URL
        self.local_dir = config.SYNC_LOCAL_DIR
        self.functions_dir = self.local_dir / "functions"
        self._repo: Optional[git.Repo] = None
        self._initialized = False

    def ensure_repo(self) -> bool:
        """Ensures the local cache directory is a valid git repository."""
        if self._initialized and self._repo:
            return True

        self.local_dir.mkdir(parents=True, exist_ok=True)

        try:
            if not (self.local_dir / ".git").exists():
                logger.info(f"Sync: Initializing local hub cache at {self.local_dir}...")
                self._repo = git.Repo.clone_from(self.repo_url, self.local_dir, depth=1)
            else:
                self._repo = git.Repo(self.local_dir)
            
            self._initialized = True
            self.functions_dir.mkdir(parents=True, exist_ok=True)
            return True
        except git.GitCommandError as e:
            logger.error(f"Sync: Git command failed during initialization: {e}")
            return False
        except Exception as e:
            logger.error(f"Sync: Unexpected error during repo init: {e}")
            return False

    def pull(self) -> int:
        """Fetch latest from Hub and merge into local DB."""
        if not self.ensure_repo():
            return 0

        logger.info("Sync: Pulling latest changes from Hub...")
        try:
            origin = self._repo.remotes.origin
            origin.pull()
        except git.GitCommandError as e:
            logger.warning(f"Sync: Pull failed (likely conflict or network error): {e}")
            # Continue to parse whatever we have locally

        count = 0
        if not self.functions_dir.exists():
            return 0

        with DBWriteLock():
            conn = get_db_connection()
            try:
                for json_file in self.functions_dir.glob("*.json"):
                    try:
                        with open(json_file, "r", encoding="utf-8") as f:
                            data = json.load(f)

                        name = data.get("name")
                        if not name:
                            continue

                        # If code or description changed, update
                        res = conn.execute(
                            "SELECT code, description FROM functions WHERE name = ?",
                            (name,),
                        ).fetchone()
                        if (
                            not res
                            or res[0] != data.get("code")
                            or res[1] != data.get("description")
                        ):
                            logger.info(f"Sync: Updating '{name}' (detected changes)")
                            self._upsert_function(conn, data)
                            count += 1
                    except Exception as fe:
                        logger.error(f"Sync: Failed to parse {json_file.name}: {fe}")
                conn.commit()
            finally:
                conn.close()

        logger.info(f"Sync: Pull complete. Updated {count} functions.")
        return count

    def _upsert_function(self, conn, data: Dict):
        """Helper to upsert function data into DuckDB."""
        now = datetime.now().isoformat()

        # Check if exists
        row = conn.execute(
            "SELECT id FROM functions WHERE name = ?", (data["name"],)
        ).fetchone()

        tags_json = json.dumps(data.get("tags", []))
        metadata = {
            "dependencies": data.get("dependencies", []),
            "quality_score": data.get("quality_score", 0),
            "sync_source": "github-hub",
        }
        meta_json = json.dumps(metadata)

        if row:
            fid = row[0]
            conn.execute(
                """
                UPDATE functions SET 
                    code = ?, description = ?, 
                    tags = ?, metadata = ?, updated_at = ?
                WHERE id = ?
            """,
                (
                    data["code"],
                    data.get("description", ""),
                    tags_json,
                    meta_json,
                    now,
                    fid,
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO functions (name, code, description, tags, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data["name"],
                    data["code"],
                    data.get("description", ""),
                    tags_json,
                    meta_json,
                    now,
                    now,
                ),
            )

    def push(self, name: str) -> bool:
        """Export a local function and push to Hub via Mediated API."""
        if not self.ensure_repo():
            return False

        logger.info(f"Sync: Delegating push for '{name}' to Hub...")
        conn = get_db_connection(read_only=False)
        try:
            if not self._export_to_cache(conn, name):
                logger.error(f"Sync: Function '{name}' not found locally.")
                return False

            # Read the exported JSON
            fpath = self.functions_dir / f"{name}.json"
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # POST to Hub (Mediated Push)
            url = f"{config.HUB_URL}/api/v1/sync/push"
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(url, json=data)
                resp.raise_for_status()

            logger.info(f"Sync: Hub successfully accepted '{name}'.")
            return True
        except Exception as e:
            logger.error(f"Sync: Hub-Mediated push failed for '{name}': {e}")
            return False
        finally:
            conn.close()

    def publish_all(self):
        """Export all local functions to the Hub and push via Mediated API."""
        if not self.ensure_repo():
            return False

        logger.info("Sync: Publishing all local functions to Hub via API...")
        conn = get_db_connection(read_only=False)
        try:
            rows = conn.execute(
                "SELECT name FROM functions WHERE status != 'deleted'"
            ).fetchall()
            
            success_count = 0
            for r in rows:
                name = r[0]
                if self.push(name):
                    success_count += 1
            
            logger.info(f"Sync: Bulk publish complete. {success_count}/{len(rows)} functions pushed.")
            return True
        except Exception as e:
            logger.error(f"Sync: Bulk publish failed: {e}")
            return False
        finally:
            conn.close()

    def _export_to_cache(self, conn, name: str) -> bool:
        """Helper to export a single function to the local cache dir."""
        row = conn.execute(
            """
            SELECT name, code, description, tags, metadata, test_cases 
            FROM functions WHERE name = ?
        """,
            (name,),
        ).fetchone()
        if not row:
            return False

        # row indices: 0=name, 1=code, 2=description, 3=tags, 4=metadata, 5=test_cases
        meta = json.loads(row[4]) if row[4] else {}
        data = {
            "name": row[0],
            "code": row[1],
            "description": row[2],
            "tags": json.loads(row[3]) if row[3] else [],
            "test_cases": json.loads(row[5]) if row[5] else [],
            "dependencies": meta.get("dependencies", []),
            "quality_score": meta.get("quality_score", 0),
            "updated_at": datetime.now().isoformat(),
        }

        fpath = self.functions_dir / f"{name}.json"
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def _update_index(self):
        """Generates a lightweight index.json for all functions in the hub."""
        index = []
        for fpath in self.functions_dir.glob("*.json"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                index.append(
                    {
                        "name": data["name"],
                        "description": data.get("description", ""),
                        "tags": data.get("tags", []),
                    }
                )
            except Exception as e:
                logger.error(f"Sync: Failed to parse {fpath.name} for index: {e}")
                continue

        with open(self.local_dir / "index.json", "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)


# Singleton Instance
sync_engine = GitHubSyncEngine()
