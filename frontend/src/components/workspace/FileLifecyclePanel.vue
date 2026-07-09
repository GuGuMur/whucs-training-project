<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { Copy, History, RotateCcw, Save, X } from '@lucide/vue'

import type {
  WorkspaceFile,
  WorkspaceFileCopyInput,
  WorkspaceFileUpdateInput,
  WorkspaceFileVersion,
  WorkspaceFolderOption,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  copying?: boolean
  file: WorkspaceFile | null
  folderOptions?: WorkspaceFolderOption[]
  loadingVersions?: boolean
  restoringVersionId?: string | null
  updating?: boolean
  versions?: WorkspaceFileVersion[]
}>(), {
  copying: false,
  folderOptions: () => [],
  loadingVersions: false,
  restoringVersionId: null,
  updating: false,
  versions: () => [],
})

const emit = defineEmits<{
  close: []
  'copy-file': [fileId: string, payload: WorkspaceFileCopyInput]
  'restore-file-version': [fileId: string, versionId: string]
  'update-file': [fileId: string, payload: WorkspaceFileUpdateInput]
}>()

const nameDraft = shallowRef('')
const folderIdDraft = shallowRef('')
const tagsDraft = shallowRef('')
const copyNameDraft = shallowRef('')
const errorMessage = shallowRef('')

const effectiveFolderOptions = computed(() => {
  const options = props.folderOptions.length ? props.folderOptions : []
  if (!props.file) {
    return options
  }

  if (options.some((option) => option.value === props.file?.folder_id)) {
    return options
  }

  return [
    ...options,
    {
      label: props.file.folder_id,
      value: props.file.folder_id,
    },
  ]
})

const sortedVersions = computed(() =>
  [...props.versions].sort((first, second) => second.version_no - first.version_no),
)

const canUpdate = computed(() => Boolean(props.file && nameDraft.value.trim() && folderIdDraft.value))
const canCopy = computed(() => Boolean(props.file && copyNameDraft.value.trim() && folderIdDraft.value))

watch(
  () => props.file?.id,
  () => {
    if (!props.file) {
      nameDraft.value = ''
      folderIdDraft.value = ''
      tagsDraft.value = ''
      copyNameDraft.value = ''
      errorMessage.value = ''
      return
    }

    nameDraft.value = props.file.name
    folderIdDraft.value = props.file.folder_id
    tagsDraft.value = props.file.tags.join(', ')
    copyNameDraft.value = buildCopyName(props.file.name)
    errorMessage.value = ''
  },
  { immediate: true },
)

function handleUpdate() {
  if (!props.file) {
    return
  }
  if (!canUpdate.value) {
    errorMessage.value = '请填写文件名并选择目录'
    return
  }

  emit('update-file', props.file.id, {
    folderId: folderIdDraft.value,
    name: nameDraft.value.trim(),
    tags: parseTags(tagsDraft.value),
  })
}

function handleCopy() {
  if (!props.file) {
    return
  }
  if (!canCopy.value) {
    errorMessage.value = '请填写副本文件名并选择目录'
    return
  }

  emit('copy-file', props.file.id, {
    name: copyNameDraft.value.trim(),
    targetFolderId: folderIdDraft.value,
  })
}

function handleRestore(versionId: string) {
  if (!props.file) {
    return
  }
  emit('restore-file-version', props.file.id, versionId)
}

