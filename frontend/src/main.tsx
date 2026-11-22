import { useEffect, useState } from 'react';
import type { FormEvent, ReactNode } from 'react';
import { createRoot } from 'react-dom/client';
import { ApiError, departments, formFilters, request } from './api';
import type { Department, Detail, Message, MessagePage, Session } from './api';
import { AuditView } from './AuditView';
import './styles.css';

const states: Record<string, string> = {
  RECIBIDO: 'Recibido',
  PENDIENTE_CLASIFICACION: 'Pendiente de clasificación',
  PENDIENTE_REVISION: 'Pendiente de revisión',
  CLASIFICADO: 'Clasificado',
  EN_GESTION: 'En gestión',
  CERRADO: 'Cerrado',
};
const dateFormat = new Intl.DateTimeFormat('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
const percentFormat = new Intl.NumberFormat('es-CO', { style: 'percent', maximumFractionDigits: 1 });
const eligible = new Set(['PENDIENTE_REVISION', 'PENDIENTE_CLASIFICACION', 'CLASIFICADO', 'EN_GESTION']);
const errorText = (error: unknown) => error instanceof Error ? error.message : 'Ocurrió un error inesperado.';

function Brand() {
  return <div className="brand"><span className="brand-mark" aria-hidden="true">✉</span> Gestión de correos</div>;
}

function Status({ value }: { value: string }) {
  return <span className={'status status-' + value.toLowerCase()}>{states[value] ?? value}</span>;
}

function Notice({ children }: { children: ReactNode }) {
  return <p className="notice" role="alert">{children}</p>;
}

function Login({ onLogin, notice }: { onLogin: (session: Session) => void; notice: string }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    setBusy(true);
    setError('');
    try {
      const session = await request<Session>('/auth/login', undefined, {
        method: 'POST',
        body: JSON.stringify({ username: String(fields.get('username')).trim(), password: fields.get('password') }),
      });
      onLogin(session);
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }

  return <main className="login-layout">
    <div className="login-brand"><Brand /></div>
    <form className="login-card stack" onSubmit={submit}>
      <div><h1>Iniciar sesión</h1><p className="muted">Accede con tu cuenta del proyecto.</p></div>
      {(error || notice) && <Notice>{error || notice}</Notice>}
      <label>Usuario<input name="username" autoComplete="username" required maxLength={64} /></label>
      <label>Contraseña<input name="password" type="password" autoComplete="current-password" required maxLength={256} /></label>
      <button className="primary" disabled={busy}>{busy ? 'Ingresando…' : 'Ingresar'}</button>
    </form>
  </main>;
}

function MessageForm({ save, cancel }: {
  save: (values: { subject: string; body: string; sender?: string }) => Promise<void>;
  cancel: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const subject = String(fields.get('subject')).trim();
    const body = String(fields.get('body')).trim();
    const sender = String(fields.get('sender')).trim();
    if (subject.length < 3 || body.length < 10) {
      setError('El asunto requiere al menos 3 caracteres y el contenido al menos 10.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await save({ subject, body, sender: sender || undefined });
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  return <form className="form-card stack" onSubmit={submit}>
    <div><h2>Registrar correo</h2><p className="muted">Usa datos ficticios para esta prueba.</p></div>
    {error && <Notice>{error}</Notice>}
    <label>Asunto<input name="subject" required minLength={3} maxLength={160} /></label>
    <label>Remitente <span className="muted">(opcional)</span><input name="sender" /></label>
    <label>Contenido<textarea name="body" required minLength={10} maxLength={10000} rows={7} /></label>
    <div className="actions">
      <button className="primary" disabled={busy}>{busy ? 'Registrando…' : 'Registrar y clasificar'}</button>
      <button type="button" disabled={busy} onClick={cancel}>Cancelar</button>
    </div>
  </form>;
}

function ReviewForm({ message, save }: {
  message: Detail;
  save: (department: Department, reason: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const reason = String(fields.get('reason')).trim();
    if (reason.length < 5) {
      setError('Escribe un motivo de al menos 5 caracteres.');
      return;
    }
    setError('');
    setBusy(true);
    try {
      await save(fields.get('department') as Department, reason);
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  return <form className="stack review" onSubmit={submit}>
    <h3>Asignación manual</h3>
    {error && <Notice>{error}</Notice>}
    <label>Departamento<select name="department" required
      defaultValue={message.department ?? message.prediction?.category ?? ''}>
      <option value="" disabled>Selecciona un departamento</option>
      {Object.entries(departments).map(([value, name]) => <option key={value} value={value}>{name}</option>)}
    </select></label>
    <label>Motivo<textarea name="reason" required minLength={5} maxLength={500} rows={3} /></label>
    <button className="primary" disabled={busy}>{busy ? 'Guardando…' : 'Guardar asignación'}</button>
  </form>;
}

function StatusForm({ closing, save }: {
  closing: boolean;
  save: (status: 'EN_GESTION' | 'CERRADO', reason?: string) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const reason = String(new FormData(event.currentTarget).get('reason') ?? '').trim();
    if (closing && reason.length < 5) {
      setError('Escribe una resolución de al menos 5 caracteres.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await save(closing ? 'CERRADO' : 'EN_GESTION', reason || undefined);
    } catch (error) {
      setError(errorText(error));
    } finally {
      setBusy(false);
    }
  }
  return <form className="stack review" onSubmit={submit}>
    {error && <Notice>{error}</Notice>}
    {closing && <label>Resolución del correo
      <textarea name="reason" required minLength={5} maxLength={500} rows={3} />
    </label>}
    <button className="primary" disabled={busy}>{busy ? 'Guardando…' : closing ? 'Cerrar correo' : 'Iniciar gestión'}</button>
  </form>;
}

function MessageDetail({ message, save, saveStatus, showAudit }: {
  message: Detail;
  save: (department: Department, reason: string) => Promise<void>;
  saveStatus: (status: 'EN_GESTION' | 'CERRADO', reason?: string) => Promise<void>;
  showAudit?: () => void;
}) {
  const prediction = message.prediction;
  return <section className="detail stack" aria-labelledby="message-subject">
    <header>
      <Status value={message.status} />
      <h2 id="message-subject" tabIndex={-1}>{message.subject}</h2>
      <p className="muted">{message.sender ? message.sender + ' · ' : ''}{dateFormat.format(new Date(message.createdAt))}</p>
    </header>
    <p className="message-body">{message.body}</p>
    <section className="prediction">
      <h3>Clasificación</h3>
      <dl>
        <div><dt>Área asignada</dt><dd>{message.department ? departments[message.department] : 'Sin asignar'}</dd></div>
        {message.assignmentOrigin && <div><dt>Origen de asignación</dt>
          <dd>{message.assignmentOrigin === 'MANUAL' ? 'Manual' : 'IA'}</dd></div>}
        {prediction && <>
          <div><dt>Sugerencia de IA</dt><dd>{departments[prediction.category]}</dd></div>
          <div><dt>Confianza</dt><dd>{percentFormat.format(prediction.confidence)}</dd></div>
          <div><dt>Modelo</dt><dd className="model">{prediction.modelVersion}</dd></div>
        </>}
      </dl>
      {!prediction && <p className="muted">Este correo aún no tiene una predicción.</p>}
    </section>
    {(message.status === 'CLASIFICADO' || message.status === 'EN_GESTION') &&
      <StatusForm key={message.id + message.status} closing={message.status === 'EN_GESTION'} save={saveStatus} />}
    {message.resolution && <section className="prediction"><h3>Resolución</h3>
      <p className="message-body">{message.resolution}</p></section>}
    {eligible.has(message.status) && <ReviewForm key={message.id + message.department} message={message} save={save} />}
    {showAudit && <div className="actions"><button onClick={showAudit}>Ver auditoría del correo</button></div>}
  </section>;
}

function Workspace({ session, onLogout }: { session: Session; onLogout: (notice?: string) => void }) {
  const [list, setList] = useState<MessagePage>();
  const [detail, setDetail] = useState<Detail>();
  const [selected, setSelected] = useState<string>();
  const [composing, setComposing] = useState(false);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [revision, refresh] = useState(0);
  const [listError, setListError] = useState('');
  const [detailError, setDetailError] = useState('');
  const [feedback, setFeedback] = useState('');
  const [auditFilter, setAuditFilter] = useState<string>();
  const isAdmin = session.user.role === 'ADMINISTRADOR';
  const token = session.accessToken;

  useEffect(() => {
    let active = true;
    const filters = new URLSearchParams(search);
    filters.set('page', String(page));
    filters.set('pageSize', '10');
    setList(undefined);
    setListError('');
    request<MessagePage>('/messages?' + filters, token).then((data) => {
      if (active) setList(data);
    }).catch((error: unknown) => {
      if (!active) return;
      if (error instanceof ApiError && error.status === 401) onLogout(error.message);
      else setListError(errorText(error));
    });
    return () => { active = false; };
  }, [token, page, search, revision, onLogout]);

  useEffect(() => {
    if (!selected || composing) return;
    let active = true;
    setDetail(undefined);
    setDetailError('');
    request<Detail>('/messages/' + selected, token).then((data) => {
      if (active) {
        setDetail(data);
        requestAnimationFrame(() => document.getElementById('message-subject')?.focus());
      }
    }).catch((error: unknown) => {
      if (!active) return;
      if (error instanceof ApiError && error.status === 401) onLogout(error.message);
      else setDetailError(errorText(error));
    });
    return () => { active = false; };
  }, [token, selected, composing, onLogout]);

  async function mutate<T>(path: string, method: string, payload: object) {
    try {
      const result = await request<T>(path, token, { method, body: JSON.stringify(payload) });
      refresh((value) => value + 1);
      return result;
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) onLogout(error.message);
      throw error;
    }
  }

  return <>
    <header className="topbar">
      <Brand />
      {isAdmin && <nav className="admin-nav" aria-label="Secciones">
        <button aria-current={auditFilter === undefined ? 'page' : undefined} onClick={() => setAuditFilter(undefined)}>Bandeja</button>
        <button aria-current={auditFilter !== undefined ? 'page' : undefined} onClick={() => setAuditFilter('')}>Auditoría</button>
      </nav>}
      <div className="account"><span>{session.user.id}<small>{session.user.role === 'OPERADOR' ? 'Operador' : 'Administrador'}</small></span>
        <button onClick={() => onLogout()}>Cerrar sesión</button></div>
    </header>
    {isAdmin && auditFilter !== undefined && <AuditView key={auditFilter} token={token} initialMessageId={auditFilter} onLogout={onLogout} />}
    <main className="workspace" hidden={auditFilter !== undefined}>
      <header className="workspace-title">
        <div><h1>Bandeja de entrada</h1>{list && <p className="muted">{list.total} {list.total === 1 ? 'correo' : 'correos'}</p>}</div>
        <button className="primary" onClick={() => { setComposing(true); setFeedback(''); }}>＋ Registrar correo</button>
      </header>
      {feedback && <p className="confirmation" role="status">{feedback}</p>}
      <div className="workspace-grid">
        <section className="inbox" aria-label="Correos">
          <form className="stack inbox-filters" role="search" onSubmit={(event) => {
            event.preventDefault();
            setSearch(formFilters(event.currentTarget));
            setPage(1);
          }}>
            <label>Texto<input name="text" type="search" placeholder="Asunto o contenido" maxLength={160} /></label>
            <label>Estado<select name="status"><option value="">Todos</option>
              {Object.entries(states).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select></label>
            <label>Departamento<select name="department"><option value="">Todos</option>
              {Object.entries(departments).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select></label>
            <label>Desde (hora local)<input type="datetime-local" name="dateFrom" /></label>
            <label>Hasta (hora local)<input type="datetime-local" name="dateTo" /></label>
            <div className="actions"><button>Filtrar</button>
              <button type="reset" onClick={() => { setSearch(''); setPage(1); }}>Limpiar</button></div>
          </form>
          {listError ? <div className="empty"><Notice>{listError}</Notice><button onClick={() => refresh(revision + 1)}>Reintentar</button></div>
            : !list ? <p className="empty muted" role="status">Cargando correos…</p>
            : list.items.length === 0 ? <p className="empty muted">{search ? 'No hay correos que coincidan.' : 'Aún no hay correos registrados.'}</p>
            : <>
              <ul className="messages">{list.items.map((item) => <li key={item.id}>
                <button className="message-row" aria-current={selected === item.id && !composing ? 'true' : undefined}
                  onClick={() => { setSelected(item.id); setComposing(false); setFeedback(''); }}>
                  <strong>{item.subject}</strong>
                  <span className="row-meta"><Status value={item.status} /><time dateTime={item.createdAt}>{dateFormat.format(new Date(item.createdAt))}</time></span>
                </button>
              </li>)}</ul>
              {list.total > list.pageSize && <nav className="pagination" aria-label="Paginación">
                <button disabled={page === 1} onClick={() => setPage(page - 1)}>Anterior</button>
                <span>Página {page}</span>
                <button disabled={page * list.pageSize >= list.total} onClick={() => setPage(page + 1)}>Siguiente</button>
              </nav>}
            </>}
        </section>
        <div className="content">
          {composing ? <MessageForm cancel={() => setComposing(false)} save={async (values) => {
            const message = await mutate<Message>('/messages', 'POST', values);
            setSelected(message.id);
            setComposing(false);
            setFeedback('Correo registrado.');
          }} /> : detail && detail.id === selected ? <MessageDetail message={detail}
            saveStatus={async (status, reason) => {
              const updated = await mutate<Detail>('/messages/' + detail.id + '/status', 'PATCH', { status, reason });
              setDetail((current) => current?.id === updated.id ? updated : current);
              setFeedback(status === 'CERRADO' ? 'Correo cerrado.' : 'El correo quedó en gestión.');
            }}
            showAudit={isAdmin ? () => setAuditFilter(detail.id) : undefined} save={async (department, reason) => {
            const updated = await mutate<Detail>('/messages/' + detail.id + '/classification', 'PATCH', { department, reason });
            setDetail((current) => current?.id === updated.id ? updated : current);
            setFeedback('Departamento asignado. El correo quedó en gestión.');
          }} /> : selected ? <div className="empty">{detailError ? <Notice>{detailError}</Notice> : <p role="status">Cargando detalle…</p>}</div>
            : <div className="detail-empty"><span aria-hidden="true">✉</span><p>Selecciona un correo para ver su detalle.</p></div>}
        </div>
      </div>
    </main>
  </>;
}

function App() {
  const [session, setSession] = useState<Session>();
  const [notice, setNotice] = useState('');
  const [logout] = useState(() => (message = '') => {
    setSession(undefined);
    setNotice(message);
  });
  return session ? <Workspace session={session} onLogout={logout} /> : <Login onLogin={setSession} notice={notice} />;
}

createRoot(document.getElementById('root')!).render(<App />);
