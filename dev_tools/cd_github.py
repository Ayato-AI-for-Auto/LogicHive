import subprocess
import sys
import os

def run_command(command, check=True):
    print(f"[EXEC] {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[ERROR] {result.stderr}")
        sys.exit(result.returncode)
    return result

def main():
    print("=== LogicHive Edge CD (GitHub) ===")
    
    # 1. Format & Lint
    print("\n[INFO] Running Ruff formatter/linter...")
    run_command(["uv", "run", "ruff", "format", "."])
    run_command(["uv", "run", "ruff", "check", ".", "--fix"])
    
    # 2. Check for changes
    status = run_command(["git", "status", "--porcelain"])
    if not status.stdout.strip():
        print("\n[INFO] No changes to deploy to GitHub.")
        return

    # 3. Add and commit
    print("\n[INFO] Committing changes...")
    run_command(["git", "add", "."])
    
    # In an automated CI this would be bypassed, but for local CD an interactive prompt is helpful
    try:
        commit_msg = input("Enter commit message (or press Enter for 'chore: automated deployment'): ").strip()
    except EOFError:
        commit_msg = ""
        
    if not commit_msg:
        commit_msg = "chore: automated deployment"
        
    run_command(["git", "commit", "-m", commit_msg])
    
    # 4. Push to origin main
    print(f"\n[INFO] Pushing to GitHub (origin main)...")
    run_command(["git", "push", "origin", "main"])
    
    print("\n[SUCCESS] Edge successfully deployed to GitHub!")

if __name__ == "__main__":
    main()
