package cl.duoc.jv0101.caso01.empresas.service;

import java.util.List;
import java.util.Optional;
import org.springframework.stereotype.Service;
import cl.duoc.jv0101.caso01.empresas.model.Empresa;
import cl.duoc.jv0101.caso01.empresas.repository.EmpresaRepository;

@Service
public class EmpresaService {

    private final EmpresaRepository repository;

    public EmpresaService(EmpresaRepository repository) {
        this.repository = repository;
    }

    public List<Empresa> findAll() {
        return repository.findAll();
    }

    public Optional<Empresa> findById(Long id) {
        return repository.findById(id);
    }

    public Empresa create(Empresa recurso) {
        return repository.save(recurso);
    }

    public Optional<Empresa> update(Long id, Empresa datos) {
        return repository.findById(id).map(existente -> {
            existente.setNombre(datos.getNombre());
            existente.setIndustria(datos.getIndustria());
            existente.setPlan(datos.getPlan());
            return repository.save(existente);
        });
    }

    public boolean delete(Long id) {
        return repository.findById(id).map(existente -> {
            repository.delete(existente);
            return true;
        }).orElse(false);
    }
}
