"""Política interna de laboratorio; no declara certificación ni cumplimiento normativo formal."""
import argparse
import json
from pathlib import Path
import sys
import yaml


def resources(path):
    for doc in yaml.safe_load_all(Path(path).read_text(encoding="utf-8")):
        if doc:
            yield from doc.get("items", []) if doc.get("kind") == "List" else [doc]


def audit(objects):
    errors = []
    for obj in objects:
        name = obj.get("metadata", {}).get("name", "sin nombre")
        kind = obj.get("kind")
        if kind in ("Deployment", "StatefulSet", "DaemonSet"):
            pod = obj.get("spec", {}).get("template", {}).get("spec", {})
            if pod.get("hostNetwork") or pod.get("hostPID"):
                errors.append(f"{name}: acceso al host prohibido para aplicaciones/observabilidad")
            for volume in pod.get("volumes", []):
                if "hostPath" in volume:
                    errors.append(f"{name}: hostPath prohibido")
            for c in pod.get("containers", []) + pod.get("initContainers", []):
                label = name + "/" + c.get("name", "?")
                security = c.get("securityContext", {})
                effective = {**pod.get("securityContext", {}), **security}
                if security.get("privileged") or security.get("allowPrivilegeEscalation") is not False:
                    errors.append(label + ": privilegios no permitidos")
                if effective.get("runAsNonRoot") is not True or effective.get("runAsUser") == 0:
                    errors.append(label + ": requiere usuario no root")
                if "ALL" not in security.get("capabilities", {}).get("drop", []):
                    errors.append(label + ": requiere drop ALL")
                image = c.get("image", "")
                if ":" not in image.rsplit("/", 1)[-1] and "@sha256:" not in image or image.endswith(":latest") or "${" in image:
                    errors.append(label + ": imagen sin versión resuelta")
                for resource in ("requests", "limits"):
                    if not all(c.get("resources", {}).get(resource, {}).get(key) for key in ("cpu", "memory")):
                        errors.append(label + ": faltan CPU/memoria en " + resource)
                if not c.get("readinessProbe") or not c.get("livenessProbe"):
                    errors.append(label + ": faltan sondas")
                for env in c.get("env", []):
                    if any(word in env.get("name", "") for word in ("PASSWORD", "TOKEN", "SECRET", "DSN")) and "value" in env:
                        errors.append(label + ": credencial literal en manifiesto")
        if kind == "Service" and name in ("prometheus", "loki", "alloy", "grafana") and obj.get("spec", {}).get("type", "ClusterIP") != "ClusterIP":
            errors.append(name + ": telemetría debe permanecer interna")
        if kind == "Secret" and (obj.get("data") or obj.get("stringData")):
            errors.append(name + ": no versionar secretos resueltos")
        if kind in ("Role", "ClusterRole"):
            for rule in obj.get("rules", []):
                if "nodes/proxy" in rule.get("resources", []):
                    errors.append(name + ": node proxy no permitido; usar nodes/metrics con TLS")
                if any("*" in rule.get(key, []) for key in ("verbs", "resources", "apiGroups")):
                    errors.append(name + ": RBAC wildcard prohibido")
    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    failures = audit([obj for path in args.files for obj in resources(path)])
    print(json.dumps({"policy": "EP3 laboratorio v1", "passed": not failures, "errors": failures}, ensure_ascii=False, indent=2))
    sys.exit(bool(failures))
