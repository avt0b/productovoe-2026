import { useAchievementCelebration } from '@shared/composables/useAchievementCelebration.js'
import { getMyAchievements } from './api.js'

// Дублирует ACHIEVEMENT_TITLES в user_service/core/models/achievement.py —
// бэкенд отдаёт только code и earned_at.
export const ACHIEVEMENT_TITLES = {
  first_route_completed: 'Первый маршрут пройден',
  archive_helper: 'Помощник архива',
  trip_volunteer: 'Доброволец',
  donor: 'Жертвователь',
}

function seenKey(userId) {
  return `marshruty.achievements-seen.${userId}`
}

function loadSeen(userId) {
  try {
    const raw = localStorage.getItem(seenKey(userId))
    return raw ? new Set(JSON.parse(raw)) : null
  } catch {
    return null
  }
}

function saveSeen(userId, codes) {
  localStorage.setItem(seenKey(userId), JSON.stringify([...codes]))
}

const { celebrate } = useAchievementCelebration()

// Вызывать сразу после любого действия, которое могло начислить ачивку —
// донат, запись на выезд, подтверждение записи «Живой памяти» и т.п. — а не
// только при заходе в профиль. Сравнивает список с бэка с уже виденными в
// этом браузере кодами и салютует за каждый новый (по очереди, если их
// несколько). Возвращает полный список — чтобы AwardsBadges.vue не делал тот
// же запрос второй раз, раз он и так ей нужен для рендера.
export async function checkForNewAchievements(token, userId) {
  const list = await getMyAchievements(token)
  if (!userId) return list

  const currentCodes = new Set(list.map((a) => a.code))
  const seen = loadSeen(userId)
  // seen === null — впервые видим этот профиль в этом браузере: просто
  // запоминаем текущие значки, не салютуем за то, что заслужено раньше.
  if (seen) {
    const newlyEarned = [...currentCodes].filter((code) => !seen.has(code))
    newlyEarned.forEach((code, i) => {
      setTimeout(() => celebrate(ACHIEVEMENT_TITLES[code] ?? code), i * 2200)
    })
  }
  saveSeen(userId, currentCodes)
  return list
}
