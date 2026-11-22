import { useEffect, useState } from 'react';
import { ApiError, formFilters, localDateInput, request } from './api';

type AuditEvent = {
  id: string;
  action: string;
  messageId: string;
  actorUserId: string;
  createdAt: string;
  reason: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  source: 'HISTORICAL' | 'LEGACY';
};

const actions: Record<string, string> = {
  MENSAJE_REGISTRADO: 'Correo registrado',
  MENSAJE_CLASIFICADO: 'Clasificación automática',
  CLASIFICACION_EN_REVISION: 'Envío a revisión',
  CLASIFICACION_NO_DISPONIBLE: 'IA no disponible',
  CLASIFICACION_MANUAL: 'Asignación manual',
  GESTION_INICIADA: 'Gestión iniciada',
  MENSAJE_CERRADO: 'Correo cerrado',
  PREDICCION_REGISTRADA: 'Predicción registrada',
};
const dateFormat = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

export function AuditView({ token, initialMessageId, onLogout }: {
  token: string;
  initialMessageId: string;
  onLogout: (notice: string) => void;
}) {
  const [filters, setFilters] = useState(() => new URLSearchParams(
    initialMessageId ? { messageId: initialMessageId } : {},
  ).toString());
  const [formRevision, resetForm] = useState(0);
  const [events, setEvents] = useState<AuditEvent[]>();
  const [revision, refresh] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setEvents(undefined);
    setError('');
    const params = new URLSearchParams(filters);
    params.set('limit', '100');
    request<{ items: AuditEvent[] }>('/audit-events?' + params, token).then(({ items }) => {
      if (active) setEvents(items);
    }).catch((error: unknown) => {
      if (!active) return;
      if (error instanceof ApiError && error.status === 401) onLogout(error.message);
      else setError(error instanceof Error ? error.message : 'No se pudo consultar la auditoría.');
    });
    return () => { active = false; };
  }, [token, filters, revision, onLogout]);

  return <main className="workspace">
    <header className="workspace-title">
      <div><h1>Auditoría</h1><p className="muted">Hasta 100 eventos coincidentes, más recientes primero.</p></div>
      <button onClick={() => refresh((value) => value + 1)}>Actualizar</button>
    </header>
    <section className="audit-panel" aria-label="Eventos de auditoría">
      <form key={formRevision} className="audit-filter" onSubmit={(event) => {
        event.preventDefault();
        const params = new URLSearchParams(formFilters(event.currentTarget));
        if (params.has('messageId')) params.set('messageId', params.get('messageId')!.toLowerCase());
        setFilters(params.toString());
      }}>
        <label>ID del correo
          <input name="messageId" defaultValue={new URLSearchParams(filters).get('messageId') ?? ''}
            pattern="[a-fA-F0-9]{24}" maxLength={24} title="24 caracteres hexadecimales" />
        </label>
        <label>Actor<input name="actor" maxLength={64} defaultValue={new URLSearchParams(filters).get('actor') ?? ''} /></label>
        <label>Acción<select name="action" defaultValue={new URLSearchParams(filters).get('action') ?? ''}>
          <option value="">Todas</option>
          {Object.entries(actions).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
        </select></label>
        <label>Desde (hora local)<input type="datetime-local" name="dateFrom"
          defaultValue={localDateInput(new URLSearchParams(filters).get('dateFrom'))} /></label>
        <label>Hasta (hora local)<input type="datetime-local" name="dateTo"
          defaultValue={localDateInput(new URLSearchParams(filters).get('dateTo'))} /></label>
        <button className="primary">Filtrar</button>
        <button type="reset" onClick={() => { setFilters(''); resetForm(value => value + 1); }}>Limpiar</button>
      </form>
      {error ? <div className="empty"><p className="notice" role="alert">{error}</p></div>
        : !events ? <p className="empty muted" role="status">Cargando eventos…</p>
        : events.length === 0 ? <p className="empty muted">No hay eventos para esta consulta.</p>
        : <div className="audit-scroll" tabIndex={0} role="region" aria-label="Tabla de eventos">
          <table className="audit-table">
            <thead><tr><th scope="col">Fecha</th><th scope="col">Evento</th><th scope="col">Actor</th>
              <th scope="col">Correo</th><th scope="col">Motivo</th><th scope="col">Cambios</th></tr></thead>
            <tbody>{events.map((event) => <tr key={event.id}>
              <td><time dateTime={event.createdAt}>{dateFormat.format(new Date(event.createdAt))}</time></td>
              <td>{actions[event.action] ?? event.action}</td>
              <td>{event.actorUserId === 'SISTEMA' ? 'Sistema' : event.actorUserId}</td>
              <td><button className="audit-id" onClick={() => {
                const params = new URLSearchParams(filters);
                params.set('messageId', event.messageId);
                setFilters(params.toString());
                resetForm(value => value + 1);
              }}
                aria-label={'Filtrar por correo ' + event.messageId}>{event.messageId}</button></td>
              <td>{event.reason ?? '—'}</td>
              <td>{event.source === 'LEGACY' ? 'Histórico embebido; antes/después no disponible' :
                <details><summary>Antes / después</summary>
                  <pre>{JSON.stringify({ before: event.before, after: event.after }, null, 2)}</pre></details>}</td>
            </tr>)}</tbody>
          </table>
        </div>}
    </section>
  </main>;
}
