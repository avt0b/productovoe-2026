<script setup lang="ts">
import { computed, ref } from 'vue'

import { errorText } from '@/core/format'
import InlineNotice from '@/ui/InlineNotice.vue'
import MsIcon from '@/ui/MsIcon.vue'
import SheetDialog from '@/ui/SheetDialog.vue'
import FormInput from '@/ui/form/FormInput.vue'
import FormTextarea from '@/ui/form/FormTextarea.vue'

import { createSquad, deleteSquad, updateSquad, type Squad } from '../data'

/**
 * Отряд: заводит его поисковик, ведёт — командир. Это же окно правит уже
 * заведённый отряд и распускает его: сборы и выезды уходят вместе с ним,
 * поэтому роспуск — в два нажатия.
 */
const props = withDefaults(defineProps<{ squad?: Squad | null }>(), { squad: null })

const emit = defineEmits<{ close: []; created: [squad: Squad]; removed: [squad: Squad] }>()

const name = ref(props.squad?.name ?? '')
const region = ref(props.squad?.region ?? '')
const description = ref(props.squad?.description ?? '')
const contact = ref(props.squad?.contact ?? '')
const saving = ref(false)
const confirmingDelete = ref(false)
const error = ref<string | null>(null)

const missing = computed(() => (name.value.trim() ? null : 'Как называется отряд?'))

async function submit(): Promise<void> {
  if (missing.value || saving.value) return
  saving.value = true
  error.value = null
  const draft = {
    name: name.value.trim(),
    region: region.value.trim(),
    description: description.value.trim(),
    contact: contact.value.trim(),
  }
  try {
    emit('created', props.squad ? await updateSquad(props.squad.id, draft) : await createSquad(draft))
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}

async function disband(): Promise<void> {
  const squad = props.squad
  if (!squad || saving.value) return
  saving.value = true
  error.value = null
  try {
    await deleteSquad(squad.id)
    emit('removed', squad)
  } catch (reason) {
    error.value = errorText(reason)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <SheetDialog
    :title="squad ? 'Отряд' : 'Новый поисковый отряд'"
    :subtitle="squad ? 'Правит командир — эти сведения видят волонтёры' : 'Вы станете его командиром'"
    @close="emit('close')"
  >
    <form class="flex flex-col gap-space-md" @submit.prevent="submit">
      <FormInput v-model="name" label="Название" :maxlength="200" placeholder="Поисковый отряд «Высота»" required />
      <FormInput v-model="region" label="Где работает" :maxlength="120" placeholder="Орёл" hint="Город штаба — по нему отряд встанет на карту потребностей" />
      <FormTextarea v-model="description" label="Чем занимается" placeholder="Какие рубежи, какие экспедиции" />
      <FormInput v-model="contact" label="Как связаться" :maxlength="300" placeholder="Телефон штаба или ссылка на чат" />

      <InlineNotice v-if="error" tone="error">{{ error }}</InlineNotice>
      <p v-else-if="missing" class="text-center font-body-sm text-body-sm text-on-surface-variant">{{ missing }}</p>

      <button
        type="submit"
        class="flex w-full items-center justify-center space-x-space-sm rounded-xl bg-primary-container py-3.5 font-label-lg text-label-lg uppercase tracking-wide text-white shadow-stamp transition-all hover:bg-primary active:scale-[0.99] disabled:opacity-70 short:py-2.5"
        :disabled="missing !== null || saving"
      >
        <MsIcon :name="saving ? 'progress_activity' : 'flag'" :size="18" :class="{ 'animate-spin': saving }" />
        <span>{{ squad ? 'Сохранить' : 'Создать отряд' }}</span>
      </button>

      <!-- Роспуск — в два нажатия: вместе с отрядом уходят его сборы и выезды. -->
      <template v-if="squad">
        <button
          type="button"
          class="self-center rounded-full px-space-md py-2 font-label-md text-label-md text-error active:scale-95"
          :aria-expanded="confirmingDelete"
          @click="confirmingDelete = !confirmingDelete"
        >
          Распустить отряд
        </button>
        <div
          class="grid transition-[grid-template-rows,opacity] duration-300 ease-out"
          :class="confirmingDelete ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'"
          :inert="!confirmingDelete"
        >
          <div class="overflow-hidden">
            <div class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-low p-space-md" role="alertdialog" aria-label="Подтверждение роспуска">
              <p class="font-body-sm text-body-sm text-on-surface">
                Распустить отряд вместе со сборами и выездами? Это не отменить.
              </p>
              <div class="flex gap-space-sm">
                <button
                  type="button"
                  class="flex-1 rounded-full bg-surface-container-high py-2.5 font-label-md text-label-md text-on-surface active:scale-95"
                  @click="confirmingDelete = false"
                >
                  Оставить
                </button>
                <button
                  type="button"
                  class="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-error py-2.5 font-label-md text-label-md text-on-error active:scale-95 disabled:opacity-60"
                  :disabled="saving"
                  @click="disband"
                >
                  <MsIcon name="delete" :size="18" />
                  Распустить
                </button>
              </div>
            </div>
          </div>
        </div>
      </template>
    </form>
  </SheetDialog>
</template>
