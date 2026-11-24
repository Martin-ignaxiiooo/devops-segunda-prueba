"""Ensayo local real de gates y despliegue SIMULADO. No ejecuta GitHub Actions ni AWS."""
import importlib.util
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parent.parent


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


if __name__ == "__main__":
    docker = load("prepare-local").docker_path()
    folder = ROOT / ".local/evidence/drills"
    folder.mkdir(parents=True, exist_ok=True)
    render = load("render-observability")
    valid = render.render()
    invalid = render.render()
    next(x for x in invalid["items"] if x["kind"] == "Deployment")["spec"]["template"]["spec"]["containers"][0]["securityContext"]["privileged"] = True
    for name, data in (("valid", valid), ("invalid", invalid)):
        (folder / (name + ".json")).write_text(json.dumps(data), encoding="utf-8")
    results = []
    for scenario in ("success", "quality", "compliance", "recovery"):
        case = folder / scenario
        case.mkdir(exist_ok=True)
        mutation = "sed -i 's/isNotNull()/isNull()/' src/test/java/cl/duoc/jv0101/caso01/empresas/OpenApiConfigTest.java; " if scenario == "quality" else ""
        command = mutation + "./gradlew test --tests '*OpenApiConfigTest' --no-daemon --max-workers=1; code=$?; cp -R build/reports build/test-results /evidence/; exit $code"
        with (case/"quality.log").open("wb") as log:
            quality = subprocess.run([docker, "run", "--rm", "--memory=1536m", "--cpus=2", "--mount", f"type=bind,source={case},target=/evidence", "ep3-backend-tests", "sh", "-c", command], stdout=log, stderr=subprocess.STDOUT).returncode
        fixture = "invalid" if scenario == "compliance" else "valid"
        with (case/"compliance.log").open("wb") as log:
            compliance = subprocess.run([docker, "run", "--rm", "--memory=256m", "--mount", f"type=bind,source={ROOT},target=/work,readonly", "-w", "/work", "python:3.12-alpine", "sh", "-c", f"pip install --quiet --target /tmp/checks -r scripts/requirements-validation.txt && PYTHONPATH=/tmp/checks python scripts/audit-manifests.py .local/evidence/drills/{fixture}.json"], stdout=log, stderr=subprocess.STDOUT).returncode
        deployment = "executed-simulation" if quality == 0 and compliance == 0 else "skipped-simulation"
        if deployment == "executed-simulation":
            (case/"simulation.txt").write_text("SIMULACION LOCAL: no se llamó a deploy.sh, kubectl ni AWS.\n", encoding="utf-8")
        expected = (quality != 0 and compliance == 0) if scenario == "quality" else (quality == 0 and compliance != 0) if scenario == "compliance" else quality == compliance == 0
        results.append({"scenario": scenario, "quality_exit": quality, "compliance_exit": compliance, "deployment": deployment, "expected_outcome_observed": expected, "scope": "local; una prueba JUnit y auditoría real; no es un run de GitHub"})
        print(json.dumps(results[-1]), flush=True)
    (folder/"results.json").write_text(json.dumps({"timestamp": time.time(), "results": results}, indent=2), encoding="utf-8")
    if not all(row["expected_outcome_observed"] for row in results):
        raise SystemExit("El ensayo no reprodujo el bloqueo o la recuperación esperados")
