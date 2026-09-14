import { reactive, readonly } from 'vue'
import { useAuthSession } from '@modules/auth'
import * as profileApi from './api.js'

const state = reactive({
  data: null,
  status: 'idle', // idle | loading | loaded | error
  error: '',
})

async function loadMyProfile() {
  const { session } = useAuthSession()
  if (!session.accessToken) return
  state.status = 'loading'
  state.error = ''
  try {
    state.data = await profileApi.getMyProfile(session.accessToken)
    state.status = 'loaded'
  } catch (err) {
    state.status = 'error'
    state.error = err.detail ?? err.message
  }
}

async function saveMyProfile(patch) {
  const { session } = useAuthSession()
  if (!session.accessToken) throw new Error('Не авторизован')
  state.data = await profileApi.updateMyProfile(session.accessToken, patch)
  return state.data
}

export function useProfileStore() {
  return {
    profile: readonly(state),
    loadMyProfile,
    saveMyProfile,
  }
}
