#!/usr/bin/env bash
set -euo pipefail
: "${ECR_REGISTRY:?Falta ECR_REGISTRY}"
: "${GITHUB_SHA:?Falta GITHUB_SHA}"
: "${IMAGE_TAG:?Falta IMAGE_TAG}"
: "${DB_PASSWORD:?Falta DB_PASSWORD}"
NAMESPACE="${NAMESPACE:-ep02}"
export NAMESPACE
kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
kubectl create secret generic database-secret --namespace "$NAMESPACE" \
  --from-literal=POSTGRES_PASSWORD="$DB_PASSWORD" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
# Renderiza solo las variables del despliegue, sin modificar expresiones ajenas.
python3 scripts/render-manifests.py > /tmp/ep02-manifests.yaml
kubectl apply -f /tmp/ep02-manifests.yaml
for component in database backend frontend; do
  kubectl rollout status "deployment/ep02-$component" -n "$NAMESPACE" --timeout=600s
done
# Verifica salud y acceso real a la BD a traves del proxy del frontend.
kubectl port-forward -n "$NAMESPACE" service/ep02-frontend 18081:80 >/tmp/ep02-port-forward.log 2>&1 &
forward_pid=$!
trap 'kill "$forward_pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:18081/ >/dev/null; then break; fi
  sleep 2
done
curl --fail --silent http://127.0.0.1:18081/ >/dev/null
curl --fail --silent http://127.0.0.1:18081/ep02 | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),list)'
kubectl annotate deployment -n "$NAMESPACE" ep02-database ep02-backend ep02-frontend \
  "ep02.duoc/commit=$GITHUB_SHA" --overwrite
