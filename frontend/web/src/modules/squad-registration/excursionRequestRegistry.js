import { reactive, readonly } from 'vue'

// В search_hq_service нет сущности ExcursionRequest вообще (модуль 5 ТЗ,
// см. README сервиса и BACKEND_INTEGRATION.md Push 9) — только localStorage
// на фронте, без притворства, что заявка ушла на сервер.
const STORAGE_KEY = 'marshruty.squad-registration.excursion-requests'

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

function addRequest(payload) {
  const entry = {
    id: crypto.randomUUID(),
    status: 'pending', // pending | accepted | declined — как только появится реальный бэкенд
    created_at: new Date().toISOString(),
    ...payload,
  }
  state.items = [entry, ...state.items]
  persist(state.items)
  return entry
}

export function useExcursionRequestRegistry() {
  return {
    requests: readonly(state).items,
    addRequest,
  }
}
