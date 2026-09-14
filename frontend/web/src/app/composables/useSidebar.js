import { onMounted, onUnmounted, ref } from 'vue'

const DESKTOP_QUERY = '(min-width: 1024px)'

export function useSidebar() {
  const isOpen = ref(true)
  const isDesktop = ref(true)
  let mql

  function syncToBreakpoint(matches) {
    isDesktop.value = matches
    isOpen.value = matches
  }

  function handleChange(event) {
    syncToBreakpoint(event.matches)
  }

  onMounted(() => {
    mql = window.matchMedia(DESKTOP_QUERY)
    syncToBreakpoint(mql.matches)
    mql.addEventListener('change', handleChange)
  })

  onUnmounted(() => {
    mql?.removeEventListener('change', handleChange)
  })

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
