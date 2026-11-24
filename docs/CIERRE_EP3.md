# Cierre técnico EP3 — 24-11-2026

Repositorio: https://github.com/Martin-ignaxiiooo/devops-segunda-prueba. Rama publicada: [`ep3/observabilidad`](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/tree/ep3/observabilidad). Base main conservada: `14cf575e1875f43cc59961f314ab9be7bee7d1f0`.

Commit de implementación: `d09b56668b117ecc7ac3f72b80b2893f1719835c`, autor Benjamín Yantzen, `benjaminy2747@gmail.com`. La identidad coincide con la cuenta autenticada Benjaa4747. Este documento integra el commit posterior de documentación; consultar `git log` para identificarlo.

## Publicación y ejecución remota

El primer intento fue rechazado con HTTP 403. Después de habilitar escritura a Benjaa4747, se publicó exclusivamente `ep3/observabilidad`. No se modificó main ni se ejecutó un despliegue AWS. El registro inicial se conserva como historial, no como estado actual.

El [CI real 45460855415](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/actions/runs/45460855415), correspondiente a `bc9b946`, terminó en success: backend, frontend, SonarQube, las tres imágenes/Trivy y la auditoría de configuraciones aprobaron. El job ECR/EKS quedó skipped por la condición de rama. El [workflow de dependencias 45460928738](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/actions/runs/45460928738) también aprobó.

La [primera suite de bloqueos](https://github.com/Martin-ignaxiiooo/devops-segunda-prueba/actions/runs/45460855852) ejecutó los cuatro escenarios: fallas intencionales de calidad y cumplimiento, sus despliegues simulados omitidos, y éxito/recuperación aprobados. Su verificador detectó un problema de identificación: GitHub devuelve nombres con `${{ inputs.scenario }}` sin resolver para algunos jobs skipped. Se corrigió el reconocimiento usando el escenario y el estado real, con dos pruebas de regresión. Esto no cambia dependencias ni permite desplegar tras un control fallido. Consultar los runs más recientes de la rama y los artefactos del ZIP para la reejecución corregida.

Los workflows preparados son:

- `ci-cd.yml`: pruebas, cobertura, SonarQube, Trivy y validación de configuraciones; se activa en esta rama. El job AWS sigue limitado a main.
- `gate-suite.yml` y `gate-drill.yml`: cuatro escenarios aislados sin AWS, con fallas intencionales de calidad/cumplimiento y despliegues simulados omitidos. El verificador contrasta los estados reales cuando se ejecuten. La suite contiene casos negativos y puede terminar en rojo; su verificador debe aprobar los doce estados esperados.
- `dependency-graph.yml`: workflow EP2 conservado, ejecutable manualmente sobre la rama una vez publicada. Dependabot es un evento administrado por GitHub, no una ejecución manual reproducida localmente.

No hay credenciales AWS, AWS CLI ni contexto kubectl configurados en Windows/Ubuntu. Se comprobó que kubectl está disponible en Ubuntu, pero no tiene contexto seleccionado ni clústeres. No se ejecutó ninguna operación AWS ni se crearon recursos. Falta la captura de un clúster real y la comprobación de targets, TLS kubelet, permisos y capacidad efectiva en Kubernetes.

## Resultados reales

| Comprobación | Resultado |
|---|---|
| Revisión rápida de cambios publicables | Sin coincidencias de credenciales; `.env` y `.local` ignorados por Git |
| Backend | 24 pruebas aprobadas; JaCoCo LINE 100% dentro del alcance configurado en EP2 |
| Frontend | 32 pruebas aprobadas; cobertura 100%; lint y build aprobados |
| Verificación funcional final | 48 comprobaciones aprobadas: CRUD/PostgreSQL, CSRF, correlación y consultas de 15 paneles |
| Controles nuevos | 11 pruebas locales aprobadas, incluidas dos regresiones del verificador; primera auditoría remota aprobada |
| Kubernetes estático | 33/33 recursos válidos con kubeconform; auditoría aprobada |
| Trivy config | 0 HIGH/CRITICAL en los manifiestos finales |
| Trivy imágenes finales | 0 HIGH/CRITICAL corregibles en backend, frontend y PostgreSQL |
| SonarQube local | Scanner exit 0; gate OK; 0 bugs; 0 vulnerabilidades; cobertura combinada 98,9% |
| Bloqueos | Cuatro casos locales y jobs reales de Actions; despliegue simulado bloqueado en calidad/cumplimiento |
| GitHub Actions | CI principal y dependencias aprobados; suite con fallas intencionales y verificador corregido |
| AWS/Kubernetes | Sin verificación de ejecución: no hay credenciales ni contexto configurado |

SonarQube usa su propio alcance combinado de análisis; su 98,9% no se sustituye por el 100% de los reportes JaCoCo/Vitest configurados. El análisis identifica el commit `d09b566`. El servidor SonarQube fue temporal y local, con límite de memoria de 2 GiB; los JSON de gate, medidas e issues y el log del scanner se conservaron antes de detenerlo.

Problemas corregidos: métricas textfile con saltos de línea Windows, series duplicadas tras reiniciar Alloy, configuración de eventos Alloy, montajes para filesystem de solo lectura, acceso de métricas kubelet con privilegios restringidos, y seis vulnerabilidades corregibles de la base Nginx anterior. La ejecución local de SonarQube requirió preparar una copia de análisis para evitar montajes anidados sobre un directorio de solo lectura; esto no cambió la aplicación. Los errores iniciales del entorno no se presentan como análisis exitosos.

## Matriz de los seis indicadores

| Indicador | Estado al cierre | Falta imprescindible |
|---|---|---|
| IE1, 20% | Monitoreo y logs comprobados localmente | Evidencia del entorno Kubernetes autorizado |
| IE2, 20% | Integración Kubernetes/CI implementada y validada estáticamente | Ejecutar y verificar orquestación real |
| IE3, 10% | Dashboard de 15 paneles con datos locales reales | Fuentes de Kubernetes y un run/despliegue real de CI |
| IE4, 10% | Guía, evidencia, resumen y estructura de PPT preparados | Apartados propios del equipo y revisión del formato de entrega |
| IE5, 20% | SonarQube, Trivy, pruebas y políticas aprobados en CI real | Mantener artefactos del run entregado |
| IE6, 20% | Fallas/omisiones y recuperación observadas en Actions; simulación sin AWS | Mostrar los casos negativos y el verificador de la reejecución corregida |

## Archivos de entrega y participación

El ZIP `output/EP3_ENTREGA_MARTIN_2026-11-24.zip`, fuera del repositorio, organiza originales/copias saneadas por indicador, capturas reales, reportes, código y un bundle Git de la rama. Incluye integridad SHA-256. No contiene `.env`, credenciales GitHub/AWS, contraseñas Grafana ni imágenes Docker exportadas. Los registros con cookies/credenciales efímeras se saneaban solo en las copias de entrega y se identifican en `SANITIZACION.json`; se mantienen privados los originales.

La asistencia IA para implementación fue confirmada por el usuario como autorizada por el docente. Los integrantes deben revisar/comprender los cambios y declarar el uso. No se redactaron conclusiones, justificaciones técnicas del equipo ni reflexiones individuales. Estos espacios quedan para los autores, junto con las contribuciones y revisiones propias verificables de Martín.
