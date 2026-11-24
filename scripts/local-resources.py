"""Mide recursos reales con Docker CLI; termina al detener el proyecto o a las 4 horas."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import time

from importlib.util import spec_from_file_location, module_from_spec

spec = spec_from_file_location("prepare_local", Path(__file__).with_name("prepare-local.py"))
helper = module_from_spec(spec)
spec.loader.exec_module(helper)


def bytes_value(value):
    match = re.fullmatch(r"([\d.]+)(B|kB|KB|MB|GB|KiB|MiB|GiB|TiB)", value.strip())
    if not match:
        raise ValueError("Unidad de memoria no reconocida")
    units = {"B": 1, "kB": 1000, "KB": 1000, "MB": 1000**2, "GB": 1000**3, "KiB": 1024, "MiB": 1024**2, "GiB": 1024**3, "TiB": 1024**4}
    return float(match[1]) * units[match[2]]


def sample(project):
    docker = helper.docker_path()
    listing = subprocess.check_output([docker, "ps", "--filter", f"label=com.docker.compose.project={project}", "--format", '{{.Names}}|{{.Label "com.docker.compose.service"}}'], text=True)
    services = {name: service.removeprefix("ep02-") for line in listing.splitlines() for name, service in [line.split("|", 1)] if service in ("ep02-db", "ep02-backend", "ep02-frontend")}
    if not services:
        return None
    output = subprocess.check_output([docker, "stats", "--no-stream", "--format", "{{json .}}", *services], text=True)
    lines = ["# Docker CLI stats: CPU percent / 100 = cores; memory is rounded by Docker CLI."]
    for line in output.splitlines():
        row = json.loads(line)
        labels = f'service="{services[row["Name"]]}",environment="local"'
        lines += [f'ep3_container_cpu_cores{{{labels}}} {float(row["CPUPerc"].rstrip("%"))/100}', f'ep3_container_memory_bytes{{{labels}}} {bytes_value(row["MemUsage"].split("/")[0])}']
    lines.append(f"ep3_resources_timestamp_seconds{{environment=\"local\"}} {time.time()}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default="ep2-local")
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()
    target = Path(__file__).resolve().parent.parent / ".local/metrics/resources.prom"
    target.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + 4 * 3600
    try:
        while time.monotonic() < deadline:
            data = sample(args.project)
            if data is None:
                break
            temporary = target.with_suffix(".tmp")
            temporary.write_text(data, encoding="utf-8", newline="\n")
            temporary.replace(target)
            if args.once:
                break
            time.sleep(15)
    finally:
        if not args.once:
            target.unlink(missing_ok=True)
