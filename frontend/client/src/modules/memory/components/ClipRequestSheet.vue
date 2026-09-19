<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import ToggleSwitch from '@/ui/ToggleSwitch.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormSelect from '@/ui/form/FormSelect.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { DEFAULT_NARRATION, VOICES, requestClip, type Clip, type VoiceStyle } from '../data'

const emit = defineEmits<{ close: []; created: [clip: Clip] }>()

const soldierName = ref('')
const photoUrl = ref('')
const narration = ref(DEFAULT_NARRATION)
const voice = ref<VoiceStyle | ''>('era_male')
const isPublic = ref(false)
const consent = ref(false)
const saving = ref(false)
const error = ref<string | null>(null)

const voiceOptions = (Object.keys(VOICES) as VoiceStyle[]).map((value) => ({ value, title: VOICES[value] }))

/** Ссылка на фото: загрузки файлов в media_service пока нет, фото берётся по адресу. */
const photoValid = computed(() => /^https?:\/\/\S+$/i.test(photoUrl.value.trim()))
const valid = computed(() => photoValid.value && narration.value.trim().length > 0 && consent.value && voice.value !== '')

async function submit(): Promise<void> {
  if (!valid.value || saving.value || voice.value === '') return
  saving.value = true
  error.value = null
  try {
    const clip = await requestClip({
      soldier_name: soldierName.value.trim(),
      source_photo_url: photoUrl.value.trim(),
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
      <FormInput v-model="soldierName" label="Кто на фото" :maxlength="255" placeholder="Сержант Воронов Алексей Григорьевич" />
      <FormInput
        v-model="photoUrl"
        label="Ссылка на фотографию"
        type="url"
        inputmode="url"
        :maxlength="500"
        placeholder="https://…"
        hint="Из семейного архива, музея или «Памяти народа». Загрузку с телефона добавим следующим шагом."
        required
      />
      <img
        v-if="photoValid"
        :src="photoUrl.trim()"
        alt="Фото, которое оживим"
        class="h-40 w-32 self-center rounded-DEFAULT object-cover shadow-sm"
      />
      <FormTextarea
        v-model="narration"
        label="Что скажет герой"
        :rows="3"
        :maxlength="2000"
        hint="От первого лица. Можно добавить краткую историю подвига из архива или от родных."
      />
      <FormSelect v-model="voice" label="Голос" :options="voiceOptions" />

      <div class="flex items-center justify-between gap-space-sm rounded-DEFAULT bg-surface-container-low p-space-sm">
        <div class="min-w-0">
          <span class="block font-label-md text-label-md text-on-surface">Показать в общем мемориале</span>
          <span class="block font-body-sm text-body-sm text-on-surface-variant">Иначе видео увидит только семья</span>
        </div>
        <ToggleSwitch v-model="isPublic" label="Показать в общем мемориале" />
      </div>

      <!-- Этическая оговорка кейса: без согласия сервис заявку не примет. -->
      <label class="flex cursor-pointer items-start gap-space-sm rounded-DEFAULT bg-secondary-container/40 p-space-sm">
        <input v-model="consent" type="checkbox" class="mt-1 h-5 w-5 shrink-0 accent-secondary" required />
        <span class="font-body-sm text-body-sm text-on-secondary-container">
          Использую только в мемориальных целях, с уважением к памяти. Не для коммерции и не для изменения смысла
          сказанного.
        </span>
      </label>

      <InlineNotice icon="hourglass_top">
        Заявка встанет в очередь. Генерация видео подключается отдельным модулем — пока его нет, заявка будет ждать.
      </InlineNotice>

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>

      <button
        type="submit"
        class="flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 font-label-lg text-label-lg text-on-primary shadow-md active:scale-[0.99] disabled:opacity-60"
        :disabled="!valid || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'auto_awesome'" :size="20" :class="{ 'animate-spin': saving }" />
        Отправить на оживление
      </button>
    </form>
  </SheetDialog>
</template>
