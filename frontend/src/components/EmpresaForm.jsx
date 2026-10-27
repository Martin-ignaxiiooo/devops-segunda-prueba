import { useState, useEffect } from 'react'
const EMPTY = { nombre: '', industria: '', plan: '' }
export default function EmpresaForm({ editing, onSubmit, onCancel }) {
  const [form, setForm] = useState(EMPTY)
  useEffect(() => {
    setForm(
      editing
        ? { nombre: editing.nombre, industria: editing.industria ?? '', plan: editing.plan ?? '' }
        : EMPTY
    )
  }, [editing])
  const handle = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }))
  const submit = async (e) => {
    e.preventDefault()
    if (!form.nombre.trim()) return
    const ok = await onSubmit({
      nombre: form.nombre.trim(),
      industria: form.industria.trim(),
      plan: form.plan.trim()
    })
    if (ok && !editing) setForm(EMPTY)
  }
  return (
    <div className="card">
      <div className="card-title">{editing ? 'Editar empresa' : 'Nueva empresa'}</div>
      <form onSubmit={submit}>
        <div className="form-row">
          <div className="form-group">
            <label htmlFor="nombre">Nombre</label>
            <input
              id="nombre"
              name="nombre"
              value={form.nombre}
              onChange={handle}
              required
              autoComplete="off"
              placeholder="Ej: WorkMatch Demo"
            />
          </div>
          <div className="form-group">
            <label htmlFor="industria">Industria</label>
            <input
              id="industria"
              name="industria"
              value={form.industria}
              onChange={handle}
              autoComplete="off"
              placeholder="Ej: Tecnología"
            />
          </div>
          <div className="form-group">
            <label htmlFor="plan">Plan</label>
            <input
              id="plan"
              name="plan"
              value={form.plan}
              onChange={handle}
              autoComplete="off"
              placeholder="Ej: Básico"
            />
          </div>
        </div>
        <div className="btn-actions">
          <button type="submit" className="btn btn-primary">
            {editing ? 'Guardar cambios' : 'Agregar empresa'}
          </button>
          {editing && (
            <button type="button" className="btn btn-ghost" onClick={onCancel}>
              Cancelar
            </button>
          )}
        </div>
      </form>
    </div>
  )
}
