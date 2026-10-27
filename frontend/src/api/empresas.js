import axios from 'axios'
const api = axios.create({
  baseURL: '/api/empresas',
  xsrfCookieName: 'XSRF-TOKEN',
  xsrfHeaderName: 'X-XSRF-TOKEN'
})
export const getEmpresas = () => api.get('')
export const createEmpresa = (data) => api.post('', data)
export const updateEmpresa = (id, data) => api.put(`/${id}`, data)
export const deleteEmpresa = (id) => api.delete(`/${id}`)
