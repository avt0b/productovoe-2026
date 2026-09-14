import { withLatency } from '@/core/mock'

/**
 * Данные окна «Память».
 *
 * Пока заглушка из макета: герой и его карточка вымышлены для демонстрации.
 * Когда подключим `media_service` и `archive_service`, поменяется только тело
 * `fetchPortrait` — живой портрет будет собираться из фотографии, которую
 * загрузила сама семья.
 */

export interface HeroPortrait {
  id: string
  name: string
  years: string
  unit: string
  homeland: string
  portraitImage: string
  /**
   * Реплика реконструированного голоса. Это не цитата героя — поэтому на экране
   * рядом всегда стоит пометка о реконструкции.
   */
  reconstructedLine: string
}

export interface MemoryOverview {
  hero: HeroPortrait
  archiveFolder: string
  mapHint: string
}

const OVERVIEW: MemoryOverview = {
  hero: {
    id: 'voronov-ag',
    name: 'Сержант Алексей Григорьевич Воронов',
    years: '1920 — 1942',
    unit: 'Командир стрелкового отделения, 137-я сд',
    homeland: 'Орловская губ., призван Елецким РВК',
    portraitImage:
      'https://lh3.googleusercontent.com/aida-public/AB6AXuD2xyruqLOLailgDwisn_NnihcRFmdBlieraiQdmaqn0ppj6dkFlzXw6_Y7Y9K2rD4LRgGr9jB_ECv19-YEihit12h2WdRqODXXZE1czSNUvLTgTBbkRRzZ1i5Fm-3Poe33DEoMquYIhjDRZDedEY8deprL23qFYSthoaRgnLYbHYwjFMbG8uoeyFs-J7TLDluluY3_MUsv1VLoerDvDCfV-HfFNmiLSv5YZ19HHgFUY_1Ye3yNWfFK',
    reconstructedLine: '«Я сделал это, чтобы ты жил и видел мирное небо. Помни меня.»',
  },
  archiveFolder: 'Папка «Герои семьи Вороновых»',
  mapHint: 'Координаты боевого пути 1941–1942',
}

export function fetchPortrait(): Promise<MemoryOverview> {
  return withLatency(OVERVIEW)
}
