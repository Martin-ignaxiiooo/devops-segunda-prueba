"""Prepara solo credenciales y directorios locales; reutiliza PostgreSQL existente."""
import os
from pathlib import Path
import secrets
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def docker_path():
    found = shutil.which("docker")
    if found:
        return found
    candidate = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/DockerDesktop/resources/bin/docker.exe"
    if candidate.is_file():
        return str(candidate)
    raise SystemExit("Docker no encontrado; abre una terminal nueva con Docker en PATH.")


if __name__ == "__main__":
    env_file = ROOT / ".env"
    existing = env_file.read_text(encoding="utf-8-sig") if env_file.exists() else ""
    values = dict(line.split("=", 1) for line in existing.splitlines() if "=" in line and not line.startswith("#"))
    additions = []
    for key in ("MONITORING_PASSWORD", "GRAFANA_ADMIN_PASSWORD"):
        if not values.get(key):
            values[key] = secrets.token_hex(24)
            additions.append(f"{key}={values[key]}")
    if additions:
        with env_file.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write("\n" + "\n".join(additions) + "\n")
    (ROOT / ".local/metrics").mkdir(parents=True, exist_ok=True)
    # Solo hex: la clave nunca se incluye en argumentos ni en la salida.
    password = values["MONITORING_PASSWORD"]
    if not all(c in "0123456789abcdef" for c in password):
        raise SystemExit("MONITORING_PASSWORD debe ser hexadecimal.")
    sql = "DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='ep3_monitor') THEN CREATE ROLE ep3_monitor LOGIN; END IF; END $$;\n"
    sql += f"ALTER ROLE ep3_monitor PASSWORD '{password}';\nGRANT pg_monitor TO ep3_monitor;\n"
    subprocess.run([docker_path(), "compose", "-p", os.environ.get("COMPOSE_PROJECT", "ep2-local"), "exec", "-T", "ep02-db", "psql", "-q", "-v", "ON_ERROR_STOP=1", "-U", "ep02_user", "-d", "ep02"], input=sql, text=True, check=True, cwd=ROOT)
    volume = os.environ.get("COMPOSE_PROJECT", "ep2-local") + "_alloy-data"
    subprocess.run([docker_path(), "run", "--rm", "--user", "0", "--entrypoint", "sh", "-v", volume + ":/data", "grafana/alloy:v1.22.0", "-c", "chown 473:473 /data"], check=True)
    print("Credenciales locales preparadas; ep3_monitor tiene pg_monitor, sin privilegios de escritura.")
