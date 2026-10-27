package cl.duoc.jv0101.caso01.empresas.cucumber;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.Then;
import io.cucumber.java.en.When;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.resttestclient.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import cl.duoc.jv0101.caso01.empresas.model.Empresa;

import static org.assertj.core.api.Assertions.assertThat;

public class EmpresaSteps {

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate rest;

    private Long id;
    private int listadoStatus;
    private ResponseEntity<Empresa> respuesta;
    private ResponseEntity<Void> respuestaVoid;

    private String url() {
        return "http://localhost:" + port + "/api/empresas";
    }

    private HttpEntity<Map<String, String>> body(String nombre) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        var initial = rest.getForEntity(url(), String.class);
        String cookie = java.util.Objects.requireNonNull(initial.getHeaders().get(HttpHeaders.SET_COOKIE))
            .stream().filter(value -> value.startsWith("XSRF-TOKEN=")).findFirst().orElseThrow().split(";", 2)[0];
        headers.set(HttpHeaders.COOKIE, cookie);
        headers.set("X-XSRF-TOKEN", cookie.substring("XSRF-TOKEN=".length()));
        return new HttpEntity<>(Map.of("nombre", nombre), headers);
    }

    @Given("el servicio {string} está disponible")
    public void servicioDisponible(String servicio) {
        ResponseEntity<Empresa[]> listado = rest.getForEntity(url(), Empresa[].class);
        listadoStatus = listado.getStatusCode().value();
        assertThat(listadoStatus).isEqualTo(HttpStatus.OK.value());
    }

    @When("consulto el listado de {string}")
    public void consultarListado(String recurso) {
        ResponseEntity<Empresa[]> listado = rest.getForEntity(url(), Empresa[].class);
        listadoStatus = listado.getStatusCode().value();
        assertThat(listadoStatus).isEqualTo(HttpStatus.OK.value());
    }

    @Then("el listado responde con código {int}")
    public void listadoCodigo(int codigo) {
        assertThat(listadoStatus).isEqualTo(codigo);
    }

    @Given("un nuevo {string} con nombre {string}")
    public void crearRecurso(String recurso, String nombre) {
        ResponseEntity<Empresa> creado = rest.postForEntity(
                url(), body(nombre), Empresa.class);
        assertThat(creado.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        id = creado.getBody().getId();
    }

    @When("consulto el {string} recién creado")
    public void consultarCreado(String recurso) {
        respuesta = rest.getForEntity(url() + "/" + id, Empresa.class);
    }

    @Then("el recurso tiene nombre {string} y código {int}")
    public void recursoConNombre(String nombre, int codigo) {
        assertThat(respuesta.getStatusCode().value()).isEqualTo(codigo);
        assertThat(respuesta.getBody().getNombre()).isEqualTo(nombre);
    }

    @When("actualizo el {string} con nombre {string}")
    public void actualizar(String recurso, String nombre) {
        respuesta = rest.exchange(url() + "/" + id, HttpMethod.PUT, body(nombre), Empresa.class);
    }

    @Then("el recurso queda con nombre {string} y código {int}")
    public void recursoActualizado(String nombre, int codigo) {
        assertThat(respuesta.getStatusCode().value()).isEqualTo(codigo);
        assertThat(respuesta.getBody().getNombre()).isEqualTo(nombre);
    }

    @When("elimino el {string}")
    public void eliminar(String recurso) {
        respuestaVoid = rest.exchange(url() + "/" + id, HttpMethod.DELETE, new HttpEntity<>(body("unused").getHeaders()), Void.class);
    }

    @Then("la eliminación responde con código {int}")
    public void eliminarCodigo(int codigo) {
        assertThat(respuestaVoid.getStatusCode().value()).isEqualTo(codigo);
    }

    @Then("al consultar el {string} eliminado responde {int}")
    public void consultarEliminado(String recurso, int codigo) {
        ResponseEntity<Empresa> noExiste = rest.getForEntity(url() + "/" + id, Empresa.class);
        assertThat(noExiste.getStatusCode().value()).isEqualTo(codigo);
    }

    @When("intento crear una empresa sin token CSRF")
    public void crearSinToken() {
        respuestaVoid = rest.postForEntity(url(), Map.of("nombre", "Sin token"), Void.class);
    }
    @Then("la escritura responde con código {int}")
    public void escrituraCodigo(int codigo) {
        assertThat(respuestaVoid.getStatusCode().value()).isEqualTo(codigo);
    }
}
