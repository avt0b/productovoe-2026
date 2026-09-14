import { reactive, readonly } from 'vue'
import * as authApi from './api.js'

const STORAGE_KEY = 'marshruty.auth.session'

function loadStoredTokens() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function persistTokens(tokens) {
  if (tokens) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tokens))
  } else {
    localStorage.removeItem(STORAGE_KEY)
  }
}

const stored = loadStoredTokens()

const state = reactive({
  accessToken: stored?.access_token ?? null,
  refreshToken: stored?.refresh_token ?? null,
  user: null,
  status: 'idle', // idle | loading | authenticated | error
  error: '',
})

async function hydrate() {
  if (!state.accessToken) return
  state.status = 'loading'
  try {
    state.user = await authApi.me(state.accessToken)
    state.status = 'authenticated'
  } catch {
    // access token expired/invalid — drop the stale session
    state.accessToken = null
    state.refreshToken = null
    state.user = null
    state.status = 'idle'
    persistTokens(null)
  }
}

if (state.accessToken) {
  hydrate()
}

async function login({ email, password }) {
  state.status = 'loading'
  state.error = ''
  try {
    const tokens = await authApi.login({ email, password })
    state.accessToken = tokens.access_token
    state.refreshToken = tokens.refresh_token
    persistTokens(tokens)
    state.user = await authApi.me(state.accessToken)
    state.status = 'authenticated'
    return state.user
  } catch (err) {
    state.status = 'error'
    state.error = err.detail ?? err.message
    throw err
  }
}

async function register({ email, password, role }) {
  state.status = 'loading'
  state.error = ''
  try {
    await authApi.register({ email, password, role })
    return login({ email, password })
  } catch (err) {
    state.status = 'error'
    state.error = err.detail ?? err.message
    throw err
  }
}

async function logout() {
  if (state.refreshToken) {
    try {
      await authApi.logout(state.refreshToken)
    } catch {
      // best-effort: still clear the local session
    }
  }
  state.accessToken = null
  state.refreshToken = null
  state.user = null
  state.status = 'idle'
  persistTokens(null)
}

export function useAuthSession() {
  return {
    session: readonly(state),
    login,
    register,
    logout,
  }
}
