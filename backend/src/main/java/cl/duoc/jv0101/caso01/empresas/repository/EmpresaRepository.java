package cl.duoc.jv0101.caso01.empresas.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import cl.duoc.jv0101.caso01.empresas.model.Empresa;

public interface EmpresaRepository extends JpaRepository<Empresa, Long> {
}
