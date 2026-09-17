import { ref } from 'vue'

const DESKTOP_QUERY = '(min-width: 1024px)'

const isOpen = ref(true)
const isDesktop = ref(true)

function syncToBreakpoint(matches) {
  isDesktop.value = matches
  isOpen.value = matches
}

const mql = window.matchMedia(DESKTOP_QUERY)
syncToBreakpoint(mql.matches)
mql.addEventListener('change', (event) => syncToBreakpoint(event.matches))

export function useSidebar() {
  function toggle() {
    isOpen.value = !isOpen.value
  }

  function close() {
    isOpen.value = false
  }

  function closeOnMobile() {
    if (!isDesktop.value) isOpen.value = false
  }

  return { isOpen, isDesktop, toggle, close, closeOnMobile }
}
