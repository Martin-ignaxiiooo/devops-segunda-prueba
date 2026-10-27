package cl.duocuc.ep02.infrastructure.controller;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

import java.util.List;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.http.MediaType;
import org.springframework.context.annotation.Import;
import cl.duocuc.ep02.config.SecurityConfig;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

import tools.jackson.databind.ObjectMapper;

import cl.duocuc.ep02.application.AlumnoService;
import cl.duocuc.ep02.domain.Alumno;

@WebMvcTest(AlumnoController.class)
@Import(SecurityConfig.class)
@WithMockUser
class AlumnoControllerTest {

    @Autowired private MockMvc mockMvc;

    @MockitoBean private AlumnoService service;

    @Autowired private ObjectMapper objectMapper;

    private org.springframework.test.web.servlet.request.RequestPostProcessor csrfToken(boolean valid)
            throws Exception {
        var response = mockMvc.perform(get("/ep02"))
                .andExpect(status().isOk()).andReturn().getResponse();
        var cookie = response.getCookie("XSRF-TOKEN");
        assertNotNull(cookie, "El GET debe emitir la cookie CSRF de la SPA");
        return request -> {
            request.setCookies(cookie);
            request.addHeader("X-XSRF-TOKEN", valid ? cookie.getValue() : "invalid");
            return request;
        };
    }

    @Test
    void listar_retorna200ConLista() throws Exception {
        when(service.listar())
                .thenReturn(
                        List.of(new Alumno(1L, "Juan", "Pérez"), new Alumno(2L, "Ana", "López")));

        mockMvc.perform(get("/ep02"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].nombre").value("Juan"))
                .andExpect(jsonPath("$[1].nombre").value("Ana"));
    }

    @Test
    void crear_retorna200ConAlumnoCreado() throws Exception {
        Alumno input = new Alumno(null, "Carlos", "Soto");
        Alumno created = new Alumno(3L, "Carlos", "Soto");
        when(service.crear(any(Alumno.class))).thenReturn(created);

        mockMvc.perform(
                        post("/ep02")
                                .with(csrfToken(true))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(objectMapper.writeValueAsString(input)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(3))
                .andExpect(jsonPath("$.nombre").value("Carlos"));
    }

    @Test
    void actualizar_retorna200ConAlumnoActualizado() throws Exception {
        Alumno input = new Alumno(null, "Luis", "Mora");
        Alumno updated = new Alumno(4L, "Luis", "Mora");
        when(service.actualizar(eq(4L), any(Alumno.class))).thenReturn(updated);

        mockMvc.perform(
                        put("/ep02/4")
                                .with(csrfToken(true))
                                .contentType(MediaType.APPLICATION_JSON)
                                .content(objectMapper.writeValueAsString(input)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value(4))
                .andExpect(jsonPath("$.nombre").value("Luis"));
    }

    @Test
    void eliminar_retorna200() throws Exception {
        doNothing().when(service).eliminar(5L);

        mockMvc.perform(delete("/ep02/5").with(csrfToken(true))).andExpect(status().isOk());

        verify(service, times(1)).eliminar(5L);
    }

    @Test
    void exportar_retornaCSV() throws Exception {
        when(service.listar())
                .thenReturn(
                        List.of(new Alumno(1L, "Juan", "Pérez"), new Alumno(2L, "Ana", "López")));

        mockMvc.perform(get("/ep02/export"))
                .andExpect(status().isOk())
                .andExpect(content().string("Juan,Pérez\nAna,López"));
    }

    @Test
    void exportar_listaVaciaRetornaCadenaVacia() throws Exception {
        when(service.listar()).thenReturn(List.of());

        mockMvc.perform(get("/ep02/export"))
                .andExpect(status().isOk())
                .andExpect(content().string(""));
    }

    @Test
    void importar_procesaCSVCorrectamente() throws Exception {
        String csv = "Juan,Pérez\nAna,López";
        when(service.crear(any(Alumno.class))).thenReturn(new Alumno(1L, "Juan", "Pérez"));

        mockMvc.perform(
                        post("/ep02/import")
                                .with(csrfToken(true))
                                .contentType(MediaType.TEXT_PLAIN)
                                .content(csv))
                .andExpect(status().isOk());

        verify(service, times(2)).crear(any(Alumno.class));
    }

    @Test
    void importar_ignoraLineasMalformadas() throws Exception {
        // línea con solo un campo no debe llamar a crear()
        String csv = "SoloNombre\nJuan,Pérez";
        when(service.crear(any(Alumno.class))).thenReturn(new Alumno(1L, "Juan", "Pérez"));

        mockMvc.perform(
                        post("/ep02/import")
                                .with(csrfToken(true))
                                .contentType(MediaType.TEXT_PLAIN)
                                .content(csv))
                .andExpect(status().isOk());

        verify(service, times(1)).crear(any(Alumno.class));
    }
    @Test
    void crear_sinTokenCsrfRetorna403() throws Exception {
        mockMvc.perform(post("/ep02")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"nombre\":\"Prueba\",\"apellido\":\"Seguridad\"}"))
                .andExpect(status().isForbidden());
        verifyNoInteractions(service);
    }

    @Test
    void crear_conTokenCsrfInvalidoRetorna403() throws Exception {
        mockMvc.perform(post("/ep02")
                        .with(csrfToken(false))
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"nombre\":\"Prueba\",\"apellido\":\"Seguridad\"}"))
                .andExpect(status().isForbidden());
        verify(service, never()).crear(any(Alumno.class));
    }
}
