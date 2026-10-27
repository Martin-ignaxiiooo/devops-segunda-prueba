# EP2 - Ingeniería DevOps (DOY0101): Empresas

![CI/CD AWS](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/actions/workflows/ci-cd.yml/badge.svg?branch=main)

## Continuidad con EP1

Esta EP2 automatiza el microservicio **Empresas** desarrollado en [empresas-svc](https://github.com/Martin-ignaxiiooo/empresas-svc), commit [`c3d15ac`](https://github.com/Martin-ignaxiiooo/empresas-svc/tree/c3d15ac9aebdd0522828e05e58c2b2625dda2d76/ms/empresas). El usuario confirmó que corresponde a su EP1.

Los seis archivos Java originales del dominio, controlador, repositorio, servicio, arranque y OpenAPI se conservaron. [ep1-origin.json](ep1-origin.json) registra sus huellas SHA256 con saltos de línea LF. El empaquetado original Maven/Spring Boot 3.3 se integró en el pipeline Gradle/Spring Boot 4.0.9. Las pruebas de EP1 se portaron a las APIs de prueba actuales; se corrigió su codificación UTF8 y una comprobación BDD que comparaba un valor constante en lugar del estado HTTP recibido.

La aplicación anterior de Alumnos se conserva en el historial y en las etiquetas `v1.0.0` y `v1.0.1`. Sus conteos y evidencias no se presentan como resultados de Empresas.

## Aplicación y API

Aplicación AWS Academy: **http://ac4ea9fb00ed74430bff6c139b708c3e-1588630464.us-east-1.elb.amazonaws.com**

La interfaz React administra empresas con `nombre` obligatorio, `industria` y `plan` opcionales. El backend utiliza Java 21, Spring Boot, JPA y Bean Validation. PostgreSQL 16 conserva los datos en un volumen EBS; H2 se utiliza en pruebas.

| Método | Ruta | Respuesta correcta |
|---|---|---|
| GET | `/api/empresas` | 200, lista |
| GET | `/api/empresas/{id}` | 200 o 404 |
| POST | `/api/empresas` | 201; nombre inválido: 400 |
| PUT | `/api/empresas/{id}` | 200 o 404 |
| DELETE | `/api/empresas/{id}` | 204 o 404 |

La especificación se obtiene en `/v3/api-docs`; Swagger UI está disponible en `/swagger-ui/index.html`. La API mantiene CSRF habilitado. Un GET emite la cookie `XSRF-TOKEN`; las escrituras deben conservarla y enviar el encabezado `X-XSRF-TOKEN`. Axios lo hace desde el mismo origen. Solicitudes sin token o con uno inválido reciben 403.

## Ejecución y estructura

- `backend/`: código y pruebas de Empresas de EP1, con configuración de seguridad y salud.
- `frontend/`: interfaz React para el contrato original de Empresas.
- `database/`: PostgreSQL y esquema `empresas`; un volumen nuevo comienza vacío.
- `.github/workflows/`: CI/CD y publicación del grafo Gradle para Dependabot.
- `infra/`: EKS/ECR; `k8s/`: despliegues, PVC, servicios, HPA y políticas.
- `scripts/`: bootstrap AWS, análisis y despliegue comprobado.

Con Docker Desktop operativo, copia `.env.example` a `.env`, configura una contraseña local y ejecuta:

```sh
docker compose up --build --wait
```

La interfaz queda en http://localhost:8081. `docker compose down` detiene los servicios y conserva el volumen. La base de datos y el backend utilizan la red interna.

## Contenedores

El backend se compila con JDK 21 y Gradle en una etapa de build. La imagen final contiene el JAR y JRE 21 Alpine, utiliza UID 10001 y comprueba Actuator. El frontend se compila con Node 22 y su lockfile; la etapa final contiene archivos estáticos y Nginx con UID 101. PostgreSQL utiliza UID 70. Los tres Dockerfiles definen healthchecks y los contextos excluyen dependencias y productos locales.

## Pipeline y trazabilidad

```mermaid
flowchart LR
  C[Push o Pull Request] --> B[JUnit y JaCoCo]
  C --> F[ESLint, Vitest y build]
  B --> S[SonarQube]
  F --> S
  C --> I[Docker y Trivy]
  B --> G{Todos aprobados}
  F --> G
  S --> G
  I --> G
  G -->|main| E[Publicar imágenes verificadas en ECR]
  E --> K[Desplegar EKS y comprobar HTTP]
```

Los PR ejecutan todos los controles. Solo `main` despliega, después de que pasen pruebas, cobertura y seguridad. El [workflow](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/actions/workflows/ci-cd.yml) conserva las ejecuciones y sus artefactos. Los seis controles de calidad son obligatorios para integrar en `main`.

Las imágenes se guardan después de Trivy y se publican en ECR sin reconstruirse. Su etiqueta incorpora SHA completo, número de ejecución e intento; ECR no permite sobrescribir etiquetas. Kubernetes registra `ep02.duoc/commit` y `deploy-evidence` registra SHA, ejecución, clúster y URL. El pipeline verifica la interfaz y consulta Empresas tanto por el servicio como por el balanceador público.

## Pruebas y políticas de calidad

Pruebas incluidas: **23 backend** (JUnit/Mockito y tres escenarios BDD) y **32 frontend**. Cubren el ciclo de vida de Empresas, campos opcionales, validación del nombre, 404, errores de interfaz y CSRF. Los resultados de cada ejecución están en sus artefactos; el badge corresponde a `main`.

```sh
cd backend
./gradlew test jacocoTestCoverageVerification --no-daemon
```

En Windows utiliza `gradlew.bat`, con Java 21. Se conserva el requisito de EP1 de **100% de líneas**, excluyendo únicamente `*Application`, como en su `pom.xml`. El reporte y el control utilizan esa misma selección. También se exigen al menos 80% de instrucciones y ramas.

```sh
cd frontend
npm ci
npm run lint
npm run test:coverage
npm run build
```

Vitest exige al menos 90% en líneas, ramas, funciones y sentencias. CI publica los reportes HTML/XML y LCOV.

## Seguridad y bloqueo

Dependabot revisa Gradle, npm, Docker y Actions. El grafo Gradle se publica en cada cambio del backend; `npm audit --audit-level=high` se ejecuta también sobre dependencias de desarrollo. Las propuestas de actualización se agrupan y deben aprobar los mismos controles antes de integrarse.

Un SonarQube temporal analiza Java y JavaScript con bibliotecas y bytecode. Su puerta exige cobertura global de al menos 80%, cero bugs y cero vulnerabilidades. `sonar.qualitygate.wait=true` espera el resultado y propaga los fallos; no necesita una cuenta Snyk. Los reportes se exportan antes de apagar el servidor y su token temporal no se conserva.

Trivy bloquea vulnerabilidades HIGH o CRITICAL con corrección disponible en las tres imágenes. Ese umbral no equivale a ausencia de todos los hallazgos. La [ejecución bloqueada de seguridad](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/actions/runs/40447441479) se conserva como prueba histórica del bloqueo del pipeline, anterior a la adaptación de Empresas.

Las credenciales se inyectan con GitHub Secrets y Kubernetes Secrets. `.local/`, `.tools/`, `.env` y `secrets.txt` están excluidos de Git. Las políticas de red permiten frontend a backend y backend a PostgreSQL. Las aplicaciones tienen límites de recursos y procesos sin privilegios. La API es una demostración con datos ficticios, HTTP y sin autenticación de usuarios; la disponibilidad pública depende de la sesión del Learner Lab.

## AWS Academy Learner Lab

La infraestructura utiliza el rol `LabRole` existente, dos subredes de la VPC predeterminada en diferentes zonas y EKS 1.35 con nodos AL2023. Antes de crear recursos se comprueba que la versión siga en soporte estándar. La cuenta debe permitir esos servicios y el rol debe conservar los permisos y relaciones de confianza necesarios.

Instala `boto3` y configura las credenciales temporales del Learner Lab mediante el mecanismo de credenciales de AWS. Nunca las pegues en un commit.

```sh
python scripts/bootstrap-aws.py
```

El comando anterior inspecciona y valida; no crea recursos. Después de revisar el plan y presupuesto:

```sh
python scripts/bootstrap-aws.py --create
```

La creación de EKS puede tardar varios minutos. Cuando el nodo esté activo, configura el acceso y el controlador de almacenamiento del laboratorio:

```sh
aws eks wait cluster-active --region us-east-1 --name ep02-devops
aws eks wait nodegroup-active --region us-east-1 --cluster-name ep02-devops --nodegroup-name ep02-nodes
aws eks update-kubeconfig --region us-east-1 --name ep02-devops
kubectl patch deployment ebs-csi-controller -n kube-system --type merge --patch-file infra/ebs-csi-lab-patch.json
kubectl rollout status deployment/ebs-csi-controller -n kube-system --timeout=180s
aws cloudformation wait stack-create-complete --region us-east-1 --stack-name ep02-devops
```

Estas operaciones requieren AWS CLI y kubectl. Configura `EKS_CLUSTER_NAME=ep02-devops` como variable de Actions y estos secretos:

| Secreto | Uso |
|---|---|
| `AWS_ACCESS_KEY_ID` | Credencial temporal del laboratorio |
| `AWS_SECRET_ACCESS_KEY` | Credencial temporal del laboratorio |
| `AWS_SESSION_TOKEN` | Token temporal del laboratorio |
| `DB_PASSWORD` | Contraseña de PostgreSQL |

Renueva los tres valores AWS al cambiar la sesión. Un token vencido debe producir un fallo de autenticación; no se omite la seguridad para continuar.

El frontend se expone por un servicio `LoadBalancer`; el pipeline espera su dirección pública y verifica tanto la interfaz como `/ep02`. La URL queda en el resumen y en `deploy-evidence`. El balanceador distribuye tráfico entre zonas mediante la anotación `aws-load-balancer-cross-zone-load-balancing-enabled`, también cuando el laboratorio utiliza un único nodo. PostgreSQL y el backend conservan servicios internos. Como alternativa de diagnóstico desde una terminal con acceso al clúster:

```sh
aws eks update-kubeconfig --region us-east-1 --name ep02-devops
kubectl port-forward -n ep02 service/ep02-frontend 8081:80
```

Abre http://localhost:8081. El pipeline comprueba HTTP y la consulta de alumnos mediante este mismo servicio.

## Orquestación y datos

PostgreSQL almacena la tabla `empresas` y mantiene una réplica y un volumen EBS gp3 de 2 GiB. Su política de recuperación `Retain` conserva el volumen ante la eliminación del PVC; debe inventariarse al limpiar el laboratorio porque sigue consumiendo almacenamiento.

El backend inicia con dos réplicas y un HPA de dos a tres, al 70% de CPU. El frontend inicia con dos réplicas. Todos tienen límites de memoria y CPU, sondas de salud y reinicio gestionado por Kubernetes. El clúster inicia con un nodo; el máximo de dos del nodegroup es un límite de tamaño, no un autoscaler de nodos. El HPA requiere Metrics Server. La persistencia requiere EBS CSI. El parche `infra/ebs-csi-lab-patch.json` configura una réplica del controlador EBS en la red del nodo, para que utilice el rol EC2 `LabRole` en este laboratorio sin crear roles IAM. Se limita al componente de almacenamiento; las aplicaciones conservan la red normal de pods. El pipeline aplica y comprueba este ajuste antes del despliegue.

EKS y el almacenamiento pueden generar cargos aunque la sesión del laboratorio termine. La eliminación debe planificarse después de registrar las evidencias y conservar los datos necesarios. Este repositorio no ejecuta borrados automáticos sobre la cuenta.

## Evidencias de evaluación

| Indicador | Evidencia |
|---|---|
| IE1 | Tres Dockerfiles, builds y reportes Trivy |
| IE2 | Pruebas de Empresas de EP1, controles JaCoCo/Vitest y reportes CI |
| IE3 | Dependabot, SonarQube, Trivy, CSRF, Secret, límites y HPA |
| IE4 | Pipeline ECR/EKS, etiquetas SHA, anotaciones y `deploy-evidence` |
| IE5 | Kubernetes, réplicas, probes, PVC y métricas del HPA |

Las verificaciones funcionales y de escalado se conservan como evidencias de la versión correspondiente. No se atribuyen a Empresas las capturas antiguas de Alumnos.

## Uso de IA

Se utilizó Codex de OpenAI como apoyo para adaptar el pipeline, actualizar dependencias, portar pruebas y preparar la interfaz de Empresas. El equipo debe revisar y validar el contenido, así como declarar y citar el uso final conforme a la [orientación de Duoc](https://bibliotecas.duoc.cl/ia).

## Integrantes

Integrantes identificados en el repositorio de EP1:

- Martin Peña
- Benjamin Yantzen

El equipo debe confirmar que la pareja de EP2 es la misma.

## Conclusiones, justificaciones y reflexiones individuales

Pendiente: cada integrante debe redactar personalmente sus conclusiones, justificaciones técnicas y reflexión sobre aprendizaje y contribución, sin apoyo de IA, conforme a la pauta. No se reutilizan automáticamente las reflexiones de EP1.
