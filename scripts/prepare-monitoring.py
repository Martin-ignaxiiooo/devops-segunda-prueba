"""Configura el usuario de lectura y Secret en un clúster ya autorizado; nunca crea infraestructura."""
import json
import os
import secrets
import subprocess

namespace = os.environ.get("NAMESPACE", "ep02")
password = secrets.token_hex(24)
admin_password = secrets.token_hex(24)
if os.environ.get("GITHUB_ACTIONS") == "true":
    print("::add-mask::" + password)
    print("::add-mask::" + admin_password)
sql = "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='ep3_monitor') THEN CREATE ROLE ep3_monitor LOGIN; END IF; END $$;\n"
sql += f"ALTER ROLE ep3_monitor PASSWORD '{password}';\nGRANT pg_monitor TO ep3_monitor;\n"
subprocess.run(["kubectl", "exec", "-i", "-n", namespace, "deployment/ep02-database", "--", "psql", "-q", "-v", "ON_ERROR_STOP=1", "-U", "ep02_user", "-d", "ep02"], input=sql, text=True, check=True)
resource = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "ep3-monitoring", "namespace": namespace}, "type": "Opaque", "stringData": {"POSTGRES_DSN": f"postgresql://ep3_monitor:{password}@ep02-database.{namespace}.svc.cluster.local:5432/ep02?sslmode=disable", "GRAFANA_ADMIN_PASSWORD": admin_password}}
subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps(resource), text=True, stdout=subprocess.DEVNULL, check=True)
print("Usuario de monitoreo y Secret actualizados sin exportar credenciales.")
