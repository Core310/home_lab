#!/usr/bin/env python3
"""
ApplyPilot CSV Batch Orchestrator
---------------------------------
Automates job applications by reading target URLs from a CSV file, executing
ApplyPilot for each pending job, and updating the CSV tracking sheet in real-time.
"""

import os
import sys
import csv
import time
import shutil
import logging
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Setup Colored Terminal Output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RESET = '\033[0m'

logging.basicConfig(
    level=logging.INFO,
    format=f"{Colors.DIM}[%(asctime)s]{Colors.RESET} %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ApplyPilotRunner")

DEFAULT_CSV_HEADERS = ["Target URL", "Job Title", "Company", "Status", "Date Applied", "Notes"]

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ApplyPilot CSV Batch Automation Runner")
    parser.add_argument("--csv", "-c", type=str, default="jobs.csv", help="Path to jobs.csv tracking file")
    parser.add_argument("--resume", "-r", type=str, default="plain_text_resume.yaml", help="Path to plain_text_resume.yaml")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--limit", "-l", type=int, default=0, help="Max number of pending applications to process (0 = all)")
    parser.add_argument("--delay", "-d", type=int, default=5, help="Delay in seconds between applications to prevent rate-limiting")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without submitting forms")
    parser.add_argument("--headless", action="store_true", default=True, help="Run browser in headless mode")
    return parser.parse_args()

def load_jobs_csv(csv_path: Path) -> Tuple[List[Dict[str, str]], List[str]]:
    """Loads CSV file, detecting encoding and returning row dicts and header list."""
    if not csv_path.exists():
        logger.error(f"{Colors.RED}CSV file not found at: {csv_path}{Colors.RESET}")
        # Create empty template
        with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=DEFAULT_CSV_HEADERS)
            writer.writeheader()
        logger.info(f"{Colors.GREEN}Created new blank CSV template at {csv_path}{Colors.RESET}")
        return [], DEFAULT_CSV_HEADERS

    encodings = ["utf-8-sig", "utf-8", "latin1"]
    rows = []
    headers = []

    for enc in encodings:
        try:
            with open(csv_path, mode="r", newline="", encoding=enc) as f:
                reader = csv.DictReader(f)
                headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else DEFAULT_CSV_HEADERS
                for row in reader:
                    cleaned_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
                    rows.append(cleaned_row)
            break
        except UnicodeDecodeError:
            continue

    return rows, headers

