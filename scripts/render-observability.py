"""Genera recursos Kubernetes nativos desde configuraciones versionadas. No aplica recursos."""
import argparse
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent


def render(namespace="ep02", include_grafana=False):
    if not re.fullmatch(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?", namespace) or len(namespace) > 63:
        raise ValueError("Namespace no válido")
    items = []
    def add(kind, name, **fields):
        api = "apps/v1" if kind == "Deployment" else "rbac.authorization.k8s.io/v1" if kind in ("Role", "RoleBinding", "ClusterRole", "ClusterRoleBinding") else "networking.k8s.io/v1" if kind == "NetworkPolicy" else "v1"
        metadata = {"name": name, "labels": {"project": "empresas", "part-of": "ep3"}}
        if kind not in ("ClusterRole", "ClusterRoleBinding"):
            metadata["namespace"] = namespace
        obj = dict(apiVersion=api, kind=kind, metadata=metadata, **fields)
        items.append(obj)
        return obj
    def config(name, data):
        add("ConfigMap", name, data=data)
    def read(path):
        return (ROOT / "observability" / path).read_text(encoding="utf-8")
    prom = f'''global:
  scrape_interval: 30s
scrape_configs:
  - job_name: empresas-backend
    metrics_path: /actuator/prometheus
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names: [{namespace}]
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        regex: ep02-backend
        action: keep
      - source_labels: [__meta_kubernetes_pod_phase]
        regex: Running
        action: keep
      - target_label: environment
        replacement: eks
      - target_label: service
        replacement: backend
  - job_name: kubelet-containers
    scheme: https
    bearer_token_file: /var/run/secrets/kubernetes.io/serviceaccount/token
    tls_config:
      ca_file: /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
    kubernetes_sd_configs:
      - role: node
    relabel_configs:
      - source_labels: [__meta_kubernetes_node_address_InternalIP]
        target_label: __address__
        replacement: $1:10250
      - target_label: __metrics_path__
        replacement: /metrics/cadvisor
      - target_label: environment
        replacement: eks
    metric_relabel_configs:
      - source_labels: [namespace]
        regex: {namespace}
        action: keep
      - source_labels: [__name__]
        regex: container_cpu_usage_seconds_total|container_memory_working_set_bytes
        action: keep
'''
    config("ep3-prometheus-config", {"prometheus.yml": prom})
    config("ep3-loki-config", {"config.yml": read("loki/config.yml")})
    config("ep3-alloy-config", {"common.alloy": read("alloy/common.alloy"), "kubernetes.alloy": read("alloy/kubernetes.alloy")})
    # ep3-ci-metrics se crea/actualiza desde reportes reales; nunca con valores iniciales ficticios.
    add("ServiceAccount", "ep3-monitor")
    add("Role", "ep3-pod-reader", rules=[{"apiGroups": [""], "resources": ["pods", "pods/log", "events"], "verbs": ["get", "list", "watch"]}])
    subject = [{"kind": "ServiceAccount", "name": "ep3-monitor", "namespace": namespace}]
    add("RoleBinding", "ep3-pod-reader", subjects=subject, roleRef={"apiGroup": "rbac.authorization.k8s.io", "kind": "Role", "name": "ep3-pod-reader"})
    cluster_role = "ep3-node-reader-" + namespace
    add("ClusterRole", cluster_role, rules=[{"apiGroups": [""], "resources": ["nodes"], "verbs": ["get", "list", "watch"]}, {"apiGroups": [""], "resources": ["nodes/metrics"], "verbs": ["get"]}])
    add("ClusterRoleBinding", cluster_role, subjects=subject, roleRef={"apiGroup": "rbac.authorization.k8s.io", "kind": "ClusterRole", "name": cluster_role})
    def deployment(name, image, port, args, volumes, mounts, memory, uid, env=None):
        container = {"name": name.removeprefix("ep3-"), "image": image, "args": args, "ports": [{"containerPort": port}], "env": env or [], "securityContext": {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True, "capabilities": {"drop": ["ALL"]}}, "resources": {"requests": {"cpu": "100m", "memory": memory}, "limits": {"cpu": "500m", "memory": "768Mi" if memory == "512Mi" else "384Mi"}}, "volumeMounts": mounts + [{"name": "tmp", "mountPath": "/tmp"}], "readinessProbe": {"httpGet": {"path": "/-/ready" if "prometheus" in name else "/ready" if "loki" in name else "/-/ready" if "alloy" in name else "/api/health", "port": port}, "initialDelaySeconds": 10, "periodSeconds": 10}, "livenessProbe": {"tcpSocket": {"port": port}, "initialDelaySeconds": 60, "periodSeconds": 15}}
        add("Deployment", name, spec={"replicas": 1, "strategy": {"type": "Recreate"}, "selector": {"matchLabels": {"app": name}}, "template": {"metadata": {"labels": {"app": name, "part-of": "ep3"}}, "spec": {"serviceAccountName": "ep3-monitor", "securityContext": {"runAsNonRoot": True, "runAsUser": uid, "fsGroup": uid, "seccompProfile": {"type": "RuntimeDefault"}}, "containers": [container], "volumes": volumes + [{"name": "tmp", "emptyDir": {"sizeLimit": "32Mi"}}]}}})
        add("Service", name.removeprefix("ep3-"), spec={"selector": {"app": name}, "ports": [{"port": port, "targetPort": port}], "type": "ClusterIP"})
    def volume(name, config_name=None, size="1Gi"):
        return {"name": name, **({"configMap": {"name": config_name}} if config_name else {"emptyDir": {"sizeLimit": size}})}
    def mount(name, path, read_only=False):
        return {"name": name, "mountPath": path, "readOnly": read_only}
    deployment("ep3-prometheus", "prom/prometheus:v3.16.0", 9090, ["--config.file=/config/prometheus.yml", "--storage.tsdb.retention.time=48h", "--storage.tsdb.retention.size=512MB", "--web.enable-remote-write-receiver"], [volume("config", "ep3-prometheus-config"), volume("data")], [mount("config", "/config", True), mount("data", "/prometheus")], "512Mi", 65534)
    deployment("ep3-loki", "grafana/loki:3.7.10", 3100, ["-config.file=/config/config.yml"], [volume("config", "ep3-loki-config"), volume("data")], [mount("config", "/config", True), mount("data", "/loki")], "512Mi", 10001)
    alloy_env = [{"name": "NAMESPACE", "value": namespace}, {"name": "EP3_ENVIRONMENT", "value": "eks"}, {"name": "FRONTEND_URL", "value": "http://ep02-frontend/"}, {"name": "API_URL", "value": "http://ep02-frontend/api/empresas"}, {"name": "POSTGRES_DSN", "valueFrom": {"secretKeyRef": {"name": "ep3-monitoring", "key": "POSTGRES_DSN"}}}]
    deployment("ep3-alloy", "grafana/alloy:v1.22.0", 12345, ["run", "--server.http.listen-addr=0.0.0.0:12345", "--storage.path=/var/lib/alloy", "/config"], [volume("config", "ep3-alloy-config"), {"name": "metrics", "configMap": {"name": "ep3-ci-metrics", "optional": True}}, volume("data", size="256Mi")], [mount("config", "/config", True), mount("metrics", "/metrics", True), mount("data", "/var/lib/alloy")], "256Mi", 473, alloy_env)
    # Una única política de entrada para los servicios de observabilidad internos.
    add("NetworkPolicy", "ep3-telemetry-internal", spec={"podSelector": {"matchLabels": {"part-of": "ep3"}}, "policyTypes": ["Ingress"], "ingress": [{"from": [{"podSelector": {"matchLabels": {"part-of": "ep3"}}}], "ports": [{"protocol": "TCP", "port": p} for p in (9090, 3100, 12345, 3000)]}]})
    if include_grafana:
        config("ep3-grafana-sources", {"sources.yml": read("grafana/provisioning/datasources/sources.yml")})
        config("ep3-grafana-provider", {"provider.yml": read("grafana/provisioning/dashboards/provider.yml")})
        config("ep3-grafana-dashboard", {"empresas.json": read("grafana/dashboards/empresas.json")})
        env = [{"name": "PROMETHEUS_URL", "value": "http://prometheus:9090"}, {"name": "LOKI_URL", "value": "http://loki:3100"}, {"name": "GF_USERS_ALLOW_SIGN_UP", "value": "false"}, {"name": "GF_SECURITY_ADMIN_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "ep3-monitoring", "key": "GRAFANA_ADMIN_PASSWORD"}}}]
        deployment("ep3-grafana", "grafana/grafana:13.3.1", 3000, [], [volume("sources", "ep3-grafana-sources"), volume("provider", "ep3-grafana-provider"), volume("dashboard", "ep3-grafana-dashboard"), volume("data")], [mount("sources", "/etc/grafana/provisioning/datasources", True), mount("provider", "/etc/grafana/provisioning/dashboards", True), mount("dashboard", "/var/lib/grafana/dashboards", True), mount("data", "/var/lib/grafana")], "512Mi", 472, env)
    return {"apiVersion": "v1", "kind": "List", "items": items}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--namespace", default="ep02")
    parser.add_argument("--include-grafana", action="store_true")
    args = parser.parse_args()
    print(json.dumps(render(args.namespace, args.include_grafana), indent=2))
