"""Prepara un SonarQube efimero de CI y una puerta de calidad obligatoria."""
import base64
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

host = "http://localhost:9000"
for attempt in range(120):
    try:
        with urllib.request.urlopen(host + "/api/system/status", timeout=5) as response:
            if json.load(response)["status"] == "UP":
                break
    except (urllib.error.URLError, TimeoutError, KeyError):
        pass
    time.sleep(5)
else:
    raise SystemExit("SonarQube no inicio en el tiempo permitido; no se omite el control.")

password = "admin"

def post(path, **params):
    auth = base64.b64encode(("admin:" + password).encode()).decode()
    request = urllib.request.Request(host + "/api/" + path, data=urllib.parse.urlencode(params).encode(), headers={"Authorization": "Basic " + auth}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as error:
        # El servidor es local y recien creado; el mensaje no contiene credenciales.
        raise RuntimeError(path + ": " + error.read().decode()) from None

new_password = secrets.token_urlsafe(36) + "Aa1!"
post("users/change_password", login="admin", previousPassword=password, password=new_password)
password = new_password
post("projects/create", project="ep02-devops", name="EP2 DevOps")
post("qualitygates/create", name="EP2 CI")
for metric, operator, threshold in [("bugs", "GT", "0"), ("vulnerabilities", "GT", "0"), ("coverage", "LT", "80")]:
    post("qualitygates/create_condition", gateName="EP2 CI", metric=metric, op=operator, error=threshold)
post("qualitygates/select", gateName="EP2 CI", projectKey="ep02-devops")
token = post("user_tokens/generate", name="ci-" + os.environ.get("GITHUB_RUN_ID", "local"), type="PROJECT_ANALYSIS_TOKEN", projectKey="ep02-devops")["token"]
print("::add-mask::" + token)
with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as output:
    output.write("SONAR_TOKEN=" + token + "\n")
print("SonarQube listo: bloquea bugs, vulnerabilidades y cobertura menor al 80%.")
