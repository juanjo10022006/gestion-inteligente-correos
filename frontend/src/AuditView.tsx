import { useEffect, useState } from 'react';
import { ApiError, request } from './api';

type AuditEvent = {
  action: string;
  messageId: string;
  actorUserId: string;
  createdAt: string;
  reason: string | null;
};

const actions: Record<string, string> = {
  MENSAJE_REGISTRADO: 'Correo registrado',
  MENSAJE_CLASIFICADO: 'Clasificación automática',
  CLASIFICACION_EN_REVISION: 'Envío a revisión',
  CLASIFICACION_NO_DISPONIBLE: 'IA no disponible',
  CLASIFICACION_MANUAL: 'Asignación manual',
  GESTION_INICIADA: 'Gestión iniciada',
  MENSAJE_CERRADO: 'Correo cerrado',
};
const dateFormat = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });

export function AuditView({ token, initialMessageId, onLogout }: {
  token: string;
  initialMessageId: string;
  onLogout: (notice: string) => void;
}) {
  const [input, setInput] = useState(initialMessageId);
  const [messageId, setMessageId] = useState(initialMessageId);
  const [events, setEvents] = useState<AuditEvent[]>();
  const [revision, refresh] = useState(0);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setEvents(undefined);
    setError('');
    const params = new URLSearchParams({ limit: '50' });
    if (messageId) params.set('messageId', messageId);
    request<{ items: AuditEvent[] }>('/audit-events?' + params, token).then(({ items }) => {
      if (active) setEvents(items);
    }).catch((error: unknown) => {
      if (!active) return;
      if (error instanceof ApiError && error.status === 401) onLogout(error.message);
      else setError(error instanceof Error ? error.message : 'No se pudo consultar la auditoría.');
    });
    return () => { active = false; };
  }, [token, messageId, revision, onLogout]);

  return <main className="workspace">
    <header className="workspace-title">
      <div><h1>Auditoría</h1><p className="muted">Últimos 50 eventos de los correos.</p></div>
      <button onClick={() => refresh((value) => value + 1)}>Actualizar</button>
    </header>
    <section className="audit-panel" aria-label="Eventos de auditoría">
      <form className="audit-filter" onSubmit={(event) => {
        event.preventDefault();
        setMessageId(input.trim().toLowerCase());
      }}>
        <label>ID del correo
          <input value={input} onChange={(event) => setInput(event.currentTarget.value)}
            pattern="[a-fA-F0-9]{24}" maxLength={24} title="24 caracteres hexadecimales" />
        </label>
        <button className="primary">Filtrar</button>
        {messageId && <button type="button" onClick={() => { setInput(''); setMessageId(''); }}>Quitar filtro</button>}
      </form>
      {error ? <div className="empty"><p className="notice" role="alert">{error}</p></div>
        : !events ? <p className="empty muted" role="status">Cargando eventos…</p>
        : events.length === 0 ? <p className="empty muted">No hay eventos para esta consulta.</p>
        : <div className="audit-scroll" tabIndex={0} role="region" aria-label="Tabla de eventos">
          <table className="audit-table">
            <thead><tr><th scope="col">Fecha</th><th scope="col">Evento</th><th scope="col">Actor</th>
              <th scope="col">Correo</th><th scope="col">Motivo</th></tr></thead>
            <tbody>{events.map((event) => <tr key={event.messageId + ':' + event.action}>
              <td><time dateTime={event.createdAt}>{dateFormat.format(new Date(event.createdAt))}</time></td>
              <td>{actions[event.action] ?? event.action}</td>
              <td>{event.actorUserId === 'SISTEMA' ? 'Sistema' : event.actorUserId}</td>
              <td><button className="audit-id" onClick={() => { setInput(event.messageId); setMessageId(event.messageId); }}
                aria-label={'Filtrar por correo ' + event.messageId}>{event.messageId}</button></td>
              <td>{event.reason ?? '—'}</td>
            </tr>)}</tbody>
          </table>
        </div>}
    </section>
  </main>;
}
