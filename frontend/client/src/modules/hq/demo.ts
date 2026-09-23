import type { Need, Squad, Trip } from './data'

/**
 * Демо-штаб на случай, когда `search_hq_service` не ответил: на защите без
 * сети, в APK вне локальной сети. Тот же набор, что в
 * `backend/search_hq_service/scripts/seed_orel.py`, чтобы экран выглядел одинаково.
 */

function inDays(days: number): string {
  const date = new Date()
  date.setDate(date.getDate() + days)
  const pad = (value: number): string => String(value).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

const CREATED = '2026-09-01T00:00:00Z'
const LEADER = 'seed-orel'

const squads: Squad[] = [
  {
    id: 'demo-vysota',
    name: 'Поисковый отряд «Высота»',
    region: 'Орёл',
    description: 'Ищет места гибели десантников 5-го ВДК под Орлом.',
    contact: '',
    leader_id: LEADER,
    created_at: CREATED,
  },
  {
    id: 'demo-rubezh',
    name: 'Поисковый отряд «Рубеж»',
    region: 'Мценск',
    description: 'Работает на рубежах обороны 1941 года по реке Зуше.',
    contact: '',
    leader_id: LEADER,
    created_at: CREATED,
  },
]

const needs: Need[] = [
  {
    id: 'demo-vysota-fuel',
    squad_id: 'demo-vysota',
    kind: 'funds',
    title: 'Поднять бойца: ГСМ и генератор',
    description: 'Бензин для мотопомп и дизельный генератор для весенней экспедиции в глухие леса Болховского района.',
    target_amount: 50_000,
    collected_amount: 35_000,
    status: 'open',
    created_at: CREATED,
  },
  {
    id: 'demo-rubezh-gear',
    squad_id: 'demo-rubezh',
    kind: 'funds',
    title: 'Экипировать отряд: металлоискатели и щупы',
    description: 'Два металлоискателя и комплект щупов для новичков полевой школы.',
    target_amount: 120_000,
    collected_amount: 42_000,
    status: 'open',
    created_at: CREATED,
  },
  {
    id: 'demo-vysota-people',
    squad_id: 'demo-vysota',
    kind: 'volunteers',
    title: 'Нужны люди на раскопки',
    description: '10 человек на выходные: копать, просеивать грунт, вести полевой журнал.',
    target_amount: null,
    collected_amount: 0,
    status: 'open',
    created_at: CREATED,
  },
]

const trips: Trip[] = [
  {
    id: 'demo-krupyshino-recon',
    squad_id: 'demo-vysota',
    title: 'Разведка у села Крупышино: археология и топография',
    location: 'с. Крупышино, Орловский район',
    starts_on: inDays(5),
    capacity: 15,
    description: 'Полевая школа для новичков: как читать местность и вести полевой журнал.',
    checklist: 'Резиновые сапоги (высокие)\nПлотные рабочие перчатки\nТермос с чаем и сухой паёк\nЗаряженный телефон с приложением',
    created_at: CREATED,
  },
]

export const DEMO_HQ = { squads, needs, trips }
