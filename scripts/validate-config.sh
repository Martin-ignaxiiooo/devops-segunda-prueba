#!/usr/bin/env bash
set -euo pipefail
export ECR_REGISTRY="${ECR_REGISTRY:-example.invalid}"
export GITHUB_SHA="${GITHUB_SHA:-local-validation}"
export IMAGE_TAG="${IMAGE_TAG:-local-validation}"
export NAMESPACE="${NAMESPACE:-ep02}"
export PUBLIC_SUBNETS="${PUBLIC_SUBNETS:-subnet-local-a,subnet-local-b}"
mkdir -p reports/kubernetes
python3 scripts/render-manifests.py > reports/kubernetes/application.yaml
python3 scripts/render-observability.py --include-grafana > reports/kubernetes/observability.json
python3 -c 'import json,yaml; d=json.load(open("reports/kubernetes/observability.json")); print(yaml.safe_dump_all(d["items"]))' > reports/kubernetes/observability.yaml
python3 -c 'import json; from pathlib import Path; d=json.load(open("reports/kubernetes/observability.json")); c=next(x for x in d["items"] if x["kind"]=="ConfigMap" and x["metadata"]["name"]=="ep3-prometheus-config"); Path("reports/kubernetes/prometheus-kubernetes.yml").write_text(c["data"]["prometheus.yml"])'
python3 scripts/audit-manifests.py reports/kubernetes/application.yaml reports/kubernetes/observability.json
docker run --rm -v "$PWD/reports/kubernetes:/work:ro" ghcr.io/yannh/kubeconform:v0.8.0 \
  -strict -summary -kubernetes-version 1.35.0 /work/application.yaml /work/observability.json
docker run --rm --entrypoint promtool -v "$PWD/observability/prometheus/local.yml:/config.yml:ro" \
  prom/prometheus:v3.16.0 check config /config.yml
docker run --rm --entrypoint promtool -v "$PWD/reports/kubernetes/prometheus-kubernetes.yml:/config.yml:ro" \
  prom/prometheus:v3.16.0 check config --syntax-only /config.yml
docker run --rm -v "$PWD/observability/loki/config.yml:/config.yml:ro" \
  grafana/loki:3.7.10 -config.file=/config.yml -verify-config=true
for config in local kubernetes; do
  docker run --rm -e POSTGRES_DSN=postgresql://validation@localhost/ep02 \
    -e FRONTEND_URL=http://localhost/ -e API_URL=http://localhost/api/empresas \
    -e NAMESPACE=ep02 -e EP3_ENVIRONMENT=local -e COMPOSE_PROJECT=validation \
    -v "$PWD/observability/alloy/common.alloy:/config/common.alloy:ro" \
    -v "$PWD/observability/alloy/$config.alloy:/config/environment.alloy:ro" \
    grafana/alloy:v1.22.0 validate /config
done
