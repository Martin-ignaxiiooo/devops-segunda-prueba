package cl.duoc.jv0101.caso01.empresas;

import tools.jackson.databind.ObjectMapper;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import cl.duoc.jv0101.caso01.empresas.model.Empresa;
import cl.duoc.jv0101.caso01.empresas.service.EmpresaService;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import org.springframework.test.web.servlet.request.RequestPostProcessor;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.put;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
class EmpresaControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockitoBean
    private EmpresaService service;

    private RequestPostProcessor csrfToken(boolean valid) throws Exception {
        var response = mockMvc.perform(get("/api/empresas")).andExpect(status().isOk()).andReturn().getResponse();
        var cookie = response.getCookie("XSRF-TOKEN");
        assertNotNull(cookie);
        return request -> {
            request.setCookies(cookie);
            request.addHeader("X-XSRF-TOKEN", valid ? cookie.getValue() : "invalid");
            return request;
        };
    }

    private Empresa recurso(Long id) {
        Empresa r = new Empresa();
        r.setId(id);
        r.setNombre("Demo");
        r.setIndustria("valor");
        r.setPlan("valor");
        return r;
    }

    private String body() throws Exception {
        return objectMapper.writeValueAsString(recurso(null));
    }

    @Test
    void listarDevuelve200YLista() throws Exception {
        when(service.findAll()).thenReturn(List.of(recurso(1L)));
        mockMvc.perform(get("/api/empresas"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$").isArray())
            .andExpect(jsonPath("$.length()").value(1));
    }

    @Test
    void obtenerExistenteDevuelve200() throws Exception {
        when(service.findById(1L)).thenReturn(Optional.of(recurso(1L)));
        mockMvc.perform(get("/api/empresas/1"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.nombre").value("Demo"));
    }

    @Test
    void obtenerInexistenteDevuelve404() throws Exception {
        when(service.findById(1L)).thenReturn(Optional.empty());
        mockMvc.perform(get("/api/empresas/1")).andExpect(status().isNotFound());
    }

    @Test
    void crearValidoDevuelve201() throws Exception {
        when(service.create(any())).thenReturn(recurso(1L));
        mockMvc.perform(post("/api/empresas").with(csrfToken(true))
                .contentType(MediaType.APPLICATION_JSON)
                .content(body()))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.id").value(1));
    }

    @Test
    void crearInvalidoDevuelve400() throws Exception {
        mockMvc.perform(post("/api/empresas").with(csrfToken(true))
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"nombre\":\"\"}"))
            .andExpect(status().isBadRequest());
    }

    @Test
    void actualizarExistenteDevuelve200() throws Exception {
        Empresa actualizado = recurso(1L);
        actualizado.setNombre("Actualizado");
        when(service.update(any(), any())).thenReturn(Optional.of(actualizado));
        mockMvc.perform(put("/api/empresas/1").with(csrfToken(true))
                .contentType(MediaType.APPLICATION_JSON)
                .content(body()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.nombre").value("Actualizado"));
    }

    @Test
    void actualizarInexistenteDevuelve404() throws Exception {
        when(service.update(any(), any())).thenReturn(Optional.empty());
        mockMvc.perform(put("/api/empresas/1").with(csrfToken(true))
                .contentType(MediaType.APPLICATION_JSON)
                .content(body()))
            .andExpect(status().isNotFound());
    }

    @Test
    void eliminarExistenteDevuelve204() throws Exception {
        when(service.delete(1L)).thenReturn(true);
        mockMvc.perform(delete("/api/empresas/1").with(csrfToken(true))).andExpect(status().isNoContent());
    }

    @Test
    void eliminarInexistenteDevuelve404() throws Exception {
        when(service.delete(1L)).thenReturn(false);
        mockMvc.perform(delete("/api/empresas/1").with(csrfToken(true))).andExpect(status().isNotFound());
    }

    @Test
    void crearSinCsrfDevuelve403() throws Exception {
        mockMvc.perform(post("/api/empresas").contentType(MediaType.APPLICATION_JSON).content("{\"nombre\":\"Prueba\"}"))
            .andExpect(status().isForbidden());
        verify(service, never()).create(any());
    }

    @Test
    void crearConCsrfInvalidoDevuelve403() throws Exception {
        mockMvc.perform(post("/api/empresas").with(csrfToken(false)).contentType(MediaType.APPLICATION_JSON).content("{\"nombre\":\"Prueba\"}"))
            .andExpect(status().isForbidden());
        verify(service, never()).create(any());
    }
}
