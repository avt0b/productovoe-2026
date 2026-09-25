<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { DEFAULT_NARRATION, VOICES, requestClip, type Clip, type VoiceStyle } from '../data'
import PhotoPicker from './PhotoPicker.vue'

const emit = defineEmits<{ close: []; created: [clip: Clip] }>()

const VOICE_ICONS: Record<VoiceStyle, string> = { era_male: 'man', era_female: 'woman', neutral: 'record_voice_over' }

const soldierName = ref('')
const photoUrl = ref('')
const uploading = ref(false)
const narration = ref(DEFAULT_NARRATION)
const voice = ref<VoiceStyle>('era_male')
const isPublic = ref(false)
const consent = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const voices = Object.keys(VOICES) as VoiceStyle[]

const missing = computed(() => {
  if (uploading.value) return 'Дождитесь, пока фото загрузится'
  if (!photoUrl.value) return 'Выберите фото героя'
  if (!narration.value.trim()) return 'Напишите, что скажет герой'
  if (!consent.value) return 'Подтвердите, что видео — только для памяти'
  return null
})

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  try {
    const clip = await requestClip({
      soldier_name: soldierName.value.trim(),
      source_photo_url: photoUrl.value,
      narration_text: narration.value.trim(),
      voice_style: voice.value,
      is_public: isPublic.value,
      consent_memorial_use: consent.value,
    })
    emit('created', clip)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog title="Оживить фото героя" subtitle="Короткое видео: лицо в движении и голос, близкий к эпохе" @close="emit('close')">
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <PhotoPicker
        v-model="photoUrl"
        v-model:uploading="uploading"
        service="media"
        label="Фото бойца"
        hint="Из семейного альбома, музея или «Памяти народа». Лучше портрет анфас, где хорошо видно лицо."
      />
      <FormInput v-model="soldierName" label="Кто на фото" :maxlength="255" placeholder="Сержант Воронов Алексей Григорьевич" />
      <FormTextarea
        v-model="narration"
        label="Что скажет герой"
        :rows="3"
        :maxlength="2000"
        hint="От первого лица. Можно добавить короткую историю подвига из архива или от родных."
      />

      <fieldset class="flex flex-col gap-space-xs">
        <legend class="mb-space-xs font-label-md text-label-md text-on-surface">Голос</legend>
        <div class="grid grid-cols-3 gap-space-xs" role="radiogroup" aria-label="Голос">
          <button
            v-for="value in voices"
            :key="value"
            type="button"
            role="radio"
            :aria-checked="voice === value"
            class="flex flex-col items-center gap-1 rounded-2xl px-1 py-space-sm text-center font-label-sm text-label-sm transition-colors duration-200 active:scale-95"
            :class="voice === value ? 'bg-secondary-container text-on-secondary-container shadow-document' : 'bg-surface-container-low text-on-surface-variant'"
            @click="voice = value"
          >
            <MsIcon :name="VOICE_ICONS[value]" :size="20" :filled="voice === value" />
            {{ VOICES[value] }}
          </button>
        </div>
      </fieldset>

      <!-- Видео всегда ложится в семейный архив; мемориал — только по желанию семьи. -->
      <div class="flex items-center justify-between gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <div class="min-w-0">
          <span class="block font-label-md text-label-md text-on-surface">Показать в общем мемориале</span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">
            {{ isPublic ? 'Портрет увидят все — и семья, и гости Орловщины' : 'Видео останется в семейном архиве' }}
          </span>
        </div>
        <ToggleSwitch v-model="isPublic" label="Показать в общем мемориале" />
      </div>

      <!-- Этическая оговорка кейса: без согласия сервис заявку не примет. -->
      <label class="flex cursor-pointer items-start gap-space-sm rounded-2xl bg-surface-container-low p-space-sm">
        <input v-model="consent" type="checkbox" class="peer sr-only" />
        <span
          class="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition-colors duration-200 peer-focus-visible:ring-2 peer-focus-visible:ring-secondary"
          :class="consent ? 'bg-secondary text-on-secondary' : 'border border-outline-variant bg-surface-container-lowest text-transparent'"
          aria-hidden="true"
        >
          <MsIcon name="check" :size="15" />
        </span>
        <span class="font-body-sm text-body-sm text-on-surface">
          Использую только в мемориальных целях, с уважением к памяти. Не для коммерции и не для изменения смысла
          сказанного.
        </span>
      </label>

      <InlineNotice icon="hourglass_top">
        Заявка встанет в очередь на оживление — статус видно в семейном архиве, экран обновит его сам.
      </InlineNotice>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'auto_awesome'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>Отправить на оживление</span>
      </button>
    </form>
  </SheetDialog>
</template>
