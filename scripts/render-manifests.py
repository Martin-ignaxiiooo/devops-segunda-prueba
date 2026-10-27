"""Renderiza manifiestos desde variables verificadas, sin incluir secretos."""
import os
from pathlib import Path
from string import Template

root = Path(__file__).resolve().parent.parent
values = {key: os.environ[key] for key in ("ECR_REGISTRY", "GITHUB_SHA", "NAMESPACE", "IMAGE_TAG", "PUBLIC_SUBNETS")}
for path in sorted((root / "k8s").glob("*.yaml")):
    print("---")
    print(Template(path.read_text(encoding="utf-8")).substitute(values))
