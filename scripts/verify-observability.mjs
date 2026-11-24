import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const output = path.join(root, '.local/evidence');
const base = 'http://127.0.0.1:8081';
const checks = [];
let cookie = '', token = '', createdId;
const dockerCandidate = path.join(process.env.LOCALAPPDATA || '', 'Programs/DockerDesktop/resources/bin/docker.exe');
const docker = fs.existsSync(dockerCandidate) ? dockerCandidate : 'docker';

function check(name, actual, expected) {
  const passed = actual === expected;
  checks.push({ name, actual, expected, passed });
  if (!passed) throw new Error(`${name}: esperado ${expected}, recibido ${actual}`);
}

async function request(method, endpoint, body, csrf = 'valid') {
  const headers = {};
  if (csrf !== 'none') {
    headers.Cookie = cookie;
    headers['X-XSRF-TOKEN'] = csrf === 'valid' ? token : 'invalid';
  }
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  return fetch(base + endpoint, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), signal: AbortSignal.timeout(15000) });
}

async function verify() {
  const initial = await fetch(base + '/api/empresas');
  check('GET lista', initial.status, 200);
  const initialCount = (await initial.json()).length;
  const csrfCookie = initial.headers.getSetCookie().find(item => item.startsWith('XSRF-TOKEN='));
  if (!csrfCookie) throw new Error('Falta cookie CSRF');
  cookie = csrfCookie.split(';')[0];
  token = decodeURIComponent(cookie.slice('XSRF-TOKEN='.length));
  const requestId = initial.headers.get('x-request-id');
  check('Request ID presente', /^[a-f0-9]{32}$/.test(requestId || ''), true);
  const created = await request('POST', '/api/empresas', { nombre: 'EP3 verificacion temporal', industria: 'Prueba', plan: 'Temporal' });
  check('Crear', created.status, 201);
  createdId = (await created.json()).id;
  check('Leer por ID', (await request('GET', '/api/empresas/' + createdId)).status, 200);
  const updated = await request('PUT', '/api/empresas/' + createdId, { nombre: 'EP3 actualizada', industria: 'Prueba', plan: 'Verificado' });
  check('Actualizar', updated.status, 200);
  check('Datos actualizados', (await updated.json()).nombre, 'EP3 actualizada');
  check('Nombre vacio rechazado', (await request('POST', '/api/empresas', { nombre: '' })).status, 400);
  check('Sin CSRF rechazado', (await request('POST', '/api/empresas', { nombre: 'No crear' }, 'none')).status, 403);
  check('CSRF invalido rechazado', (await request('POST', '/api/empresas', { nombre: 'No crear' }, 'invalid')).status, 403);
  check('Eliminar', (await request('DELETE', '/api/empresas/' + createdId)).status, 204);
  check('Eliminada devuelve 404', (await request('GET', '/api/empresas/' + createdId)).status, 404);
  createdId = undefined;
  check('Sin registros residuales', (await (await request('GET', '/api/empresas')).json()).length, initialCount);
  check('Actuator fuera del proxy', (await fetch(base + '/actuator/prometheus')).status, 404);
  const correlation = {};
  for (const service of ['ep02-backend', 'ep02-frontend']) {
    for (let attempt = 0; attempt < 20; attempt++) {
      const log = execFileSync(docker, ['compose', '-p', 'ep2-local', 'logs', '--no-color', '--since', '2m', service], { cwd: root, encoding: 'utf8' });
      correlation[service] = log.split('\n').filter(line => line.includes(requestId));
      if (correlation[service].length) break;
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    check('Correlacion ' + service, correlation[service].length > 0, true);
  }
  const board = JSON.parse(fs.readFileSync(path.join(root, 'observability/grafana/dashboards/empresas.json'), 'utf8'));
  const queries = [];
  for (const panel of board.panels) {
    const expr = panel.targets[0].expr.replaceAll('$environment', 'local').replaceAll('$__range', '30m');
    const loki = panel.datasource.uid === 'loki';
    const route = loki ? (panel.type === 'logs' ? '/loki/api/v1/query_range' : '/loki/api/v1/query') : '/api/v1/query';
    const response = await fetch((loki ? 'http://127.0.0.1:3100' : 'http://127.0.0.1:9090') + route + '?query=' + encodeURIComponent(expr) + '&limit=100');
    const data = await response.json();
    check('Consulta: ' + panel.title, data.status, 'success');
    const rows = data.data?.result || [];
    queries.push({ panel: panel.title, expression: expr, rows });
    check('Datos: ' + panel.title, rows.length > 0, true);
  }
  const services = await (await fetch('http://127.0.0.1:3100/loki/api/v1/label/service/values')).json();
  for (const name of ['backend', 'frontend', 'db']) check('Logs Loki: ' + name, services.data.includes(name), true);
  fs.writeFileSync(path.join(output, 'correlation.json'), JSON.stringify({ requestId, logs: correlation }, null, 2));
  fs.writeFileSync(path.join(output, 'dashboard-queries.json'), JSON.stringify(queries, null, 2));
}

fs.mkdirSync(output, { recursive: true });
try {
  await verify();
  console.log(`${checks.length} verificaciones reales aprobadas: CRUD, CSRF, correlacion y consultas de los 15 paneles.`);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
} finally {
  if (createdId !== undefined) await request('DELETE', '/api/empresas/' + createdId);
  fs.writeFileSync(path.join(output, 'verification.json'), JSON.stringify({ timestamp: new Date().toISOString(), scope: 'local', checks }, null, 2));
}
