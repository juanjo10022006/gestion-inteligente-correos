export const departments = {
  FACTURACION: 'Facturación',
  RECURSOS_HUMANOS: 'Recursos Humanos',
  SOPORTE_TECNICO: 'Soporte Técnico',
  VENTAS: 'Ventas',
} as const;

export type Department = keyof typeof departments;

export type Session = {
  accessToken: string;
  user: { id: string; role: 'OPERADOR' | 'ADMINISTRADOR' };
};

export type Message = {
  id: string;
  status: string;
  prediction: { category: Department; confidence: number; modelVersion: string } | null;
  department: Department | null;
};

export type Summary = Message & { subject: string; sender: string | null; createdAt: string };
export type Detail = Summary & {
  body: string;
  resolution: string | null;
  assignmentOrigin: 'IA' | 'MANUAL' | null;
};
export type MessagePage = { items: Summary[]; page: number; pageSize: number; total: number };

export function formFilters(form: HTMLFormElement): string {
  const result = new URLSearchParams();
  new FormData(form).forEach((raw, key) => {
    const value = String(raw).trim();
    if (value) result.set(key, key === 'dateFrom' || key === 'dateTo' ? new Date(value).toISOString() : value);
  });
  return result.toString();
}

export function localDateInput(value: string | null): string {
  if (!value) return '';
  const date = new Date(value);
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

export async function request<T>(path: string, token?: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch('/api/v1' + path, {
      ...options,
      headers: {
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...(token ? { Authorization: 'Bearer ' + token } : {}),
      },
    });
  } catch {
    throw new Error('No se pudo conectar con la API. Intenta de nuevo.');
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    let message = 'No se pudo completar la solicitud. Intenta de nuevo.';
    if (typeof data?.detail === 'string') message = data.detail;
    if (response.status === 422 && typeof data?.detail !== 'string') message = 'Revisa los campos del formulario.';
    if (response.status === 401 && token) message = 'Tu sesión terminó. Vuelve a iniciar sesión.';
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
