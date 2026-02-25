import argparse
import subprocess
import sys
import os
from dotenv import load_dotenv

# Load local .env for BYOK deployment
load_dotenv()


def run_command(command, check=True):
    print(f"[EXEC] {' '.join(command)}")
    # On Windows, we need shell=True to find .cmd files like gcloud.cmd
    use_shell = sys.platform == "win32"
    result = subprocess.run(command, capture_output=True, text=True, shell=use_shell)
    if check and result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        sys.exit(result.returncode)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Deploy Function Store MCP to GCP Cloud Run"
    )
    parser.add_argument("--project", help="GCP Project ID", required=False)
    parser.add_argument("--region", default="asia-northeast1", help="GCP Region")
    parser.add_argument("--service", default="function-store-hub", help="Service Name")
    parser.add_argument(
        "--gemini-key", help="Google Gemini API Key (BYOK)", required=False
    )
    parser.add_argument(
        "--setup-only", action="store_true", help="Only setup GCP project and APIs"
    )

    args = parser.parse_args()

    # Priority: Command line arg > .env > None
    gemini_key = args.gemini_key or os.getenv("FS_GEMINI_API_KEY")
    project_id = args.project

    # 1. Project Initialization
    if not project_id:
        # Try to get currently active project
        res = run_command(["gcloud", "config", "get-value", "project"], check=False)
        project_id = res.stdout.strip()

        if not project_id or project_id == "(unset)":
            print(
                "[ERROR] No GCP project ID specified. Please use --project <PROJECT_ID>"
            )
            sys.exit(1)

    print(f"[INFO] Using GCP Project: {project_id}")
    run_command(["gcloud", "config", "set", "project", project_id])

    # 2. Enable APIs
    apis = [
        "run.googleapis.com",
        "cloudbuild.googleapis.com",
        "artifactregistry.googleapis.com",
    ]
    print("[INFO] Enabling necessary APIs...")
    for api in apis:
        run_command(["gcloud", "services", "enable", api])

    if args.setup_only:
        print("[SUCCESS] GCP Project and APIs are set up.")
        return

    # 3. Build and Deploy using Cloud Build
    print("[INFO] Building and deploying to Cloud Run...")

    # Zero-Trust Hub: We do NOT pass any API keys (AI keys).
    # However, we DO pass the GitHub Token for mediated sync.
    # Priority: token_secret.txt > Environment Variable > empty
    github_token = ""
    if os.path.exists("token_secret.txt"):
        with open("token_secret.txt", "r") as f:
            github_token = f.read().strip()
    
    if not github_token:
        github_token = os.getenv("FS_GITHUB_TOKEN", "").strip()
    
    github_repo = os.getenv("FS_GITHUB_STORAGE_REPO", "Ayato-AI-for-Auto/LogicHive-Storage")

    env_vars = [
        "FS_TRANSPORT=http",
        "DATABASE_PATH=:memory:",
        "FS_MODEL_TYPE=gemini",
        f"FS_GITHUB_TOKEN={github_token}",
        f"FS_GITHUB_STORAGE_REPO={github_repo}"
    ]

    deploy_cmd = [
        "gcloud",
        "run",
        "deploy",
        args.service,
        "--source",
        ".",
        "--dockerfile",
        "backend/hub/Dockerfile",
        "--region",
        args.region,
        "--platform",
        "managed",
        "--allow-unauthenticated",
        "--set-env-vars",
        ",".join(env_vars),
        "--quiet",
    ]

    run_command(deploy_cmd)

    print("\n[SUCCESS] Function Store Hub is live!")
    # Get the URL
    res = run_command(
        [
            "gcloud",
            "run",
            "services",
            "describe",
            args.service,
            "--region",
            args.region,
            "--format",
            "value(status.url)",
        ]
    )
    print(f"URL: {res.stdout.strip()}")


if __name__ == "__main__":
    main()
