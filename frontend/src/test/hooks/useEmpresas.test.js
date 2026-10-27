import { renderHook, waitFor, act } from '@testing-library/react'
import { beforeAll, afterAll, afterEach, it, expect } from 'vitest'
import { http, HttpResponse } from 'msw'
import { server } from '../mocks/server'
import { useEmpresas } from '../../hooks/useEmpresas'
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => server.resetHandlers())
afterAll(() => server.close())
async function loaded() {
  const hook = renderHook(() => useEmpresas())
  await waitFor(() => expect(hook.result.current.empresas).toHaveLength(3))
  return hook
}
it('carga y permite recargar las empresas', async () => {
  const h = await loaded()
  server.use(http.get('/api/empresas', () => HttpResponse.json([])))
  await act(async () => {
    await h.result.current.reload()
  })
  expect(h.result.current.empresas).toEqual([])
  expect(h.result.current.loading).toBe(false)
})
it('informa un error de lectura', async () => {
  server.use(http.get('/api/empresas', () => HttpResponse.error()))
  const h = renderHook(() => useEmpresas())
  await waitFor(() => expect(h.result.current.error).toContain('cargar'))
  expect(h.result.current.loading).toBe(false)
})
for (const [method, action, args, text] of [
  ['post', 'crear', [{ nombre: 'Nueva' }], 'creada'],
  ['put', 'actualizar', [1, { nombre: 'Cambio' }], 'actualizada'],
  ['delete', 'eliminar', [1], 'eliminada']
]) {
  it(`${action} y notifica éxito`, async () => {
    const h = await loaded()
    let ok
    await act(async () => {
      ok = await h.result.current[action](...args)
    })
    expect(ok).toBe(true)
    expect(h.result.current.success).toContain(text)
    expect(h.result.current.error).toBeNull()
  })
  it(`${action} informa el fallo sin éxito falso`, async () => {
    const h = await loaded()
    server.use(
      http[method](
        method === 'post' ? '/api/empresas' : '/api/empresas/:id',
        () => new HttpResponse(null, { status: 500 })
      )
    )
    let ok
    await act(async () => {
      ok = await h.result.current[action](...args)
    })
    expect(ok).toBe(false)
    expect(h.result.current.error).toContain('Error')
    expect(h.result.current.success).toBeNull()
  })
}
