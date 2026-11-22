import { useState } from 'react';
import type { FormEvent } from 'react';
import { request } from './api';

export function ActivationForm({ done, cancel }: { done: () => void; cancel: () => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const password = String(fields.get('newPassword'));
    if (password !== fields.get('confirmPassword')) {
      setError('Las contraseñas no coinciden.');
      return;
    }
    if (!password.trim()) {
      setError('La contraseña no puede estar en blanco.');
      return;
    }
    setBusy(true);
    setError('');
    try {
      await request<void>('/auth/activate', undefined, {
        method: 'POST',
        body: JSON.stringify({
          username: String(fields.get('username')).trim(),
          temporaryCredential: fields.get('temporaryCredential'),
          newPassword: password,
        }),
      });
      form.reset();
      done();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se pudo activar la cuenta.');
    } finally {
      setBusy(false);
    }
  }
  return <form className="login-card stack" onSubmit={submit}>
    <h1>Activar cuenta</h1>
    <p>Usa la credencial que te entregó el administrador. Es de un uso y vence en 24 horas.</p>
    {error && <p className="notice" role="alert">{error}</p>}
    <label>Usuario<input name="username" required maxLength={64} autoComplete="username" /></label>
    <label>Credencial temporal<input name="temporaryCredential" type="password" required maxLength={128}
      autoComplete="off" /></label>
    <label>Nueva contraseña<input name="newPassword" type="password" required minLength={12} maxLength={256}
      autoComplete="new-password" /></label>
    <label>Repetir contraseña<input name="confirmPassword" type="password" required minLength={12} maxLength={256}
      autoComplete="new-password" /></label>
    <p className="muted">Entre 12 y 256 caracteres; se permiten espacios, pero no una contraseña en blanco.</p>
    <button className="primary" disabled={busy}>{busy ? 'Activando…' : 'Activar cuenta'}</button>
    <button type="button" onClick={cancel} disabled={busy}>Volver al acceso</button>
  </form>;
}
