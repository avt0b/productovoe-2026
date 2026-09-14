// Соответствует enum Role в auth_service (core/models/user.py).
export const ROLE_LABELS = {
  family: 'Родитель / семейный режим',
  searcher: 'Поисковик-исследователь',
  local_historian: 'Краевед',
  mentor: 'Наставник',
  moderator: 'Модератор архива',
}

export function roleLabel(role) {
  return ROLE_LABELS[role] ?? role
}
