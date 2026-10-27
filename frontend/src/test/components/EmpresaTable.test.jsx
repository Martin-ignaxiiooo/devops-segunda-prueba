import { render, screen, fireEvent } from '@testing-library/react'
import { it, expect, vi, afterEach } from 'vitest'
import EmpresaTable from '../../components/EmpresaTable'
import { EMPRESAS } from '../mocks/handlers'
afterEach(() => vi.restoreAllMocks())
it('presenta estado vacío', () => {
  render(<EmpresaTable empresas={[]} />)
  expect(screen.getByText('No hay empresas registradas.')).toBeInTheDocument()
})
it('presenta campos de EP1 y valores opcionales ausentes', () => {
  render(<EmpresaTable empresas={EMPRESAS} />)
  expect(screen.getByText('WorkMatch Demo')).toBeInTheDocument()
  expect(screen.getByText('Tecnología')).toBeInTheDocument()
  expect(screen.getByText('Básico')).toBeInTheDocument()
  expect(screen.getAllByText('—')).toHaveLength(2)
})
it('selecciona la empresa para editar', () => {
  const edit = vi.fn()
  render(<EmpresaTable empresas={EMPRESAS} onEdit={edit} />)
  fireEvent.click(screen.getAllByTitle('Editar')[0])
  expect(edit).toHaveBeenCalledWith(EMPRESAS[0])
})
it('elimina solo tras confirmar', () => {
  const remove = vi.fn()
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
  render(<EmpresaTable empresas={EMPRESAS} onDelete={remove} />)
  fireEvent.click(screen.getAllByTitle('Eliminar')[0])
  expect(confirm).toHaveBeenCalledWith('¿Eliminar la empresa WorkMatch Demo?')
  expect(remove).toHaveBeenCalledWith(1)
})
it('respeta la cancelación de eliminar', () => {
  const remove = vi.fn()
  vi.spyOn(window, 'confirm').mockReturnValue(false)
  render(<EmpresaTable empresas={EMPRESAS} onDelete={remove} />)
  fireEvent.click(screen.getAllByTitle('Eliminar')[0])
  expect(remove).not.toHaveBeenCalled()
})