function parseTags(value: string): string[] {
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

function buildCopyName(fileName: string) {
  const dotIndex = fileName.lastIndexOf('.')
  if (dotIndex <= 0) {
    return `${fileName} 副本`
  }
  return `${fileName.slice(0, dotIndex)} 副本${fileName.slice(dotIndex)}`
}

function formatBytes(size: number) {
  if (size < 1024) {
    return `${size} B`
  }
  if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`
  }
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <section v-if="file" data-testid="file-lifecycle-panel" class="border-t border-line bg-#F8FAFD px-4 py-4">
    <div class="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <NIcon class="text-primary" aria-hidden="true"><History /></NIcon>
          <h3 class="m-0 text-ink text-16px font-700">文件生命周期</h3>
        </div>
        <p class="m-0 mt-1 break-words text-13px text-sub leading-[1.55]">
          {{ file.name }} · {{ file.type }} · {{ formatBytes(file.size) }}
        </p>
      </div>
      <NButton quaternary size="small" @click="emit('close')">
        <template #icon>
          <NIcon aria-hidden="true"><X /></NIcon>
        </template>
        关闭
      </NButton>
    </div>

    <NAlert v-if="errorMessage" class="mt-3" type="warning" :bordered="false">
      {{ errorMessage }}
    </NAlert>

    <div class="mt-4 grid grid-cols-[minmax(0,1.15fr)_minmax(280px,0.85fr)] gap-4 max-lg:grid-cols-1">
      <div class="grid gap-4">
        <section class="border border-line rounded-2 bg-surface p-3">
          <div class="mb-3 flex items-center justify-between gap-2">
            <div>
              <h4 class="m-0 text-ink text-15px font-700">属性与目录</h4>
              <p class="m-0 mt-1 text-12px text-sub">重命名、移动目录和更新标签</p>
            </div>
          </div>
          <NForm :show-feedback="false" label-placement="top">
            <div class="grid grid-cols-[minmax(0,1fr)_minmax(190px,0.55fr)] gap-3 max-md:grid-cols-1">
              <NFormItem label="文件名">
                <NInput v-model:value="nameDraft" placeholder="文件名" />
              </NFormItem>
              <NFormItem label="目录">
                <NSelect v-model:value="folderIdDraft" :options="effectiveFolderOptions" />
              </NFormItem>
            </div>
            <NFormItem label="标签">
              <NInput v-model:value="tagsDraft" placeholder="标签，用逗号分隔" />
            </NFormItem>
            <div class="flex justify-end">
              <NButton
                data-testid="submit-update-file"
                type="primary"
                :disabled="!canUpdate"
                :loading="updating"
                @click="handleUpdate"
              >
                <template #icon>
                  <NIcon aria-hidden="true"><Save /></NIcon>
                </template>
                保存属性
              </NButton>
            </div>
          </NForm>
        </section>

        <section class="border border-line rounded-2 bg-surface p-3">
          <div class="mb-3">
            <h4 class="m-0 text-ink text-15px font-700">复制文件</h4>
            <p class="m-0 mt-1 text-12px text-sub">副本默认写入当前选择目录</p>
          </div>
          <div class="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 max-md:grid-cols-1">
            <NInput v-model:value="copyNameDraft" placeholder="副本文件名" />
            <NButton
              data-testid="submit-copy-file"
              type="primary"
              :disabled="!canCopy"
              :loading="copying"
              @click="handleCopy"
            >
              <template #icon>
                <NIcon aria-hidden="true"><Copy /></NIcon>
              </template>
              创建副本
            </NButton>
          </div>
        </section>
      </div>

      <section class="min-w-0 border border-line rounded-2 bg-surface p-3">
        <div class="mb-3 flex items-center justify-between gap-2">
          <div>
            <h4 class="m-0 text-ink text-15px font-700">版本记录</h4>
            <p class="m-0 mt-1 text-12px text-sub">同名上传会形成可回滚版本</p>
          </div>
          <NSpin v-if="loadingVersions" size="small" />
        </div>

        <NEmpty v-if="!sortedVersions.length && !loadingVersions" size="small" description="暂无版本记录" />
        <NList v-else :show-divider="false">
          <NListItem v-for="version in sortedVersions" :key="version.id" class="!px-0 !py-2">
            <div class="grid gap-2 border border-line rounded-1.5 bg-#FBFCFE p-2">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <strong class="text-ink text-13px">V{{ version.version_no }} · {{ version.name }}</strong>
                  <p class="m-0 mt-1 text-12px text-sub">
                    {{ formatTime(version.created_at) }} · {{ formatBytes(version.size) }} · {{ version.created_by }}
                  </p>
                </div>
                <NTag v-if="version.is_current" size="small" round :bordered="false" type="success">
                  当前
                </NTag>
              </div>
              <div class="flex items-center justify-between gap-2">
                <code class="min-w-0 truncate rounded-full bg-muted px-2 py-0.5 text-11px text-sub">
                  {{ version.sha256 }}
                </code>
                <NButton
                  v-if="!version.is_current"
                  :data-testid="`restore-version-${version.id}`"
                  size="tiny"
                  secondary
                  :loading="restoringVersionId === version.id"
                  @click="handleRestore(version.id)"
                >
                  <template #icon>
                    <NIcon aria-hidden="true"><RotateCcw /></NIcon>
                  </template>
                  回滚
                </NButton>
              </div>
            </div>
          </NListItem>
        </NList>
      </section>
    </div>
  </section>
</template>
