/**
 * Организации — то, что `search_hq_service` хранит как «отряды»: поисковый
 * отряд, музей, школа или клуб. У всех одно и то же — город, выезды, сборы,
 * командир; различаются только видом. Нужны «Штабу» (завести и править) и
 * профилю (заявка на роль: к какой организации человек себя относит).
 */

export type OrganizationKind = 'squad' | 'museum' | 'school'

export const ORGANIZATION_KINDS: Record<OrganizationKind, { title: string; many: string; icon: string }> = {
  squad: { title: 'Поисковый отряд', many: 'Отряды', icon: 'flag' },
  museum: { title: 'Музей', many: 'Музеи', icon: 'museum' },
  school: { title: 'Школа или клуб', many: 'Школы', icon: 'school' },
}

/** Старый сервис вида не присылает — тогда это отряд, как было до музеев и школ. */
export function organizationKind(value: string | null | undefined): OrganizationKind {
  return value === 'museum' || value === 'school' ? value : 'squad'
}

function normalize(text: string): string {
  return text.trim().toLowerCase().replaceAll('ё', 'е')
}

/**
 * Относится ли организация к городу человека. Город у обоих — свободная строка
 * («Орёл», «г. Орел», «Орёл, Орловская обл.»), поэтому сравниваем вхождением
 * без учёта регистра и «ё».
 */
export function sameCity(region: string, city: string): boolean {
  const a = normalize(region)
  const b = normalize(city)
  return Boolean(a && b) && (a.includes(b) || b.includes(a))
}
