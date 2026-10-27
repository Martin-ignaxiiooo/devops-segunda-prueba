import { useState, useEffect, useCallback } from 'react'
import { getEmpresas, createEmpresa, updateEmpresa, deleteEmpresa } from '../api/empresas'
export function useEmpresas() {
  const [empresas, setEmpresas] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const notify = (message, failed = false) => {
    setError(failed ? message : null)
    setSuccess(failed ? null : message)
  }
  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await getEmpresas()
      setEmpresas(data)
    } catch {
      notify('Error al cargar empresas', true)
    } finally {
      setLoading(false)
    }
  }, [])
  useEffect(() => {
    load()
  }, [load])
  const crear = async (data) => {
    try {
      await createEmpresa(data)
      await load()
      notify('Empresa creada correctamente')
      return true
    } catch {
      notify('Error al crear empresa', true)
      return false
    }
  }
  const actualizar = async (id, data) => {
    try {
      await updateEmpresa(id, data)
      await load()
      notify('Empresa actualizada correctamente')
      return true
    } catch {
      notify('Error al actualizar empresa', true)
      return false
    }
  }
  const eliminar = async (id) => {
    try {
      await deleteEmpresa(id)
      await load()
      notify('Empresa eliminada')
      return true
    } catch {
      notify('Error al eliminar empresa', true)
      return false
    }
  }
  return { empresas, loading, error, success, crear, actualizar, eliminar, reload: load }
}