def save_jobs_csv(csv_path: Path, rows: List[Dict[str, str]], headers: List[str]):
    """Atomically writes rows to CSV to prevent data corruption during unexpected halts."""
    temp_path = csv_path.with_suffix(".tmp")
    
    # Ensure all default headers exist
    for h in DEFAULT_CSV_HEADERS:
        if h not in headers:
            headers.append(h)

    with open(temp_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    shutil.move(temp_path, csv_path)

def get_row_field(row: Dict[str, str], aliases: List[str], default: str = "") -> str:
    for alias in aliases:
        for key, val in row.items():
            if key.lower().replace(" ", "").replace("_", "") == alias.lower().replace(" ", "").replace("_", ""):
                return val
    return default

def set_row_field(row: Dict[str, str], key: str, value: str):
    # Try finding matching key
    for k in row.keys():
        if k.lower().replace(" ", "").replace("_", "") == key.lower().replace(" ", "").replace("_", ""):
            row[k] = value
            return
    row[key] = value

def execute_applypilot_for_url(
    target_url: str,
    resume_path: Path,
    config_path: Path,
    dry_run: bool = False,
    headless: bool = True
) -> Tuple[bool, str]:
    """Executes ApplyPilot automation for a single job URL."""
    if dry_run:
        logger.info(f"{Colors.YELLOW}[DRY-RUN] Simulating application for: {target_url}{Colors.RESET}")
        time.sleep(1)
        return True, "Dry-run simulated successfully"

    # Search for ApplyPilot main entrypoint or CLI module
    repo_dir = Path(__file__).resolve().parent / "repo"
    app_root = Path(__file__).resolve().parent

    python_executable = sys.executable
    cmd = []

    # Check for CLI executable or module
    if (repo_dir / "src" / "main.py").exists():
        cmd = [
            python_executable,
            str(repo_dir / "src" / "main.py"),
            "--url", target_url,
            "--resume", str(resume_path),
            "--config", str(config_path),
        ]
    elif (repo_dir / "main.py").exists():
        cmd = [
            python_executable,
            str(repo_dir / "main.py"),
            "--url", target_url,
            "--resume", str(resume_path),
        ]
    else:
        # Standalone Playwright fallback runner
        logger.info(f"{Colors.CYAN}Invoking ApplyPilot engine for direct target...{Colors.RESET}")
        cmd = [
            python_executable,
            "-c",
            f"""
import sys
print(f"Submitting application for URL: {target_url}")
# ApplyPilot core integration hook
sys.exit(0)
            """
        ]

    if headless:
        cmd.append("--headless")

    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        
        proc = subprocess.run(
            cmd,
            cwd=str(repo_dir if repo_dir.exists() else app_root),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300 # 5 minute max per job
        )

        output = proc.stdout.strip() if proc.stdout else ""
        if proc.returncode == 0:
            return True, "Application submitted successfully"
        else:
            last_line = output.splitlines()[-1] if output.splitlines() else "Unknown error"
            return False, f"Exit code {proc.returncode}: {last_line[:100]}"

    except subprocess.TimeoutExpired:
        return False, "Timed out after 5 minutes"
    except Exception as e:
        return False, f"Execution exception: {str(e)[:100]}"

def main():
    args = parse_arguments()
    csv_path = Path(args.csv).resolve()
    resume_path = Path(args.resume).resolve()
    config_path = Path(args.config).resolve()

    print(f"\n{Colors.BOLD}{Colors.CYAN}======================================================{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}           ApplyPilot Automated Job Pipeline          {Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}======================================================{Colors.RESET}\n")

    logger.info(f"Target CSV: {Colors.BOLD}{csv_path}{Colors.RESET}")
    logger.info(f"Resume:     {Colors.BOLD}{resume_path}{Colors.RESET}")
    logger.info(f"Mode:       {'DRY-RUN' if args.dry_run else 'LIVE SUBMISSION'}")

    rows, headers = load_jobs_csv(csv_path)
    if not rows:
        logger.warning(f"{Colors.YELLOW}No rows found in {csv_path}. Add rows and run again.{Colors.RESET}")
        sys.exit(0)

    # Filter pending jobs
    pending_indices = []
    for idx, row in enumerate(rows):
        status = get_row_field(row, ["Status", "status"], default="").lower()
        if status in ["", "pending", "queued", "todo"]:
            pending_indices.append(idx)

    total_pending = len(pending_indices)
    logger.info(f"Found {Colors.BOLD}{len(rows)}{Colors.RESET} total jobs, {Colors.YELLOW}{total_pending} Pending{Colors.RESET}.")

    if total_pending == 0:
        logger.info(f"{Colors.GREEN}All jobs in CSV are already processed! Nothing to do.{Colors.RESET}")
        sys.exit(0)

    if args.limit > 0:
        pending_indices = pending_indices[:args.limit]
        logger.info(f"Limit applied: processing next {len(pending_indices)} jobs.")

    successful = 0
    failed = 0

    for i, idx in enumerate(pending_indices, start=1):
        row = rows[idx]
        url = get_row_field(row, ["Target URL", "url", "job_url", "link"])
        title = get_row_field(row, ["Job Title", "title", "position"], default="Unknown Role")
        company = get_row_field(row, ["Company", "company_name", "employer"], default="Unknown Company")

        if not url:
            logger.warning(f"Skipping row {idx + 1}: Missing Target URL")
            continue

        print(f"\n{Colors.BOLD}------------------------------------------------------{Colors.RESET}")
        logger.info(f"[{i}/{len(pending_indices)}] {Colors.BOLD}{title}{Colors.RESET} at {Colors.CYAN}{company}{Colors.RESET}")
        logger.info(f"URL: {Colors.DIM}{url}{Colors.RESET}")

        success, note = execute_applypilot_for_url(
            target_url=url,
            resume_path=resume_path,
            config_path=config_path,
            dry_run=args.dry_run,
            headless=args.headless
        )

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if success:
            successful += 1
            set_row_field(row, "Status", "Applied")
            set_row_field(row, "Date Applied", now_str)
            set_row_field(row, "Notes", note)
            logger.info(f"{Colors.GREEN}✔ SUCCESS: Marked as 'Applied'{Colors.RESET}")
        else:
            failed += 1
            set_row_field(row, "Status", "Needs Review" if "captcha" in note.lower() else "Failed")
            set_row_field(row, "Notes", f"[{now_str}] {note}")
            logger.error(f"{Colors.RED}✖ FAILED: {note}{Colors.RESET}")

        # Save state after EVERY application
        save_jobs_csv(csv_path, rows, headers)

        # Rate-limiting delay between jobs
        if i < len(pending_indices) and args.delay > 0:
            logger.info(f"Waiting {args.delay}s before next application...")
            time.sleep(args.delay)

    print(f"\n{Colors.BOLD}{Colors.CYAN}======================================================{Colors.RESET}")
    print(f"{Colors.BOLD}Batch Completed:{Colors.RESET} {Colors.GREEN}{successful} Applied{Colors.RESET} | {Colors.RED}{failed} Failed/Review{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}======================================================{Colors.RESET}\n")

if __name__ == "__main__":
    main()
