# Cierre técnico EP3 — 24-11-2026

Repositorio: https://github.com/Martin-ignaxiiooo/devops-segunda-prueba. Rama de entrega local: `ep3/observabilidad`. Base main conservada: `14cf575e1875f43cc59961f314ab9be7bee7d1f0`.

Commit de implementación: `d09b56668b117ecc7ac3f72b80b2893f1719835c`, autor Benjamín Yantzen, `benjaminy2747@gmail.com`. La identidad coincide con la cuenta autenticada Benjaa4747. Este documento integra el commit posterior de documentación; consultar `git log` para identificarlo.

## Publicación y ejecución remota

Se intentó publicar exclusivamente `ep3/observabilidad`. GitHub rechazó el push con HTTP 403: la cuenta Benjaa4747 tiene lectura y no escritura en el repositorio de Martín. No se publicó la rama, no se modificó main y no se ejecutaron workflows EP3. La captura de Actions muestra cero runs de esta rama; no representa una ejecución exitosa.

Martín debe agregar a Benjaa4747 como colaborador y este aceptar la invitación, o importar y publicar la rama desde el bundle incluido en el ZIP. El propietario puede publicar el historial manteniendo la autoría real de Benjamín; eso no convierte estos commits en contribuciones individuales de Martín.

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
| Controles nuevos | 9 pruebas aprobadas; workflows YAML válidos |
| Kubernetes estático | 33/33 recursos válidos con kubeconform; auditoría aprobada |
| Trivy config | 0 HIGH/CRITICAL en los manifiestos finales |
| Trivy imágenes finales | 0 HIGH/CRITICAL corregibles en backend, frontend y PostgreSQL |
| SonarQube local | Scanner exit 0; gate OK; 0 bugs; 0 vulnerabilidades; cobertura combinada 98,9% |
| Bloqueos locales | Éxito, falla JUnit, incumplimiento y recuperación con los resultados esperados; despliegue simulado |
| GitHub Actions / AWS | No verificados para EP3 por los accesos faltantes |

SonarQube usa su propio alcance combinado de análisis; su 98,9% no se sustituye por el 100% de los reportes JaCoCo/Vitest configurados. El análisis identifica el commit `d09b566`. El servidor SonarQube fue temporal y local, con límite de memoria de 2 GiB; los JSON de gate, medidas e issues y el log del scanner se conservaron antes de detenerlo.

Problemas corregidos: métricas textfile con saltos de línea Windows, series duplicadas tras reiniciar Alloy, configuración de eventos Alloy, montajes para filesystem de solo lectura, acceso de métricas kubelet con privilegios restringidos, y seis vulnerabilidades corregibles de la base Nginx anterior. La ejecución local de SonarQube requirió preparar una copia de análisis para evitar montajes anidados sobre un directorio de solo lectura; esto no cambió la aplicación. Los errores iniciales del entorno no se presentan como análisis exitosos.

## Matriz de los seis indicadores

| Indicador | Estado al cierre | Falta imprescindible |
|---|---|---|
| IE1, 20% | Monitoreo y logs comprobados localmente | Evidencia del entorno Kubernetes autorizado |
| IE2, 20% | Integración Kubernetes/CI implementada y validada estáticamente | Ejecutar y verificar orquestación real |
| IE3, 10% | Dashboard de 15 paneles con datos locales reales | Fuentes de Kubernetes y un run/despliegue real de CI |
| IE4, 10% | Guía, evidencia, resumen y estructura de PPT preparados | Apartados propios del equipo y revisión del formato de entrega |
| IE5, 20% | SonarQube, Trivy, pruebas y políticas locales aprobados | Resultados del pipeline publicado en Actions |
| IE6, 20% | Bloqueos comprobados en ensayo local con despliegue simulado | Jobs reales de Actions fallidos/omitidos y recuperación |

## Archivos de entrega y participación

El ZIP `output/EP3_ENTREGA_MARTIN_2026-11-24.zip`, fuera del repositorio, organiza originales/copias saneadas por indicador, capturas reales, reportes, código y un bundle Git de la rama. Incluye integridad SHA-256. No contiene `.env`, credenciales GitHub/AWS, contraseñas Grafana ni imágenes Docker exportadas. Los registros con cookies/credenciales efímeras se saneaban solo en las copias de entrega y se identifican en `SANITIZACION.json`; se mantienen privados los originales.

La asistencia IA para implementación fue confirmada por el usuario como autorizada por el docente. Los integrantes deben revisar/comprender los cambios y declarar el uso. No se redactaron conclusiones, justificaciones técnicas del equipo ni reflexiones individuales. Estos espacios quedan para los autores, junto con las contribuciones y revisiones propias verificables de Martín.
