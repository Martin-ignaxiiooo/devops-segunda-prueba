"""Inspecciona el laboratorio; --create solicita crear la infraestructura revisada.

Usa las credenciales temporales configuradas en el entorno o el perfil AWS.
No elimina stacks ni cambia roles IAM existentes.
"""
import argparse
import json
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

parser = argparse.ArgumentParser()
parser.add_argument("--create", action="store_true")
parser.add_argument("--region", default="us-east-1")
parser.add_argument("--version", default="1.35")
args = parser.parse_args()
session = boto3.Session(region_name=args.region)
identity = session.client("sts").get_caller_identity()
ec2 = session.client("ec2")
eks = session.client("eks")
cloudformation = session.client("cloudformation")
role = session.client("iam").get_role(RoleName="LabRole")["Role"]["Arn"]
versions = eks.describe_cluster_versions()["clusterVersions"]
if not any(v["clusterVersion"] == args.version and v.get("versionStatus") == "STANDARD_SUPPORT" for v in versions):
    raise SystemExit("La version solicitada no esta en soporte estandar. Revisa --version.")
vpcs = ec2.describe_vpcs(Filters=[{"Name": "is-default", "Values": ["true"]}])["Vpcs"]
if len(vpcs) != 1:
    raise SystemExit("No se encontro una unica VPC predeterminada; revisar la red antes de crear.")
subnets = sorted(ec2.describe_subnets(Filters=[{"Name": "vpc-id", "Values": [vpcs[0]["VpcId"]]}])["Subnets"], key=lambda s: s["AvailabilityZone"])
chosen = []
for subnet in subnets:
    if subnet["MapPublicIpOnLaunch"] and subnet["AvailabilityZone"] not in [s["AvailabilityZone"] for s in chosen]:
        chosen.append(subnet)
    if len(chosen) == 2:
        break
if len(chosen) != 2:
    raise SystemExit("Se requieren dos subredes publicas en distintas zonas.")
plan = {"account": identity["Account"], "region": args.region, "cluster": "ep02-devops", "version": args.version, "vpc": vpcs[0]["VpcId"], "subnets": [s["SubnetId"] for s in chosen], "nodes": "1 x t3.medium; maximo 2", "ebs": "20 GiB nodo y 2 GiB PostgreSQL"}
print(json.dumps(plan, indent=2))
body = (Path(__file__).resolve().parent.parent / "infra" / "eks.yaml").read_text(encoding="utf-8")
cloudformation.validate_template(TemplateBody=body)
print("Plantilla validada por CloudFormation.")
if not args.create:
    print("Solo inspeccion. Para crear: agrega --create despues de revisar el plan y el presupuesto.")
    raise SystemExit(0)
try:
    existing = cloudformation.describe_stacks(StackName="ep02-devops")["Stacks"][0]
except ClientError as error:
    if error.response["Error"]["Code"] != "ValidationError" or "does not exist" not in error.response["Error"]["Message"]:
        raise
else:
    raise SystemExit("El stack ya existe (" + existing["StackStatus"] + "). Inspeccionarlo; no se sobrescribe ni elimina.")
parameters = {"ClusterName": "ep02-devops", "KubernetesVersion": args.version, "LabRoleArn": role, "SubnetA": chosen[0]["SubnetId"], "SubnetB": chosen[1]["SubnetId"]}
result = cloudformation.create_stack(StackName="ep02-devops", TemplateBody=body, Parameters=[{"ParameterKey": k, "ParameterValue": v} for k,v in parameters.items()], Tags=[{"Key": "Project", "Value": "ep02-devops"}])
print("Creacion solicitada:", result["StackId"])
print("Revisar eventos con: aws cloudformation describe-stack-events --stack-name ep02-devops")
