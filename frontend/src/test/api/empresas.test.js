import { beforeAll, afterEach, afterAll, it, expect } from 'vitest'
import { server } from '../mocks/server'
import { getEmpresas, createEmpresa, updateEmpresa, deleteEmpresa } from '../../api/empresas'
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
it('obtiene las empresas con los campos de EP1', async () => {
  const { data } = await getEmpresas()
  expect(data[0]).toMatchObject({
    nombre: 'WorkMatch Demo',
    industria: 'Tecnología',
    plan: 'Básico'
  })
})
it('crea una empresa con HTTP201', async () => {
  const r = await createEmpresa({ nombre: 'Nueva', industria: 'Servicios', plan: 'Pro' })
  expect(r.status).toBe(201)
  expect(r.data).toMatchObject({ id: 99, nombre: 'Nueva', plan: 'Pro' })
})
it('actualiza la empresa indicada', async () => {
  const r = await updateEmpresa(2, { nombre: 'Cambio' })
  expect(r.data).toMatchObject({ id: 2, nombre: 'Cambio' })
})
it('elimina con HTTP204', async () => {
  expect((await deleteEmpresa(1)).status).toBe(204)
})
