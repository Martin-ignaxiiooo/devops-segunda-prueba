export default function EmpresaTable({ empresas, onEdit, onDelete }) {
  if (empresas.length === 0)
    return (
      <div className="empty-state">
        <div className="icon">🏢</div>
        <p>No hay empresas registradas.</p>
        <p>Agrega la primera empresa usando el formulario.</p>
      </div>
    )
  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Nombre</th>
            <th>Industria</th>
            <th>Plan</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          {empresas.map((empresa) => (
            <tr key={empresa.id}>
              <td>
                <span className="badge">{empresa.id}</span>
              </td>
              <td>{empresa.nombre}</td>
              <td>{empresa.industria || '—'}</td>
              <td>{empresa.plan || '—'}</td>
              <td>
                <div className="td-actions">
                  <button
                    className="btn btn-ghost btn-sm"
                    title="Editar"
                    onClick={() => onEdit(empresa)}
                  >
                    Editar
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    title="Eliminar"
                    onClick={() => {
                      if (window.confirm(`¿Eliminar la empresa ${empresa.nombre}?`))
                        onDelete(empresa.id)
                    }}
                  >
                    Eliminar
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
