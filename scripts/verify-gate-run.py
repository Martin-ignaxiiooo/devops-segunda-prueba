"""Comprueba los estados reales de los jobs; no habilita ni ejecuta despliegues."""
import json
import os
from pathlib import Path
import urllib.request

def evaluate(jobs):
    results = []
    for scenario in ("success", "quality", "compliance", "recovery"):
        expected = {
            "calidad": "failure" if scenario == "quality" else "success",
            "cumplimiento": "failure" if scenario == "compliance" else "success",
            "despliegue-simulado": "skipped" if scenario in ("quality", "compliance") else "success",
        }
        for role, conclusion in expected.items():
            matches = []
            for job in jobs:
                scope, _, name = job["name"].rpartition(" / ")
                resolved = name == f"{role}-{scenario}"
                # GitHub conserva la expresión literal en algunos jobs omitidos.
                unresolved_skip = (scope == f"escenario-{scenario}"
                                   and name == role + "-${{ inputs.scenario }}"
                                   and job.get("conclusion") == "skipped"
                                   and conclusion == "skipped")
                if resolved or unresolved_skip:
                    matches.append(job)
            actual = matches[0].get("conclusion") if len(matches) == 1 else "missing-or-ambiguous"
            results.append({"scenario": scenario, "job": role, "expected": conclusion, "actual": actual, "passed": actual == conclusion, "url": matches[0]["html_url"] if len(matches) == 1 else None})
    return results


def main():
    api = os.environ.get("GITHUB_API_URL", "https://api.github.com")
    repo = os.environ["GITHUB_REPOSITORY"]
    run = os.environ["GITHUB_RUN_ID"]
    request = urllib.request.Request(
        f"{api}/repos/{repo}/actions/runs/{run}/jobs?per_page=100",
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"], "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        results = evaluate(json.load(response)["jobs"])
    report = {"run_url": f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/{repo}/actions/runs/{run}", "scope": "Jobs reales; despliegue simulado sin AWS", "passed": all(row["passed"] for row in results), "results": results}
    Path("evidence").mkdir(exist_ok=True)
    Path("evidence/gate-suite-results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as output:
        output.write("## Estados reales de los bloqueos\n\n| Caso | Job | Esperado | Observado |\n|---|---|---|---|\n")
        for row in results:
            output.write(f"| {row['scenario']} | {row['job']} | {row['expected']} | {row['actual']} |\n")
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise SystemExit("Los estados reales no coinciden con los bloqueos esperados.")


if __name__ == "__main__":
    main()
