import { useEffect, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, request } from './api';

type Role = 'OPERADOR' | 'ADMINISTRADOR';
type User = { id: string; username: string; role: Role; active: boolean; activated: boolean };
type UserPage = { items: User[]; total: number; pageSize: number };
type Created = { user: User; temporaryCredential: string; credentialExpiresAt: string };

function EditUser({ user, save, renew }: {
  user: User; save: (user: User, role: Role, active: boolean) => Promise<void>;
  renew: (user: User) => Promise<void>;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    setBusy(true);
    setError('');
    try {
      await save(user, fields.get('role') as Role, fields.get('active') === 'on');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo actualizar.');
    } finally { setBusy(false); }
  }
  return <form className="user-row stack" onSubmit={submit}>
    <h3>{user.username}</h3>
    <p>{user.activated ? 'Cuenta activada' : 'Pendiente de activación'}</p>
    <label>Rol de {user.username}<select name="role" defaultValue={user.role}>
      <option value="OPERADOR">Operador</option><option value="ADMINISTRADOR">Administrador</option>
    </select></label>
    <label><input type="checkbox" name="active" defaultChecked={user.active} /> Cuenta habilitada</label>
    {error && <p className="notice" role="alert">{error}</p>}
    <button disabled={busy}>{busy ? 'Guardando…' : 'Guardar cuenta'}</button>
    {!user.activated && <button type="button" disabled={busy} onClick={async () => {
      if (!window.confirm('Se invalidará la credencial anterior. ¿Renovar la credencial pendiente?')) return;
      setBusy(true); setError('');
      try { await renew(user); }
      catch (err) { setError(err instanceof Error ? err.message : 'No se pudo renovar.'); }
      finally { setBusy(false); }
    }}>Renovar credencial pendiente</button>}
  </form>;
}

export function UsersView({ token, onLogout }: { token: string; onLogout: (notice?: string) => void }) {
  const [list, setList] = useState<UserPage>();
  const [page, setPage] = useState(1);
  const [revision, refresh] = useState(0);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<Created>();
  const [feedback, setFeedback] = useState('');
  function failure(err: unknown) {
    if (err instanceof ApiError && err.status === 401) onLogout(err.message);
    else setError(err instanceof Error ? err.message : 'No se pudo completar la operación.');
  }
  useEffect(() => {
    let active = true;
    setList(undefined);
    request<UserPage>(`/users?page=${page}&pageSize=10`, token).then(data => {
      if (active) setList(data);
    }).catch(err => {
      if (!active) return;
      if (err instanceof ApiError && err.status === 401) onLogout(err.message);
      else setError(err instanceof Error ? err.message : 'No se pudieron consultar las cuentas.');
    });
    return () => { active = false; };
  }, [token, page, revision, onLogout]);

  async function create(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    setBusy(true);
    setError('');
    setFeedback('');
    setCreated(undefined);
    try {
      const result = await request<Created>('/users', token, { method: 'POST', body: JSON.stringify({
        username: String(fields.get('username')).trim(), role: fields.get('role'),
        active: fields.get('active') === 'on',
      }) });
      setCreated(result);
      form.reset();
      refresh(value => value + 1);
    } catch (err) { failure(err); }
    finally { setBusy(false); }
  }

  return <main className="workspace stack">
    <h1>Usuarios</h1>
    {error && <p className="notice" role="alert">{error}</p>}
    {feedback && <p role="status" className="confirmation">{feedback}</p>}
    {created && <section className="prediction stack" aria-label="Credencial de un uso">
      <h2>Cuenta creada: {created.user.username}</h2>
      <p>Entrega esta credencial por el canal aprobado. Solo se muestra ahora y no podrá consultarse de nuevo.</p>
      <code className="one-time-credential">{created.temporaryCredential}</code>
      <p>Vence: {new Date(created.credentialExpiresAt).toLocaleString('es-CO')}</p>
      <button onClick={() => setCreated(undefined)}>Ocultar credencial</button>
    </section>}
    <form className="form-card stack" onSubmit={create}>
      <h2>Crear cuenta</h2>
      <label>Identificador<input name="username" required maxLength={64} pattern="[A-Za-z0-9._-]+"
        autoComplete="off" /></label>
      <label>Rol<select name="role" defaultValue="OPERADOR">
        <option value="OPERADOR">Operador</option><option value="ADMINISTRADOR">Administrador</option>
      </select></label>
      <label><input name="active" type="checkbox" defaultChecked /> Cuenta habilitada</label>
      <button className="primary" disabled={busy || !!created}>
        {busy ? 'Creando…' : 'Crear y mostrar credencial'}
      </button>
    </form>
    <p className="muted">Cambiar el rol o estado invalida las sesiones anteriores. No puedes degradar ni desactivar tu propia cuenta.</p>
    {!list ? <p role="status">Cargando usuarios…</p> :
      <section className="users-grid" aria-label="Cuentas">
        {list.items.map(user => <EditUser key={user.id + user.role + user.active} user={user}
          renew={async current => {
            if (created) throw new Error('Oculta primero la credencial que acabas de recibir.');
            try {
              setCreated(await request<Created>('/users/' + encodeURIComponent(current.username) + '/activation-credential',
                token, { method: 'POST' }));
            } catch (err) {
              if (err instanceof ApiError && err.status === 401) onLogout(err.message);
              throw err;
            }
          }}
          save={async (current, role, active) => {
            try {
              await request<User>('/users/' + encodeURIComponent(current.username), token, {
                method: 'PATCH', body: JSON.stringify({ role, active }),
              });
              setFeedback('Cuenta actualizada. Las sesiones anteriores quedaron invalidadas.');
              refresh(value => value + 1);
            } catch (err) {
              if (err instanceof ApiError && err.status === 401) onLogout(err.message);
              throw err;
            }
          }} />)}
      </section>}
    {list && list.total > list.pageSize && <nav className="pagination" aria-label="Paginación de usuarios">
      <button disabled={page === 1} onClick={() => setPage(value => value - 1)}>Anterior</button>
      <span>Página {page}</span>
      <button disabled={page * list.pageSize >= list.total} onClick={() => setPage(value => value + 1)}>Siguiente</button>
    </nav>}
  </main>;
}
