import axios from 'axios'

// Rutas del mismo origen; Axios propaga el token CSRF emitido por Spring.
const api = axios.create({
  baseURL: '/ep02',
  xsrfCookieName: 'XSRF-TOKEN',
  xsrfHeaderName: 'X-XSRF-TOKEN'
})

export const getAlumnos = () => api.get('')
export const createAlumno = (data) => api.post('', data)
export const updateAlumno = (id, data) => api.put(`/${id}`, data)
export const deleteAlumno = (id) => api.delete(`/${id}`)
export const exportCSV = () => api.get('/export', { responseType: 'text' })
export const importCSV = (csvText) =>
  api.post('/import', csvText, {
    headers: { 'Content-Type': 'text/plain' }
  })
