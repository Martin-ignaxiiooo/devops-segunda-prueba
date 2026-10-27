import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, it, expect, vi } from 'vitest'
import EmpresaForm from '../../components/EmpresaForm'
const submit = vi.fn(),
  cancel = vi.fn()
beforeEach(() => {
  submit.mockReset()
  cancel.mockReset()
})
const show = (editing = null) =>
  render(<EmpresaForm editing={editing} onSubmit={submit} onCancel={cancel} />)
const send = () =>
  fireEvent.submit(screen.getByRole('button', { name: /Agregar|Guardar/ }).closest('form'))
it('muestra tres campos vacíos y solo nombre obligatorio', () => {
  show()
  for (const name of ['Nombre', 'Industria', 'Plan'])
    expect(screen.getByLabelText(name)).toHaveValue('')
  expect(screen.getByLabelText('Nombre')).toBeRequired()
  expect(screen.getByLabelText('Industria')).not.toBeRequired()
  expect(screen.queryByText('Cancelar')).not.toBeInTheDocument()
})
it('rechaza nombre compuesto de espacios', async () => {
  show()
  await userEvent.type(screen.getByLabelText('Nombre'), '   ')
  send()
  expect(submit).not.toHaveBeenCalled()
})
it('envía los tres campos y limpia después de crear', async () => {
  submit.mockResolvedValue(true)
  show()
  for (const [label, value] of [
    ['Nombre', '  Nueva  '],
    ['Industria', 'Servicios'],
    ['Plan', 'Pro']
  ])
    await userEvent.type(screen.getByLabelText(label), value)
  send()
  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith({ nombre: 'Nueva', industria: 'Servicios', plan: 'Pro' })
  )
  await waitFor(() => expect(screen.getByLabelText('Nombre')).toHaveValue(''))
})
it('acepta industria y plan opcionales', async () => {
  submit.mockResolvedValue(true)
  show()
  await userEvent.type(screen.getByLabelText('Nombre'), 'Nueva')
  send()
  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith({ nombre: 'Nueva', industria: '', plan: '' })
  )
})
it('conserva los datos si falla la creación', async () => {
  submit.mockResolvedValue(false)
  show()
  await userEvent.type(screen.getByLabelText('Nombre'), 'Nueva')
  send()
  await waitFor(() => expect(submit).toHaveBeenCalled())
  expect(screen.getByLabelText('Nombre')).toHaveValue('Nueva')
})
it('precarga y edita los tres campos', async () => {
  submit.mockResolvedValue(true)
  show({ id: 1, nombre: 'Actual', industria: 'Comercio', plan: 'Básico' })
  expect(screen.getByLabelText('Plan')).toHaveValue('Básico')
  await userEvent.clear(screen.getByLabelText('Plan'))
  await userEvent.type(screen.getByLabelText('Plan'), 'Pro')
  send()
  await waitFor(() =>
    expect(submit).toHaveBeenCalledWith({ nombre: 'Actual', industria: 'Comercio', plan: 'Pro' })
  )
  expect(screen.getByLabelText('Nombre')).toHaveValue('Actual')
})
it('edita campos opcionales nulos como vacíos y cancela', async () => {
  show({ id: 1, nombre: 'Actual', industria: null, plan: null })
  expect(screen.getByLabelText('Industria')).toHaveValue('')
  expect(screen.getByLabelText('Plan')).toHaveValue('')
  await userEvent.click(screen.getByText('Cancelar'))
  expect(cancel).toHaveBeenCalledOnce()
})
