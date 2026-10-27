package cl.duoc.jv0101.caso01.empresas.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.NotBlank;

@JsonIgnoreProperties("id")
public record EmpresaRequest(@NotBlank(message = "El nombre es obligatorio") String nombre,
                             String industria, String plan) {}
