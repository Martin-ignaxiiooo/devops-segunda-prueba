import { useState } from 'react'
import { useEmpresas } from './hooks/useEmpresas'
import EmpresaForm from './components/EmpresaForm'
import EmpresaTable from './components/EmpresaTable'
export default function App() {
  const { empresas, loading, error, success, crear, actualizar, eliminar } = useEmpresas()
  const [editing, setEditing] = useState(null)
  const handleSubmit = async (form) => {
    if (editing) {
      const ok = await actualizar(editing.id, form)
      if (ok) setEditing(null)
      return ok
    }
    return crear(form)
  }
  return (
    <div className="app-wrapper">
      <header className="app-header">
        <h1>🏢 Gestión de Empresas</h1>
        <p>WorkMatch · Registro de empresas</p>
      </header>
      {error && (
        <div role="alert" className="alert alert-error">
          {error}
        </div>
      )}
      {success && (
        <div role="status" className="alert alert-success">
          {success}
        </div>
      )}
      <div className="stats-bar">
        <div className="stat-card">
          <div className="stat-num">{empresas.length}</div>
          <div className="stat-label">Total empresas</div>
        </div>
        <div className="stat-card">
          <div className="stat-num">
            {new Set(empresas.map((e) => e.industria).filter(Boolean)).size}
          </div>
          <div className="stat-label">Industrias</div>
        </div>
      </div>
      <EmpresaForm editing={editing} onSubmit={handleSubmit} onCancel={() => setEditing(null)} />
      <div className="card">
        <div className="card-title">Lista de empresas {loading && <span>Cargando...</span>}</div>
        {loading ? (
          <div className="spinner-wrap">
            <div className="spinner" />
          </div>
        ) : (
          <EmpresaTable empresas={empresas} onEdit={setEditing} onDelete={eliminar} />
        )}
      </div>
      <footer className="app-footer">
        Empresas · Ingeniería DevOps · <a href="/v3/api-docs">Especificación OpenAPI</a>
      </footer>
    </div>
  )
}
