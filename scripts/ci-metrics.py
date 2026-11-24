"""Extrae métricas de reportes reales y rechaza mezclas de ejecuciones o reportes alterados."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def identity():
    sha = os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
    return {"sha": sha, "run_id": os.environ.get("GITHUB_RUN_ID", os.environ.get("EP3_RUN_ID", "local")), "attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "1"), "origin": "github-actions" if os.environ.get("GITHUB_ACTIONS") == "true" else "local", "working_tree": "modified" if dirty else "clean"}


def collect(args):
    sources = [json.loads(Path(p).read_text(encoding="utf-8")) for p in (args.backend_source, args.frontend_source)]
    for source, report in zip(sources, (args.jacoco, args.lcov)):
        if source["report_sha256"] != digest(report):
            raise ValueError("El reporte no coincide con su procedencia")
    for key in ("sha", "run_id", "attempt", "origin"):
        if sources[0][key] != sources[1][key]:
            raise ValueError("No se pueden mezclar reportes de distintas ejecuciones")
    counter = ET.parse(args.jacoco).getroot().find("counter[@type='LINE']")
    if counter is None:
        raise ValueError("JaCoCo no contiene contador global LINE")
    covered, missed = int(counter.get("covered")), int(counter.get("missed"))
    totals = {"LF": 0, "LH": 0}
    for line in Path(args.lcov).read_text().splitlines():
        if line.startswith(("LF:", "LH:")):
            key, value = line.split(":", 1)
            totals[key] += int(value)
    if min(covered, missed) < 0 or covered + missed <= 0 or totals["LF"] <= 0 or not 0 <= totals["LH"] <= totals["LF"]:
        raise ValueError("No existe cobertura válida; no se inventa un cero")
    record = {key: sources[0][key] for key in ("sha", "run_id", "attempt", "origin")}
    if args.environment == "eks" and record["origin"] != "github-actions":
        raise ValueError("Un reporte local no se publica como despliegue EKS de Actions")
    record.update(environment=args.environment, captured_at=time.time(), backend_coverage_ratio=covered/(covered+missed), frontend_coverage_ratio=totals["LH"]/totals["LF"], backend_report_sha256=digest(args.jacoco), frontend_report_sha256=digest(args.lcov))
    record["working_tree"] = "modified" if any(s.get("working_tree") == "modified" for s in sources) else "clean"
    lines = []
    labels = f'environment="{args.environment}",origin="{record["origin"]}"'
    for component in ("backend", "frontend"):
        lines.append(f'ep3_test_coverage_ratio{{{labels},component="{component}"}} {record[component+"_coverage_ratio"]}')
    if args.duration:
        deployment = json.loads(Path(args.duration).read_text())
        if any(deployment.get(key) != record[key] for key in ("sha", "run_id", "attempt")):
            raise ValueError("La duración pertenece a otra ejecución")
        if deployment["exit_code"] != 0 or deployment["environment"] != args.environment or deployment["origin"] != record["origin"] or deployment["duration_seconds"] < 0:
            raise ValueError("El despliegue no es exitoso o no corresponde al entorno")
        record["deployment"] = deployment
        lines.append(f'ep3_deployment_duration_seconds{{{labels}}} {deployment["duration_seconds"]}')
        lines.append(f'ep3_deployment_timestamp_seconds{{{labels}}} {deployment["finished_at"]}')
    provenance = ",".join(f'{key}="{record[key]}"' for key in ("sha", "run_id", "attempt", "working_tree"))
    lines += [f'ep3_ci_run_info{{{labels},{provenance}}} 1', f'ep3_ci_timestamp_seconds{{{labels}}} {record["captured_at"]}']
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".tmp")
    temporary.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(destination)
    destination.with_suffix(".json").write_text(json.dumps(record, indent=2), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    provenance = commands.add_parser("provenance")
    provenance.add_argument("--report", required=True)
    provenance.add_argument("--output", required=True)
    metrics = commands.add_parser("collect")
    for name in ("jacoco", "lcov", "backend-source", "frontend-source", "output"):
        metrics.add_argument("--" + name, required=True)
    metrics.add_argument("--environment", choices=("local", "eks"), required=True)
    metrics.add_argument("--duration")
    args = parser.parse_args()
    if args.action == "provenance":
        record = identity()
        record.update(report_sha256=digest(args.report), captured_at=time.time())
        Path(args.output).write_text(json.dumps(record, indent=2), encoding="utf-8")
    else:
        collect(args)
