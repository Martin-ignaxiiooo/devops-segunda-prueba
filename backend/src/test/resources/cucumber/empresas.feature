# language: es
Característica: Servicio Empresas y Usuarios (microservicio empresas del caso caso01)
  Los escenarios validan el contrato REST del microservicio alineado a sus endpoints.

  Escenario: el listado del recurso responde 200
    Dado el servicio "Empresas y Usuarios" está disponible
    Cuando consulto el listado de "empresas"
    Entonces el listado responde con código 200

  Escenario: ciclo de vida completo del recurso
    Dado un nuevo "empresa" con nombre "hola-cucumber"
    Cuando consulto el "empresa" recién creado
    Entonces el recurso tiene nombre "hola-cucumber" y código 200
    Cuando actualizo el "empresa" con nombre "cucumber-actualizado"
    Entonces el recurso queda con nombre "cucumber-actualizado" y código 200
    Cuando elimino el "empresa"
    Entonces la eliminación responde con código 204
    Y al consultar el "empresa" eliminado responde 404

  Escenario: Rechazar escritura sin token CSRF
    Cuando intento crear una empresa sin token CSRF
    Entonces la escritura responde con código 403
