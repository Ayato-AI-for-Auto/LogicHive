import json
import logging
from typing import Dict, Optional
from github import Github
from core.config import GITHUB_TOKEN, GITHUB_STORAGE_REPO

logger = logging.getLogger(__name__)

def push_function_to_github(
    name: str, 
    code: str, 
    description: str = "", 
    tags: list = [], 
    dependencies: list = [],
    metadata: Dict = {}
) -> tuple[bool, str]:
    """
    Pushes a function JSON to the public storage repository (LogicHive-Storage)
    using the Hub's Personal Access Token.
    Returns (True, message) if successful, (False, error_message) otherwise.
    """
    if not GITHUB_TOKEN or not GITHUB_TOKEN.strip():
        logger.error("Hub: GITHUB_TOKEN is not configured. Cannot perform mediated push.")
        return False, "GITHUB_TOKEN is not configured in Hub"

    token = GITHUB_TOKEN.strip()
    repo_name = GITHUB_STORAGE_REPO.strip()

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        
        path = f"functions/{name}.json"
        
        # Prepare the standardized JSON structure
        data = {
            "name": name,
            "description": description,
            "code": code,
            "tags": tags,
            "dependencies": dependencies,
            "metadata": metadata
        }
        content = json.dumps(data, indent=4, ensure_ascii=False)
        
        try:
            # Attempt to find the file to update it
            contents = repo.get_contents(path)
            repo.update_file(
                contents.path,
                f"Update function '{name}' (via LogicHive Hub)",
                content,
                contents.sha
            )
            msg = f"Hub: Successfully updated '{name}' in {GITHUB_STORAGE_REPO}"
            logger.info(msg)
            return True, msg
        except Exception as e_update:
            # File doesn't exist, try to create it
            # But only if it's a 404 (not found). Otherwise, log the error.
            if hasattr(e_update, 'status') and e_update.status == 404:
                repo.create_file(
                    path,
                    f"Register new function '{name}' (via LogicHive Hub)",
                    content
                )
                msg = f"Hub: Successfully created '{name}' in {GITHUB_STORAGE_REPO}"
                logger.info(msg)
                return True, msg
            else:
                logger.error(f"Hub: Failed to update '{name}': {e_update}")
                return False, str(e_update)
        
    except Exception as e:
        logger.error(f"Hub: GitHub API Error when pushing '{name}': {e}")
        return False, str(e)
