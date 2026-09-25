import { defineModule } from '@/core/module'

/**
 * «Место у метки»: куда ведёт NFC-чип на табличке у памятника или братской
 * могилы (`marshruty://place/<id точки слоя «ВОВ»>`, экран `/nfc` умеет
 * записать такую ссылку). Детский режим — пазл из фотографии места, обычный —
 * факты и видео, если для точки они есть.
 *
 * Своей вкладки нет — экран открывают только по ссылке с метки.
 */
export default defineModule({
  id: 'place',
  routes: [
    {
      path: '/place/:poiId',
      name: 'place',
      component: () => import('./PlacePage.vue'),
      props: true,
      meta: { title: 'Место у метки', layout: 'detail', public: true },
    },
  ],
})
