# EP3: operación y verificación

Base EP2: `14cf575`. Rama de trabajo: `ep3/observabilidad`. El estado de publicación y los resultados del cierre se registran en `CIERRE_EP3.md`. No se han autorizado merges a main ni recursos AWS adicionales.

## Arranque local

Desde la raíz del repositorio, con Docker Desktop Linux iniciado:

```powershell
docker compose -p ep2-local up -d --build ep02-db
python scripts/prepare-local.py
docker compose -p ep2-local -f compose.yaml -f observability/compose.observability.yaml up -d --build --wait
python scripts/local-resources.py
```

La última orden permanece en la terminal, recolecta Docker stats cada 15 segundos y termina con Ctrl+C, al detener EP2 o después de cuatro horas. No instala un servicio de Windows. Sus métricas son CPU de contenedor (porcentaje Docker / 100) y memoria redondeada por Docker CLI. No representan CPU/memoria del computador completo. Si se detiene, los paneles descartan muestras de recursos de más de 60 segundos.

- Empresas: http://127.0.0.1:8081
- Grafana: http://127.0.0.1:3000/d/empresas-ep3 (lectura anónima solo en loopback).
- Prometheus: http://127.0.0.1:9090
- Loki: http://127.0.0.1:3100/ready
- Administración Grafana: usuario `admin`; contraseña generada en `.env`, nunca en Git ni capturas.

Detener conservando los volúmenes:

```powershell
docker compose -p ep2-local -f compose.yaml -f observability/compose.observability.yaml stop
```

No usar `down -v` para detener: elimina los datos. No habilitar arranque automático de Docker ni Kubernetes para esta validación.

## Instrumentación y fuentes

| Requisito | Fuente / implementación |
|---|---|
| Solicitudes, 4xx/5xx, p95 | Actuator + registro Micrometer Prometheus; histogramas HTTP. Scrape de cada backend. |
| CPU/memoria local | `local-resources.py` -> archivo atómico LF -> Alloy textfile -> Prometheus. |
| CPU/memoria EKS | Kubelet `/metrics/cadvisor`, ServiceAccount con `nodes/metrics`, TLS verificado. |
| Disponibilidad | Sondas Alloy a interfaz y API; promedio de muestras observadas. No atribuye disponibilidad a huecos sin recolección. |
| PostgreSQL | Exportador integrado en Alloy con usuario `ep3_monitor` y `pg_monitor`. |
| Logs | Alloy Docker local / API Kubernetes; backend, frontend y PostgreSQL -> Loki, retención 24h. |
| Cobertura | XML global JaCoCo y LCOV, con hash y procedencia del mismo SHA/run/intento. |
| Duración | `timed-deploy.py`: aplicación/verificación reales; no duración total de CI ni tiempo de cola. |

`X-Request-ID` lo genera Nginx, se propaga a Tomcat y vuelve al cliente. Ambos access logs incluyen el mismo identificador. `%D` en el Tomcat actual se registra como microsegundos. No se registran query strings, cuerpos, cookies ni encabezados de autenticación. Alloy descarta líneas conocidas con credenciales. Esto es correlación de logs, no spans de trazado distribuido. Los logs Nginx no capturan errores JavaScript del navegador.

Actuator se consulta dentro de la red Docker/Kubernetes; Nginx devuelve 404 para `/actuator`. CSRF y los umbrales EP2 siguen activos. Los filesystems raíz son de solo lectura, con volúmenes limitados para datos y temporales.

Alloy local necesita el socket Docker para descubrir/leer logs. Aunque el mount sea `ro`, el socket concede acceso privilegiado al motor; usar únicamente la imagen versionada en este laboratorio. En Kubernetes no se monta el socket ni se usan contenedores privilegiados: se utiliza RBAC de lectura.

## Métricas CI: datos ausentes y procedencia

Los jobs generan `provenance.json` junto a los reportes. `ci-metrics.py collect` comprueba hash, SHA, run e intento; rechaza mezclas y reportes locales etiquetados como EKS. No genera duración si no existe un despliegue verificado. `working_tree=modified` identifica la implementación local sin commit.

Tras un despliegue exitoso, el job crea/actualiza `ep3-ci-metrics`. Alloy lo monta como directorio, sin `subPath`, y publica el último snapshot. La actualización del volumen es eventual. Los artefactos conservan el registro por ejecución; Prometheus conserva el historial observado, no reconstruye los períodos en que estuvo apagado. Los PR/fallos no sobrescriben la cobertura de la versión desplegada. Un panel sin telemetría muestra **Sin datos**.

Para publicar resultados locales, ejecutar `provenance` sobre cada reporte real y luego `collect --environment local`; consultar `python scripts/ci-metrics.py --help`. No reutilizar un reporte de otro cambio de código sin ejecutar sus pruebas.

## Validación y bloqueos

`scripts/validate-config.sh` renderiza, audita, valida esquemas Kubernetes 1.35 y comprueba Prometheus, Loki y Alloy local/Kubernetes. Usa kubeconform 0.8.0. PyYAML 6.0.3 es solo dependencia de validación; no se instala en las aplicaciones. Trivy config bloquea HIGH/CRITICAL sin excepciones generales. Los escaneos de imágenes, SonarQube, pruebas y cobertura de EP2 se conservan.

