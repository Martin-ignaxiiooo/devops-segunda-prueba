# EP3: evidencia local y pendientes

Fecha: 24-11-2026. Base `14cf575e1875f43cc59961f314ab9be7bee7d1f0`, rama `ep3/observabilidad`. Los primeros reportes se obtuvieron antes de crear commits e indican `origin=local`, `working_tree=modified`; no corresponden a una ejecución de GitHub Actions ni AWS. El estado posterior del cierre está en `CIERRE_EP3.md`; se conserva la procedencia original de los reportes.

| Indicador de la rúbrica | Implementado y comprobado | Evidencia pendiente |
|---|---|---|
| IE1: monitoreo y logs (20%) | Actuator/Micrometer, Prometheus, Loki y Alloy funcionando en Docker; logs de backend, frontend y PostgreSQL; correlación Nginx/Tomcat con el mismo request ID. | Capturas y consultas del entorno Kubernetes autorizado. |
| IE2: automatización y orquestación (20%) | Generación de manifiestos, RBAC, redes, límites y despliegue integrado al pipeline. Configuraciones validadas; 33 recursos pasan kubeconform. | Ejecución real en Kubernetes; targets, TLS kubelet, permisos y capacidad efectiva del nodo. |
| IE3: dashboard (10%) | 15 paneles con consultas y datos reales: duración, ambas coberturas, CPU, memoria, disponibilidad, errores, logs y procedencia. | Dashboard consultando fuentes Kubernetes y un despliegue real de Actions. |
| IE4: documentación (10%) | Guía operativa `EP3.md`, fuentes, comandos, limitaciones y registro de asistencia IA. | Explicaciones, decisiones, conclusiones y reflexiones redactadas por los integrantes; revisión del formato solicitado por la rúbrica. |
| IE5: cumplimiento y auditoría (20%) | Auditor propio, kubeconform, validadores nativos y Trivy config. Nueve pruebas de controles pasan. SonarQube y controles EP2 conservados. | Resultados del pipeline completo con SonarQube y auditorías de la versión que el equipo publique. |
| IE6: bloqueo (20%) | Dependencias obligatorias de `deploy`; ensayo local de éxito, falla de JUnit, incumplimiento y recuperación con resultados esperados. | Runs reales del workflow `gate-drill.yml`, con jobs de despliegue simulado omitidos ante fallas. No se ha probado un bloqueo remoto durante esta sesión. |

## Resultados observados

- Backend: 24 pruebas aprobadas; JaCoCo LINE 100% dentro del alcance configurado en EP2 (excluye la clase Application). Pruebas automatizadas con H2; CRUD de ejecución comprobado con PostgreSQL real.
- Frontend: 32 pruebas aprobadas; cobertura 100% en líneas, sentencias, funciones y ramas; lint y compilación aprobados.
- Verificación funcional: 48 comprobaciones aprobadas, incluyendo crear/leer/actualizar/eliminar, validaciones 400, CSRF 403, eliminación 404, ausencia de registros de prueba residuales, Actuator fuera del proxy y las consultas de los 15 paneles.
- Kubeconform 0.8.0: 33/33 recursos válidos, esquema Kubernetes 1.35.0; cero errores, inválidos u omitidos. Es validación estática, no ejecución del clúster.
- Trivy 0.76.2 config: cero hallazgos HIGH/CRITICAL en los manifiestos finales. Las imágenes finales de backend, frontend y PostgreSQL tienen cero vulnerabilidades HIGH/CRITICAL corregibles según las bases descargadas en esta ejecución. Esto no demuestra ausencia de vulnerabilidades de otras severidades o todavía sin corrección.
- Arranque/aplicación y verificación local inicial: 73,125 segundos (`deploy-timing-initial.json`). Última actualización local, recreando el frontend corregido y esperando salud del stack: 6,985 segundos (`deploy-timing.json`, valor del dashboard). No son tiempos de arranque en frío, duración total del pipeline ni tiempos de cola.
- Ensayos locales: éxito y recuperación permiten la simulación; JUnit fallido e incumplimiento de manifiesto la bloquean. Ningún manifiesto inválido se aplicó.
- Los siete contenedores estaban activos sin OOM al tomar `runtime.json`; las tres aplicaciones estaban healthy. Memoria instantánea del conjunto cercana a 1 GiB, sin incluir Docker/WSL ni el sistema operativo. No representa el máximo durante compilaciones ni garantiza capacidad de EKS.
- La disponibilidad observada incluye las interrupciones reales de los reinicios; no se corrigió artificialmente a 100%.

## Ubicación y reproducción

Los originales están en `.local/evidence/` (ignorados por Git): `verification.json`, `dashboard-queries.json`, `correlation.json`, `runtime.json`, `deploy-timing.json`, `kubeconform.log`, `configuration-tests-final.log`, `trivy-config-final.json`, `trivy-backend.json`, `backend/`, `frontend/` y `drills/results.json`. Las métricas derivadas y sus hashes están en `.local/metrics/ci.json`. `source-files.sha256` identifica los archivos de código/configuración de esta copia local.

Problema corregido: la imagen anterior del frontend contenía Nginx 1.30.6 y seis hallazgos corregibles (cuatro CRITICAL, dos HIGH). `apk upgrade` no actualizaba ese paquete del proveedor. Se cambió la base a `nginx/nginx-unprivileged:1.30.7-alpine`, fijada por digest; el escaneo posterior pasó y se repitieron las 48 comprobaciones funcionales. El [repositorio oficial de Nginx](https://github.com/nginx/docker-nginx-unprivileged/blob/main/README.md#image-registries) documenta el cambio de registro de imágenes. Se conservan `trivy-frontend-before.json`, `trivy-frontend.json` y `trivy-database.json`. Los dos últimos escaneos se realizaron sobre imágenes exportadas, sin entregar el socket Docker al escáner.

Con el stack y el recolector de recursos activos, reproducir la comprobación funcional:

```sh
node scripts/verify-observability.mjs
```

El procedimiento crea y elimina una empresa temporal y produce respuestas 400/403/404 deliberadas. Estas quedan como errores registrados reales. Reemplaza los reportes de esa comprobación; conservar copias fechadas si se necesita comparar ejecuciones. Las pruebas y los ensayos de controles se ejecutan con los comandos de `EP3.md`.

No se ha desplegado AWS ni publicado cambios remotos. El equipo todavía debe revisar los cambios, realizar contribuciones propias verificables y ejecutar las demostraciones remotas cuando exista autorización. No se presenta esta copia local como cumplimiento completo de los seis indicadores.
