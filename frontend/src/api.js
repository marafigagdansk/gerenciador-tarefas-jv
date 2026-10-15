const TOKEN_KEY = 'gt_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => (t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY))

let unauthorizedHandler = null
export const onUnauthorized = (fn) => { unauthorizedHandler = fn }

export async function api(path, { method = 'GET', body } = {}) {
  const headers = {}
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  if (res.status === 401 && token && unauthorizedHandler) unauthorizedHandler()

  const data = await res.json().catch(() => null)
  if (!res.ok) {
    let msg = 'Erro inesperado.'
    if (data?.detail) {
      msg = Array.isArray(data.detail)
        ? data.detail.map((d) => (d.msg || '').replace(/^Value error, /, '')).join(' ')
        : data.detail
    }
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return data
}

export function formatDoc(digits) {
  const d = (digits || '').replace(/\D/g, '')
  if (d.length === 11) return d.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4')
  if (d.length === 14) return d.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5')
  return digits
}

export function maskDoc(value) {
  const d = value.replace(/\D/g, '').slice(0, 14)
  if (d.length <= 11) {
    return d.replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d)/, '$1.$2').replace(/(\d{3})(\d{1,2})$/, '$1-$2')
  }
  return d
    .replace(/^(\d{2})(\d)/, '$1.$2')
    .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
    .replace(/\.(\d{3})(\d)/, '.$1/$2')
    .replace(/(\d{4})(\d)/, '$1-$2')
}

export const STATUS_LABELS = {
  todo: 'A Fazer',
  in_progress: 'Em Andamento',
  blocked: 'Bloqueada',
  done: 'Concluída',
}
export const PRIORITY_LABELS = { low: 'Baixa', medium: 'Média', high: 'Alta' }
export const ROLE_LABELS = { master: 'Master', collaborator: 'Colaborador' }
