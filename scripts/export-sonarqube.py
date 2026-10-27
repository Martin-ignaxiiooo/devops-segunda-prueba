"""Conserva el resultado del servidor temporal sin exportar su token."""
import base64
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

token = os.environ.get("SONAR_TOKEN")
if token:
    destination = Path("reports/sonarqube")
    destination.mkdir(parents=True, exist_ok=True)
    endpoints = {
        "quality-gate": "/api/qualitygates/project_status?projectKey=ep02-devops",
        "measures": "/api/measures/component?component=ep02-devops&metricKeys=coverage,bugs,vulnerabilities,lines_to_cover,uncovered_lines",
        "issues": "/api/issues/search?componentKeys=ep02-devops&ps=100",
    }
    authorization = base64.b64encode((token + ":").encode()).decode()
    for name, endpoint in endpoints.items():
        request = urllib.request.Request(
            "http://localhost:9000" + endpoint,
            headers={"Authorization": "Basic " + authorization},
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                report = json.load(response)
        except (urllib.error.URLError, OSError) as error:
            report = {"export_error": str(error)}
        (destination / (name + ".json")).write_text(
            json.dumps(report, indent=2), encoding="utf-8"
        )
