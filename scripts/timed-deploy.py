"""Ejecuta un despliegue y registra su duración real incluso si falla."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument("--environment", choices=("local", "eks"), required=True)
parser.add_argument("--output", required=True)
parser.add_argument("command", nargs=argparse.REMAINDER)
args = parser.parse_args()
command = args.command[1:] if args.command[:1] == ["--"] else args.command
if not command:
    parser.error("Se requiere un comando real de despliegue")
started = time.time()
monotonic_start = time.monotonic()
result = subprocess.run(command, check=False)
record = {"environment": args.environment, "origin": "github-actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local", "started_at": started, "finished_at": time.time(), "duration_seconds": time.monotonic() - monotonic_start, "exit_code": result.returncode}
record.update(sha=os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(), run_id=os.environ.get("GITHUB_RUN_ID", os.environ.get("EP3_RUN_ID", "local")), attempt=os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
destination = Path(args.output)
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_text(json.dumps(record, indent=2), encoding="utf-8")
sys.exit(result.returncode)
