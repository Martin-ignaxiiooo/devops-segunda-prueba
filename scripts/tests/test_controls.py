import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
import yaml

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


audit = module("audit-manifests")
render = module("render-observability")
metrics = module("ci-metrics")


class PolicyTests(unittest.TestCase):
    def test_real_observability_resources_pass(self):
        self.assertEqual(audit.audit(render.render(include_grafana=True)["items"]), [])

    def test_privileged_container_blocks(self):
        items = render.render()["items"]
        deployment = next(i for i in items if i["kind"] == "Deployment")
        deployment["spec"]["template"]["spec"]["containers"][0]["securityContext"]["privileged"] = True
        self.assertTrue(audit.audit(items))

    def test_missing_limits_blocks(self):
        items = render.render()["items"]
        deployment = next(i for i in items if i["kind"] == "Deployment")
        del deployment["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]
        self.assertTrue(audit.audit(items))

    def test_prod_deploy_requires_every_control(self):
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci-cd.yml").read_text())
        deploy = workflow["jobs"]["deploy"]
        self.assertEqual(set(deploy["needs"]), {"backend", "frontend", "security", "containers", "configuration"})
        self.assertNotIn("always()", deploy["if"])
        for name in deploy["needs"]:
            job = workflow["jobs"][name]
            self.assertFalse(job.get("continue-on-error", False))
            for step in job["steps"]:
                self.assertFalse(step.get("continue-on-error", False))


class MetricsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.xml = self.folder / "jacoco.xml"
        self.lcov = self.folder / "lcov.info"
        self.xml.write_text('<report><counter type="LINE" covered="9" missed="1"/></report>')
        self.lcov.write_text('SF:example.js\nLF:10\nLH:8\nend_of_record\n')
        for name, report in (("backend", self.xml), ("frontend", self.lcov)):
            (self.folder / (name + ".json")).write_text(json.dumps({"sha": "fixture", "run_id": "unit-test", "attempt": "1", "origin": "local", "report_sha256": metrics.digest(report)}))
        self.args = SimpleNamespace(jacoco=self.xml, lcov=self.lcov, backend_source=self.folder/"backend.json", frontend_source=self.folder/"frontend.json", environment="local", duration=None, output=self.folder/"ci.prom")

    def test_coverage_calculated_from_counters(self):
        metrics.collect(self.args)
        result = json.loads((self.folder/"ci.json").read_text())
        self.assertEqual(result["backend_coverage_ratio"], .9)
        self.assertEqual(result["frontend_coverage_ratio"], .8)
        self.assertNotIn("deployment", result)
        self.assertNotIn(b"\r", (self.folder/"ci.prom").read_bytes())

    def test_changed_report_rejected(self):
        self.xml.write_text('<report/>')
        with self.assertRaises(ValueError):
            metrics.collect(self.args)

    def test_mixed_runs_rejected(self):
        file = self.folder/"frontend.json"
        data = json.loads(file.read_text())
        data["run_id"] = "another-run"
        file.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            metrics.collect(self.args)

    def test_local_run_cannot_be_relabelled_as_eks(self):
        self.args.environment = "eks"
        with self.assertRaises(ValueError):
            metrics.collect(self.args)

    def test_failed_deployment_rejected(self):
        self.args.duration = self.folder/"timing.json"
        self.args.duration.write_text(json.dumps({"sha":"fixture","run_id":"unit-test","attempt":"1","environment":"local","origin":"local","duration_seconds":10,"exit_code":1}))
        with self.assertRaises(ValueError):
            metrics.collect(self.args)


if __name__ == "__main__":
    unittest.main()
