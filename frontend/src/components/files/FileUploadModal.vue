<script setup lang="ts">
import { shallowRef, watch } from 'vue'
import { Upload, X } from '@lucide/vue'
import type { UploadFileInfo } from 'naive-ui'
import type { WorkspaceFolderOption } from '@/client/workspace'

const props = withDefaults(defineProps<{
  show?: boolean
  activeFolderId?: string | null
  folderOptions?: WorkspaceFolderOption[]
  uploading?: boolean
}>(), {
  show: false,
  activeFolderId: null,
  folderOptions: () => [],
  uploading: false,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  submit: [payload: { files: File[]; folderId: string; tags: string[] }]
}>()

const selectedFolder = shallowRef('')
const tags = shallowRef<string[]>([])
const fileList = shallowRef<UploadFileInfo[]>([])
const errorMessage = shallowRef('')

// Reset state when modal opens
watch(() => props.show, (visible) => {
  if (visible) {
    // Default to active folder, else first option
    if (props.folderOptions.length) {
      const activeOpt = props.activeFolderId
        ? props.folderOptions.find(o => o.value === props.activeFolderId)
        : undefined
      if (activeOpt) {
        selectedFolder.value = activeOpt.value
      } else if (!selectedFolder.value || !props.folderOptions.some(o => o.value === selectedFolder.value)) {
        const firstOption = props.folderOptions[0]
        if (firstOption) {
          selectedFolder.value = firstOption.value
        }
      }
    }
    fileList.value = []
    tags.value = []
    errorMessage.value = ''
  }
})

// Keep selected folder in sync with folderOptions changes
watch(() => props.folderOptions, (opts) => {
  if (opts.length && !opts.some(o => o.value === selectedFolder.value)) {
    const firstOption = opts[0]
    if (firstOption) {
      selectedFolder.value = firstOption.value
    }
  }
})

function handleSubmit() {
  const files = fileList.value
    .map((info) => info.file)
    .filter((f): f is File => f != null)
  if (!files.length) {
    errorMessage.value = '请选择要上传的文件'
    return
  }
  if (!selectedFolder.value) {
    errorMessage.value = '请选择目标文件夹'
    return
  }
  errorMessage.value = ''
  emit('submit', {
    files,
    folderId: selectedFolder.value,
    tags: tags.value,
  })
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

function handleClose() {
  emit('update:show', false)
}
</script>

<template>
  <NModal
    :show="show"
    preset="card"
    title="上传文件"
    :style="{ width: '480px' }"
    :mask-closable="!uploading"
    @update:show="(v: boolean) => !uploading && emit('update:show', v)"
  >
    <div class="grid gap-4">
      <!-- Drag-drop upload zone -->
      <NUpload
        :default-upload="false"
        :max="20"
        multiple
        :file-list="fileList"
        accept="*"
        directory-dnd
        @update:file-list="(list: UploadFileInfo[]) => (fileList = list)"
      >
        <div
          class="flex flex-col items-center justify-center gap-2 border-2 border-dashed border-line rounded-2 bg-muted px-4 py-10 text-center cursor-pointer transition-colors hover:border-primary"
        >
          <NIcon size="36" class="text-sub">
            <Upload />
          </NIcon>
          <p class="m-0 text-sub text-13px">
            点击或拖拽文件到此区域上传
          </p>
          <p v-if="fileList.length" class="m-0 text-ink text-13px font-600">
            已选择 {{ fileList.length }} 个文件
          </p>
          <p v-else class="m-0 text-sub text-12px opacity-60">
            未选择文件
          </p>
        </div>
      </NUpload>

      <!-- Selected file list -->
      <div v-if="fileList.length > 1" class="max-h-30 overflow-y-auto border border-line rounded-2 p-2">
        <div
          v-for="(info, idx) in fileList"
          :key="idx"
          class="flex items-center justify-between gap-2 px-2 py-1 text-13px text-ink rounded-1 hover:bg-hover"
        >
          <span class="truncate">{{ info.name }}</span>
          <span class="shrink-0 text-sub text-11px">{{ info.file ? formatFileSize(info.file.size) : '' }}</span>
        </div>
      </div>

      <!-- Target folder -->
      <div>
        <label class="mb-2 block text-13px text-ink font-600">目标文件夹</label>
        <NTreeSelect
          v-model:value="selectedFolder"
          :options="folderOptions"
          placeholder="选择目标文件夹"
          clearable
          filterable
          key-field="value"
          label-field="label"
        />
      </div>

      <!-- Tags -->
      <div>
        <label class="mb-2 block text-13px text-ink font-600">标签</label>
        <NDynamicTags v-model:value="tags" />
      </div>

      <!-- Error -->
      <NAlert v-if="errorMessage" type="warning" :bordered="false">
        {{ errorMessage }}
      </NAlert>
    </div>

    <template #footer>
      <NSpace justify="end">
        <NButton :disabled="uploading" @click="handleClose">
          <template #icon>
            <NIcon aria-hidden="true"><X /></NIcon>
          </template>
          取消
        </NButton>
        <NButton
          type="primary"
          :disabled="!fileList.length || !selectedFolder"
          :loading="uploading"
          @click="handleSubmit"
        >
          <template #icon>
            <NIcon aria-hidden="true"><Upload /></NIcon>
          </template>
          上传
        </NButton>
      </NSpace>
    </template>
  </NModal>
</template>
