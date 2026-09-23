export class ApiError extends Error {
  constructor(message, status, detail) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

async function request(path, { method = 'GET', body, token, headers } = {}) {
  const res = await fetch(path, {
    method,
    // Один и тот же URL может звучать и без токена (аноним), и с ним
    // (авторизован) — а бэкенд не шлёт Vary: Authorization, так что браузер
    // не знает, что кэш нужно различать по заголовку. no-store — не потому
    // что данные часто меняются, а чтобы разные принципалы никогда не
    // получали чужой закэшированный ответ на один и тот же путь.
    cache: 'no-store',
    headers: {
      ...(body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  })

  const isJson = res.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await res.json().catch(() => null) : null

  if (!res.ok) {
    const detail = payload?.detail ?? res.statusText
    throw new ApiError(typeof detail === 'string' ? detail : 'Ошибка запроса', res.status, detail)
  }

  return payload
}

// multipart/form-data — свой путь в обход request(), потому что там тело
// всегда уходит как JSON (Content-Type: application/json).
async function upload(path, file, { token } = {}) {
  const form = new FormData()
  form.append('file', file)
  const res = await fetch(path, {
    method: 'POST',
    cache: 'no-store',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    body: form,
  })
  const isJson = res.headers.get('content-type')?.includes('application/json')
  const payload = isJson ? await res.json().catch(() => null) : null
  if (!res.ok) {
    const detail = payload?.detail ?? res.statusText
    throw new ApiError(typeof detail === 'string' ? detail : 'Ошибка запроса', res.status, detail)
  }
  return payload
}

export const http = {
  get: (path, options) => request(path, { ...options, method: 'GET' }),
  post: (path, body, options) => request(path, { ...options, method: 'POST', body }),
  put: (path, body, options) => request(path, { ...options, method: 'PUT', body }),
  patch: (path, body, options) => request(path, { ...options, method: 'PATCH', body }),
  delete: (path, options) => request(path, { ...options, method: 'DELETE' }),
  upload,
}
