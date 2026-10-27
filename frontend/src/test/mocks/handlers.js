import { http, HttpResponse } from 'msw'
export const EMPRESAS = [
  { id: 1, nombre: 'WorkMatch Demo', industria: 'Tecnología', plan: 'Básico' },
  { id: 2, nombre: 'Comercio Demo', industria: 'Comercio', plan: 'Pro' },
  { id: 3, nombre: 'Servicios Demo', industria: null, plan: null }
]
export const handlers = [
  http.get('/api/empresas', () => HttpResponse.json(EMPRESAS)),
  http.post('/api/empresas', async ({ request }) =>
    HttpResponse.json({ id: 99, ...(await request.json()) }, { status: 201 })
  ),
  http.put('/api/empresas/:id', async ({ params, request }) =>
    HttpResponse.json({ id: Number(params.id), ...(await request.json()) })
  ),
  http.delete('/api/empresas/:id', () => new HttpResponse(null, { status: 204 }))
]
