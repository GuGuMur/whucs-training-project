<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { Upload, X } from '@lucide/vue'

import type { WorkspaceFileUploadInput, WorkspaceFolderOption } from '@/client/workspace'

const props = withDefaults(defineProps<{
  defaultFolderId?: string | null
  folderOptions?: WorkspaceFolderOption[]
  uploading?: boolean
}>(), {
  defaultFolderId: null,
  folderOptions: () => [],
  uploading: false,
})

const emit = defineEmits<{
  cancel: []
  submit: [payload: WorkspaceFileUploadInput]
}>()

const fallbackFolderOptions: WorkspaceFolderOption[] = [
  { label: '个人文件', value: 'personal-root' },
  { label: '生物学实验', value: 'folder-biology' },
  { label: '软件工程课程', value: 'folder-course' },
  { label: '团队文件', value: 'team-root' },
]

const folderId = shallowRef('')
const selectedFile = shallowRef<File | null>(null)
const tagsText = shallowRef('')
const errorMessage = shallowRef('')

const effectiveFolderOptions = computed(() => (props.folderOptions.length ? props.folderOptions : fallbackFolderOptions))
const canSubmit = computed(() => Boolean(selectedFile.value && folderId.value))

watch(
  () => [props.defaultFolderId, effectiveFolderOptions.value.map((option) => option.value).join('|')] as const,
  () => {
    const values = new Set(effectiveFolderOptions.value.map((option) => option.value))
    if (props.defaultFolderId && values.has(props.defaultFolderId)) {
      folderId.value = props.defaultFolderId
      return
    }
    if (!values.has(folderId.value)) {
      folderId.value = effectiveFolderOptions.value[0]?.value ?? ''
    }
  },
  { immediate: true },
)

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
  errorMessage.value = ''
}

function handleSubmit() {
  if (!selectedFile.value) {
    errorMessage.value = '请选择要上传的文件'
    return
  }

  emit('submit', {
    file: selectedFile.value,
    folderId: folderId.value,
    tags: tagsText.value
      .split(',')
      .map((tag) => tag.trim())
      .filter(Boolean),
  })
}
</script>

<template>
  <div data-testid="file-upload-panel" class="border-b border-line bg-#F8FAFD px-4 py-3">
    <NForm :show-feedback="false" label-placement="left" label-width="76">
      <div class="grid grid-cols-[minmax(0,1.2fr)_minmax(160px,0.6fr)_minmax(180px,0.8fr)_auto] items-start gap-3 max-lg:grid-cols-1">
        <NFormItem label="文件">
          <input
            data-testid="upload-file-input"
            type="file"
            class="block min-h-34px w-full border border-line rounded-1.5 bg-surface px-3 py-1.5 text-13px text-ink file:mr-3 file:border-0 file:bg-primarySoft file:px-2 file:py-1 file:text-primary file:font-700"
            @change="handleFileChange"
          >
        </NFormItem>

        <NFormItem label="目录">
          <NSelect v-model:value="folderId" :options="effectiveFolderOptions" />
        </NFormItem>

        <NFormItem label="标签">
          <NInput v-model:value="tagsText" placeholder="实验, 观察" />
        </NFormItem>

        <NSpace class="justify-end" :wrap="false">
          <NButton :disabled="uploading" @click="emit('cancel')">
            <template #icon>
              <NIcon aria-hidden="true"><X /></NIcon>
            </template>
            取消
          </NButton>
          <NButton
            data-testid="submit-upload-file"
            type="primary"
            :disabled="!canSubmit"
            :loading="uploading"
            @click="handleSubmit"
          >
            <template #icon>
              <NIcon aria-hidden="true"><Upload /></NIcon>
            </template>
            上传
          </NButton>
        </NSpace>
      </div>
    </NForm>

    <NAlert v-if="errorMessage" class="mt-2" type="warning" :bordered="false">
      {{ errorMessage }}
    </NAlert>
  </div>
</template>
