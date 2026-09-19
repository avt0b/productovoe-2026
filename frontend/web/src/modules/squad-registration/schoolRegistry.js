import { reactive, readonly } from 'vue'

// В search_hq_service нет ни одной ручки под регистрацию школ/клубов (см.
// BACKEND_INTEGRATION.md, Push 9) — только localStorage на фронте, без
// притворства, что заявка ушла на сервер.
const STORAGE_KEY = 'marshruty.squad-registration.schools'

function load() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

function persist(items) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch {
    // приватный режим браузера / переполненное хранилище — не критично для демо-режима
  }
}

const state = reactive({ items: load() })

function addSchool(payload) {
  const entry = {
    id: crypto.randomUUID(),
    created_at: new Date().toISOString(),
    ...payload,
  }
  state.items = [entry, ...state.items]
  persist(state.items)
  return entry
}

export function useSchoolRegistry() {
  return {
    schools: readonly(state).items,
    addSchool,
  }
}
