"""Preflight de requests y margen para rollout. No sustituye mediciones de consumo real."""
import argparse
import json
import subprocess


def memory(value):
    for suffix, multiplier in (("Gi", 1024), ("Mi", 1), ("Ki", 1/1024)):
        if value.endswith(suffix):
            return float(value[:-len(suffix)]) * multiplier
    return float(value) / 1024**2


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-grafana", action="store_true")
    args = parser.parse_args()
    nodes = json.loads(subprocess.check_output(["kubectl", "get", "nodes", "-o", "json"]))["items"]
    pods = json.loads(subprocess.check_output(["kubectl", "get", "pods", "-A", "-o", "json"]))["items"]
    free = {}
    for node in nodes:
        if any(c["type"] == "Ready" and c["status"] == "True" for c in node["status"]["conditions"]):
            free[node["metadata"]["name"]] = memory(node["status"]["allocatable"]["memory"]) - 512
    for pod in pods:
        if pod["status"].get("phase") in ("Succeeded", "Failed") or pod["metadata"].get("labels", {}).get("part-of") == "ep3":
            continue
        node = pod["spec"].get("nodeName")
        if node in free:
            regular = sum(memory(c.get("resources", {}).get("requests", {}).get("memory", "0")) for c in pod["spec"].get("containers", []))
            init = max([memory(c.get("resources", {}).get("requests", {}).get("memory", "0")) for c in pod["spec"].get("initContainers", [])] or [0])
            free[node] -= max(regular, init) + memory(pod["spec"].get("overhead", {}).get("memory", "0"))
    # 512 MiB por nodo reservados arriba; 416 MiB adicionales para rollout backend/frontend.
    requests = [512, 512, 256, 416] + ([512] if args.include_grafana else [])
    for request in sorted(requests, reverse=True):
        candidates = [node for node in free if free[node] >= request]
        if not candidates:
            raise SystemExit("Sin margen de memoria para EP3 y rollout; no se añaden nodos. Usa Grafana local o revisa capacidad.")
        selected = max(candidates, key=free.get)
        free[selected] -= request
    print(json.dumps({"request_preflight": "passed", "remaining_MiB_after_margin": free, "limitation": "requests no garantizan picos reales; medir CPU/memoria y OOM"}, indent=2))
