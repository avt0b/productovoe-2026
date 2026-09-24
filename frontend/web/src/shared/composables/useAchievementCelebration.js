import { ref } from 'vue'

// Синглтон-состояние по образцу useOnboarding.js: один экземпляр на всё
// приложение, AchievementCelebration.vue монтируется один раз в App.vue и
// слушает его, а любой компонент (сейчас — AwardsBadges.vue) может вызвать
// celebrate() из любого места, не зная про разметку оверлея.
const active = ref(false)
const title = ref('')
let hideTimer = null

export function useAchievementCelebration() {
  function celebrate(achievementTitle) {
    title.value = achievementTitle
    active.value = true
    clearTimeout(hideTimer)
    hideTimer = setTimeout(() => {
      active.value = false
    }, 2000)
  }

  return { active, title, celebrate }
}
