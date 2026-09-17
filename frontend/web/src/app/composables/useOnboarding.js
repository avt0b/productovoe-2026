import { ref } from 'vue'

const STORAGE_KEY = 'marshruty.onboarding.seen'

function readSeen() {
  try {
    return localStorage.getItem(STORAGE_KEY) === '1'
  } catch {
    return true // localStorage недоступен (приватный режим и т.п.) — не мешаем пользователю
  }
}

function writeSeen() {
  try {
    localStorage.setItem(STORAGE_KEY, '1')
  } catch {
    // некритично: гайд в этом случае будет появляться заново — не страшно
  }
}

const showGuide = ref(!readSeen())

export function useOnboarding() {
  function dismiss() {
    showGuide.value = false
    writeSeen()
  }

  function reopen() {
    showGuide.value = true
  }

  return { showGuide, dismiss, reopen }
}
