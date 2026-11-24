#!/usr/bin/env bash
set -euo pipefail
: "${ECR_REGISTRY:?Falta ECR_REGISTRY}"
: "${GITHUB_SHA:?Falta GITHUB_SHA}"
: "${IMAGE_TAG:?Falta IMAGE_TAG}"
: "${PUBLIC_SUBNETS:?Falta PUBLIC_SUBNETS}"
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
# Solo servicios internos y almacenamiento efímero; no crea EKS/ECR/nodos/volúmenes.
obs_args=()
if [ "${OBSERVABILITY_GRAFANA_IN_CLUSTER:-false}" = "true" ]; then obs_args+=(--include-grafana); fi
python3 scripts/check-capacity.py "${obs_args[@]}"
python3 scripts/prepare-monitoring.py
python3 scripts/render-observability.py --namespace "$NAMESPACE" "${obs_args[@]}" > /tmp/ep3-observability.json
kubectl apply -f /tmp/ep3-observability.json
for component in prometheus loki alloy; do
  kubectl rollout restart "deployment/ep3-$component" -n "$NAMESPACE"
  kubectl rollout status "deployment/ep3-$component" -n "$NAMESPACE" --timeout=300s
done
if [ "${OBSERVABILITY_GRAFANA_IN_CLUSTER:-false}" = "true" ]; then
  kubectl rollout status deployment/ep3-grafana -n "$NAMESPACE" --timeout=300s
fi
# Verifica salud y acceso real a la BD a traves del proxy del frontend.
kubectl port-forward -n "$NAMESPACE" service/ep02-frontend 18081:80 >/tmp/ep02-port-forward.log 2>&1 &
forward_pid=$!
trap 'kill "$forward_pid" 2>/dev/null || true' EXIT
for attempt in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:18081/ >/dev/null; then break; fi
  sleep 2
done
curl --fail --silent http://127.0.0.1:18081/ >/dev/null
curl --fail --silent http://127.0.0.1:18081/api/empresas | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),list)'
kubectl annotate deployment -n "$NAMESPACE" ep02-database ep02-backend ep02-frontend \
  "ep02.duoc/commit=$GITHUB_SHA" --overwrite
# Espera y verifica tambien el acceso publico, ademas de la ruta interna.
public_url=""
for attempt in $(seq 1 90); do
  hostname=$(kubectl get service ep02-frontend -n "$NAMESPACE" -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
  if [ -n "$hostname" ]; then
    public_url="http://$hostname"
    if curl --fail --silent --max-time 10 "$public_url/api/empresas" >/dev/null; then break; fi
  fi
  sleep 5
done
test -n "$public_url"
curl --fail --silent --max-time 30 "$public_url/" >/dev/null
curl --fail --silent --max-time 30 "$public_url/api/empresas" | python3 -c 'import json,sys; assert isinstance(json.load(sys.stdin),list)'
echo "APP_URL=$public_url" >> "$GITHUB_ENV"
printf '### Aplicacion desplegada\n\n%s\n' "$public_url" >> "$GITHUB_STEP_SUMMARY"