```sh
python -m pip install -r scripts/requirements-validation.txt  # entorno de validación aislado
python -m unittest discover -s scripts/tests -v
bash scripts/validate-config.sh
```

En este computador se ejecutaron los parsers/validadores en contenedores temporales, sin instalación global. No ejecutar `pip install` globalmente si no se desea modificar Python local.

`configuration` es dependencia obligatoria de `deploy`. Guardar reportes con `always()` no habilita despliegues después de fallos. La política interna rechaza privilegios, node proxy, imágenes sin versión, falta de recursos/probes y secretos literales; no equivale a una certificación normativa.

Ensayo local, con imágenes de pruebas construidas desde el código actual:

```sh
docker build --target build -t ep3-backend-tests backend
python scripts/local-gate-drill.py
```

El ensayo usa una prueba JUnit real y el auditor real; muta únicamente un contenedor/fixture descartable. Su job de despliegue es **simulado**, no es GitHub Actions ni EKS. `.github/workflows/gate-drill.yml` prepara la demostración equivalente con runs reales de Actions, incluyendo jobs omitidos. Requiere publicar/ejecutar con autorización: success -> quality -> compliance -> success (recuperación). Nunca aplicar el fixture inválido a un clúster.

`gate-suite.yml` ejecuta esos cuatro escenarios al publicar `ep3/observabilidad`; reutiliza `gate-drill.yml`. Las fallas de JUnit y cumplimiento son intencionales: los jobs correspondientes deben fallar y el despliegue simulado debe quedar omitido. El job `verify` consulta los estados reales de GitHub y contrasta doce resultados esperados. No sustituye los controles del pipeline principal ni permite desplegar después de fallos. La suite puede figurar fallida por contener casos negativos; revisar también el resultado del verificador y su artefacto.

El pipeline principal también se ejecuta al publicar esta rama. Su job AWS mantiene la condición exclusiva de `main`, por lo que comprobar CI en `ep3/observabilidad` no despliega AWS. `dependency-graph.yml`, ya existente en main, permite ejecución manual sobre esta rama después de publicarla.

## EKS: preparado, no ejecutado

`deploy.sh` conserva la publicación de imágenes verificadas y las comprobaciones de Empresas. Añade preflight de memoria, usuario de monitoreo, configuraciones y rollouts de Prometheus/Loki/Alloy. No crea nodos, balanceadores de observabilidad ni volúmenes EBS. Los datos de observabilidad usan `emptyDir` y se pierden al reemplazar el pod. Los artefactos y configuraciones versionadas permiten reconstrucción, no recuperación del historial perdido.

Grafana queda local por defecto. `OBSERVABILITY_GRAFANA_IN_CLUSTER=true` solo debe habilitarse después de revisar capacidad. El preflight de requests reserva margen, pero no demuestra suficiencia de CPU, créditos t3 ni picos reales. No aumenta nodos automáticamente.

Antes de autorizar un despliegue, verificar acceso a `nodes/metrics`, conectividad privada al kubelet y confianza de sus certificados. Si un target falla por TLS, corregir CA/certificado; **no desactivar la verificación**. La configuración de kubelet todavía no está probada en AWS.

Para Grafana local con datos EKS, después de autorizar acceso:

```sh
kubectl -n ep02 port-forward service/prometheus 19090:9090
kubectl -n ep02 port-forward service/loki 13100:3100
docker compose -p ep2-local -f compose.yaml -f observability/compose.observability.yaml run --rm --no-deps -p 127.0.0.1:3001:3000 -e PROMETHEUS_URL=http://host.docker.internal:19090 -e LOKI_URL=http://host.docker.internal:13100 grafana
```

Seleccionar `eks` en el dashboard. Declarar que la visualización es local y las fuentes son de EKS. No presentar el Kubernetes renderizado/validado como un despliegue realizado.

## Participación y uso de IA

El usuario confirmó el 24-11-2026 que el docente permite asistencia para generar/modificar código y configuraciones, con revisión, comprensión y declaración. Codex generó cambios de instrumentación/configuración/scripts y ejecutó verificaciones locales. No se redactaron conclusiones, justificaciones del equipo ni reflexiones individuales. La declaración final debe ajustarse a la orientación Duoc: https://bibliotecas.duoc.cl/ia.

El cierre autoriza commits con la identidad real de Benjamín. Benjamín debe revisar instrumentación, fuentes y casos de calidad; Martín, RBAC, redes, recursos y auditoría. Cada uno registra sus comprobaciones/correcciones reales desde su cuenta y revisa el PR del otro. No repartir artificialmente autoría ni fabricar commits. Las explicaciones de decisiones y reflexiones las escriben ustedes.

Fuente de requisitos: `EP3_DOY0101_Estudiante.pdf`, páginas 2, 4 y 5; restricciones académicas en página 3. La evidencia local y los pendientes se registran en `EP3-evidencias.md`.
