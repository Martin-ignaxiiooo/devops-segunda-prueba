import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeAll, afterAll, afterEach, it, expect, vi } from 'vitest'
import { http, HttpResponse, delay } from 'msw'
import { server } from './mocks/server'
import { EMPRESAS } from './mocks/handlers'
import App from '../App'
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  vi.restoreAllMocks()
})
afterAll(() => server.close())
async function loaded() {
  render(<App />)
  await screen.findByText('WorkMatch Demo')
}
const send = () =>
  fireEvent.submit(screen.getByRole('button', { name: /Agregar|Guardar/ }).closest('form'))
it('presenta Empresas y sus estadísticas', async () => {
  await loaded()
  expect(screen.getByRole('heading')).toHaveTextContent('Gestión de Empresas')
  expect(document.querySelectorAll('.stat-num')[0]).toHaveTextContent('3')
  expect(document.querySelectorAll('.stat-num')[1]).toHaveTextContent('2')
  expect(screen.getByRole('link')).toHaveAttribute('href', '/v3/api-docs')
})
it('muestra carga y después registros', async () => {
  server.use(
    http.get('/api/empresas', async () => {
      await delay(40)
      return HttpResponse.json(EMPRESAS)
    })
  )
  render(<App />)
  expect(screen.getByText('Cargando...')).toBeInTheDocument()
  await screen.findByText('WorkMatch Demo')
})
it('muestra fallo de lectura', async () => {
  server.use(http.get('/api/empresas', () => HttpResponse.error()))
  render(<App />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Error al cargar empresas')
})
it('crea una empresa', async () => {
  await loaded()
  await userEvent.type(screen.getByLabelText('Nombre'), 'Nueva')
  send()
  expect(await screen.findByRole('status')).toHaveTextContent('Empresa creada correctamente')
})
it('edita y vuelve al formulario de creación', async () => {
  await loaded()
  fireEvent.click(screen.getAllByTitle('Editar')[0])
  expect(screen.getByText('Editar empresa')).toBeInTheDocument()
  send()
  expect(await screen.findByRole('status')).toHaveTextContent('actualizada')
  await waitFor(() => expect(screen.getByText('Nueva empresa')).toBeInTheDocument())
})
it('conserva edición tras error', async () => {
  server.use(http.put('/api/empresas/:id', () => new HttpResponse(null, { status: 400 })))
  await loaded()
  fireEvent.click(screen.getAllByTitle('Editar')[0])
  send()
  expect(await screen.findByRole('alert')).toHaveTextContent('Error al actualizar')
  expect(screen.getByText('Editar empresa')).toBeInTheDocument()
})
it('cancela la edición', async () => {
  await loaded()
  fireEvent.click(screen.getAllByTitle('Editar')[0])
  await userEvent.click(screen.getByText('Cancelar'))
  expect(screen.getByText('Nueva empresa')).toBeInTheDocument()
})
it('elimina una empresa con confirmación', async () => {
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  await loaded()
  fireEvent.click(screen.getAllByTitle('Eliminar')[0])
  expect(await screen.findByRole('status')).toHaveTextContent('Empresa eliminada')
})
