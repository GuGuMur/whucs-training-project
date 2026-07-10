<script setup lang="ts">
import { computed, h, shallowRef, watch } from 'vue'
import { Download, MessageSquareText, PenLine, RefreshCw, Search, Trash2, Upload } from '@lucide/vue'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NDataTable, NIcon, NTag } from 'naive-ui'

import type {
  WorkspaceFile,
  WorkspaceFileAnnotation,
  WorkspaceFileAnnotationCreateInput,
  WorkspaceFileAnnotationReplyInput,
  WorkspaceFileCopyInput,
  WorkspaceFileFilters,
  WorkspaceFileUpdateInput,
  WorkspaceFileUploadInput,
  WorkspaceFileVersion,
  WorkspaceFolder,
  WorkspaceFolderCreateInput,
  WorkspaceFolderOption,
  WorkspaceFolderUpdateInput,
  WorkspacePermissionRule,
  WorkspacePermissionRuleCreateInput,
  WorkspaceTeamDetail,
} from '@/client/workspace'
import FileAnnotationPanel from './FileAnnotationPanel.vue'
import FileLifecyclePanel from './FileLifecyclePanel.vue'
import FileUploadPanel from './FileUploadPanel.vue'
import FolderTreePanel from './FolderTreePanel.vue'
import PermissionRulesPanel from './PermissionRulesPanel.vue'
import StatusChip from './StatusChip.vue'

const emptyFilters: WorkspaceFileFilters = {
  fileType: '',
  query: '',
  tag: '',
  updatedFrom: '',
  updatedTo: '',
}

const props = withDefaults(defineProps<{
  activeFolderId?: string | null
  activeTeamDetail?: WorkspaceTeamDetail | null
  annotationFileIdLoading?: string | null
  annotationSaving?: boolean
  creatingFolder?: boolean
  deletingAnnotationId?: string | null
  deletingFileId?: string | null
  deletingFolderId?: string | null
  deletingPermissionRuleId?: string | null
  downloadingFileId?: string | null
  filters?: WorkspaceFileFilters
  copyingFileId?: string | null
  files: WorkspaceFile[]
  fileAnnotationsById?: Record<string, WorkspaceFileAnnotation[]>
  fileVersionsById?: Record<string, WorkspaceFileVersion[]>
  folderOptions?: WorkspaceFolderOption[]
  folderTreeLoading?: boolean
  folders?: WorkspaceFolder[]
  listingFiles?: boolean
  permissionRules?: WorkspacePermissionRule[]
  permissionRulesLoading?: boolean
  permissionRuleSaving?: boolean
  restoringVersionId?: string | null
  updatingFileId?: string | null
  updatingFolderId?: string | null
  uploadingFile?: boolean
  versionFileId?: string | null
}>(), {
  activeFolderId: null,
  activeTeamDetail: null,
  annotationFileIdLoading: null,
  annotationSaving: false,
  copyingFileId: null,
  creatingFolder: false,
  deletingAnnotationId: null,
  deletingFileId: null,
  deletingFolderId: null,
  deletingPermissionRuleId: null,
  downloadingFileId: null,
  filters: () => ({
    fileType: '',
    query: '',
    tag: '',
    updatedFrom: '',
    updatedTo: '',
  }),
  fileAnnotationsById: () => ({}),
  fileVersionsById: () => ({}),
  folderOptions: () => [],
  folderTreeLoading: false,
  folders: () => [],
  listingFiles: false,
  permissionRuleSaving: false,
  permissionRules: () => [],
  permissionRulesLoading: false,
  restoringVersionId: null,
  updatingFileId: null,
  updatingFolderId: null,
  uploadingFile: false,
  versionFileId: null,
})

const emit = defineEmits<{
  'copy-file': [fileId: string, payload: WorkspaceFileCopyInput]
  'create-file-annotation': [fileId: string, payload: WorkspaceFileAnnotationCreateInput]
  'create-permission-rule': [payload: WorkspacePermissionRuleCreateInput]
  'create-folder': [payload: WorkspaceFolderCreateInput]
  'delete-file': [file: WorkspaceFile]
  'delete-file-annotation': [fileId: string, annotationId: string]
  'delete-folder': [folderId: string]
  'delete-permission-rule': [ruleId: string]
  'download-file': [file: WorkspaceFile]
  'load-file-annotations': [fileId: string]
  'load-file-versions': [fileId: string]
  'reply-file-annotation': [annotationId: string, payload: WorkspaceFileAnnotationReplyInput]
  'restore-file-version': [fileId: string, versionId: string]
  'search-files': [filters: WorkspaceFileFilters]
  'select-folder': [folderId: string]
  'update-file': [fileId: string, payload: WorkspaceFileUpdateInput]
  'update-folder': [folderId: string, payload: WorkspaceFolderUpdateInput]
  'upload-file': [payload: WorkspaceFileUploadInput]
}>()

const queryText = shallowRef('')
const selectedFileType = shallowRef('')
const selectedTag = shallowRef('')
const updatedFromText = shallowRef('')
const updatedToText = shallowRef('')
const uploadPanelOpen = shallowRef(false)
const annotationFileId = shallowRef<string | null>(null)
const lifecycleFileId = shallowRef<string | null>(null)

watch(
  () => props.filters,
  (filters) => {
    queryText.value = filters.query
    selectedFileType.value = filters.fileType
    selectedTag.value = filters.tag
    updatedFromText.value = filters.updatedFrom
    updatedToText.value = filters.updatedTo
  },
  { immediate: true },
)

const tagOptions = computed(() => {
  const tags = new Set(props.files.flatMap((file) => file.tags))
  if (selectedTag.value) {
    tags.add(selectedTag.value)
  }
  return [
    { label: '全部标签', value: '' },
    ...[...tags].sort((first, second) => first.localeCompare(second, 'zh-Hans-CN')).map((tag) => ({
      label: tag,
      value: tag,
    })),
  ]
})

const fileTypeOptions = computed(() => {
  const fileTypes = new Set(props.files.map((file) => file.type))
  if (selectedFileType.value) {
    fileTypes.add(selectedFileType.value)
  }
  return [
    { label: '全部类型', value: '' },
    ...[...fileTypes].sort().map((fileType) => ({
      label: fileType,
      value: fileType,
    })),
  ]
})

const activeFolderIds = computed(() => {
  if (!props.activeFolderId) {
    return null
  }
  const activeFolder = findFolderById(props.folders, props.activeFolderId)
  if (!activeFolder) {
    return null
  }
  return collectFolderIds(activeFolder)
})
const visibleFiles = computed(() => {
  if (!activeFolderIds.value) {
    return props.files
  }
  return props.files.filter((file) => activeFolderIds.value?.has(file.folder_id))
})
const lifecycleFile = computed(() => {
  if (!lifecycleFileId.value) {
    return null
  }
  return props.files.find((file) => file.id === lifecycleFileId.value) ?? null
})
const lifecycleVersions = computed(() => {
  if (!lifecycleFile.value) {
    return []
  }
  return props.fileVersionsById[lifecycleFile.value.id] ?? []
})
const annotationFile = computed(() => {
  if (!annotationFileId.value) {
    return null
  }
  return props.files.find((file) => file.id === annotationFileId.value) ?? null
})
const annotationItems = computed(() => {
  if (!annotationFile.value) {
    return []
  }
  return props.fileAnnotationsById[annotationFile.value.id] ?? []
})

function parseLabel(status: WorkspaceFile['parse_status']) {
  return {
    queued: '待解析',
    parsing: '解析中',
    indexed: '已入库',
    failed: '解析失败',
  }[status]
}

function parseTone(status: WorkspaceFile['parse_status']) {
  return {
    queued: 'muted',
    parsing: 'warning',
    indexed: 'success',
    failed: 'danger',
  }[status] as 'success' | 'warning' | 'danger' | 'muted'
}

function renderActionButtons(row: WorkspaceFile) {
  return h('div', { class: 'flex items-center justify-end gap-1' }, [
    h(
      NButton,
      {
        'data-testid': `manage-file-${row.id}`,
        disabled: props.deletingFileId === row.id,
        quaternary: true,
        size: 'tiny',
        onClick: () => handleOpenLifecyclePanel(row),
      },
      {
        default: () => '管理',
        icon: () => h(NIcon, { 'aria-hidden': 'true' }, { default: () => h(PenLine) }),
      },
    ),
    h(
      NButton,
      {
        'data-testid': `download-file-${row.id}`,
        disabled: props.deletingFileId === row.id,
        loading: props.downloadingFileId === row.id,
        quaternary: true,
        size: 'tiny',
        onClick: () => emit('download-file', row),
      },
      {
        default: () => '下载',
        icon: () => h(NIcon, { 'aria-hidden': 'true' }, { default: () => h(Download) }),
      },
    ),
    h(
      NButton,
      {
        'data-testid': `annotate-file-${row.id}`,
        disabled: props.deletingFileId === row.id,
        quaternary: true,
        size: 'tiny',
        onClick: () => handleOpenAnnotationPanel(row),
      },
      {
        default: () => '批注',
        icon: () => h(NIcon, { 'aria-hidden': 'true' }, { default: () => h(MessageSquareText) }),
      },
    ),
    h(
      NButton,
      {
        'data-testid': `delete-file-${row.id}`,
        disabled: props.downloadingFileId === row.id,
        loading: props.deletingFileId === row.id,
        quaternary: true,
        size: 'tiny',
        type: 'error',
        onClick: () => emit('delete-file', row),
      },
      {
        default: () => '删除',
        icon: () => h(NIcon, { 'aria-hidden': 'true' }, { default: () => h(Trash2) }),
      },
    ),
  ])
}

function handleOpenLifecyclePanel(file: WorkspaceFile) {
  lifecycleFileId.value = file.id
  emit('load-file-versions', file.id)
}

function handleOpenAnnotationPanel(file: WorkspaceFile) {
  annotationFileId.value = file.id
  emit('load-file-annotations', file.id)
}

function handleSearch() {
  emit('search-files', {
    fileType: selectedFileType.value,
    query: queryText.value.trim(),
    tag: selectedTag.value,
    updatedFrom: updatedFromText.value.trim(),
    updatedTo: updatedToText.value.trim(),
  })
}

function handleResetFilters() {
  queryText.value = ''
  selectedFileType.value = ''
  selectedTag.value = ''
  updatedFromText.value = ''
  updatedToText.value = ''
  emit('search-files', { ...emptyFilters })
}

function handleUploadSubmit(payload: WorkspaceFileUploadInput) {
  emit('upload-file', payload)
  uploadPanelOpen.value = false
}

function findFolderById(folders: WorkspaceFolder[], folderId: string): WorkspaceFolder | null {
  for (const folder of folders) {
    if (folder.id === folderId) {
      return folder
    }
    const child = findFolderById(folder.children ?? [], folderId)
    if (child) {
      return child
    }
  }
  return null
}

function collectFolderIds(folder: WorkspaceFolder): Set<string> {
  const ids = new Set<string>([folder.id])
  for (const child of folder.children ?? []) {
    for (const childId of collectFolderIds(child)) {
      ids.add(childId)
    }
  }
  return ids
}

const columns = computed<DataTableColumns<WorkspaceFile>>(() => [
  {
    title: '文件名',
    key: 'name',
    minWidth: 220,
    render: (row) => h('strong', { class: 'text-ink text-13px' }, row.name),
  },
  { title: '类型', key: 'type', width: 88 },
  {
    title: '解析',
    key: 'parse_status',
    width: 104,
    render: (row) => h(StatusChip, { tone: parseTone(row.parse_status), label: parseLabel(row.parse_status) }),
  },
  {
    title: '标签',
    key: 'tags',
    minWidth: 150,
    render: (row) =>
      h(
        'div',
        { class: 'flex flex-wrap gap-1.5' },
        row.tags.map((tag) => h(NTag, { size: 'small', round: true, bordered: false }, { default: () => tag })),
      ),
  },
  { title: '权限', key: 'permission_scope', width: 88 },
  {
    title: '操作',
    key: 'actions',
    width: 204,
    align: 'right',
    render: renderActionButtons,
  },
])
</script>

<template>
  <NCard id="files" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" :bordered="true" size="small" content-class="!p-0">
    <template #header>
      <div class="flex items-start justify-between gap-4 max-md:flex-col">
        <div>
          <h2 class="m-0 text-ink text-18px font-700">文件管理</h2>
          <p class="mt-1 panel-subtitle">个人文件、团队文件、解析状态和权限范围</p>
        </div>
        <NSpace>
          <NButton data-testid="open-upload-panel" type="primary" @click="uploadPanelOpen = !uploadPanelOpen">
            <template #icon>
              <NIcon aria-hidden="true"><Upload /></NIcon>
            </template>
            上传文件
          </NButton>
        </NSpace>
      </div>
    </template>

    <div class="grid grid-cols-[260px_minmax(0,1fr)] max-lg:grid-cols-1">
      <FolderTreePanel
        :active-folder-id="activeFolderId"
        :creating-folder="creatingFolder"
        :deleting-folder-id="deletingFolderId"
        :folder-tree-loading="folderTreeLoading"
        :folders="folders"
        :updating-folder-id="updatingFolderId"
        @create-folder="emit('create-folder', $event)"
        @delete-folder="emit('delete-folder', $event)"
        @select-folder="emit('select-folder', $event)"
        @update-folder="(folderId, payload) => emit('update-folder', folderId, payload)"
      />

      <div class="min-w-0">
        <div class="border-b border-line bg-muted px-4 py-3">
          <div class="flex flex-wrap items-center gap-2">
            <NInput v-model:value="queryText" clearable placeholder="搜索文件名…" class="flex-1 min-w-200px" @keyup.enter="handleSearch">
              <template #prefix>
                <NIcon aria-hidden="true"><Search /></NIcon>
              </template>
            </NInput>
            <NSelect v-model:value="selectedFileType" :options="fileTypeOptions" placeholder="文件类型" class="w-130px" clearable />
            <NSelect v-model:value="selectedTag" :options="tagOptions" placeholder="标签" class="w-120px" clearable />
            <NInput v-model:value="updatedFromText" clearable placeholder="更新起" class="w-130px" @keyup.enter="handleSearch" />
            <NInput v-model:value="updatedToText" clearable placeholder="更新止" class="w-130px" @keyup.enter="handleSearch" />
            <NButton data-testid="search-files" type="primary" size="small" :loading="listingFiles" @click="handleSearch">
              <template #icon><NIcon aria-hidden="true"><Search /></NIcon></template>
              检索
            </NButton>
            <NButton size="small" :disabled="listingFiles" @click="handleResetFilters">
              <template #icon><NIcon aria-hidden="true"><RefreshCw /></NIcon></template>
              重置
            </NButton>
          </div>
        </div>

        <FileUploadPanel
          v-if="uploadPanelOpen"
          :default-folder-id="activeFolderId"
          :folder-options="folderOptions"
          :uploading="uploadingFile"
          @cancel="uploadPanelOpen = false"
          @submit="handleUploadSubmit"
        />

        <FileLifecyclePanel
          v-if="lifecycleFile"
          :copying="copyingFileId === lifecycleFile.id"
          :file="lifecycleFile"
          :folder-options="folderOptions"
          :loading-versions="versionFileId === lifecycleFile.id"
          :restoring-version-id="restoringVersionId"
          :updating="updatingFileId === lifecycleFile.id"
          :versions="lifecycleVersions"
          @close="lifecycleFileId = null"
          @copy-file="(fileId, payload) => emit('copy-file', fileId, payload)"
          @restore-file-version="(fileId, versionId) => emit('restore-file-version', fileId, versionId)"
          @update-file="(fileId, payload) => emit('update-file', fileId, payload)"
        />

        <FileAnnotationPanel
          v-if="annotationFile"
          :annotations="annotationItems"
          :deleting-annotation-id="deletingAnnotationId"
          :file="annotationFile"
          :loading="annotationFileIdLoading === annotationFile.id"
          :saving="annotationSaving"
          @close="annotationFileId = null"
          @create-annotation="(fileId, payload) => emit('create-file-annotation', fileId, payload)"
          @delete-annotation="(fileId, annotationId) => emit('delete-file-annotation', fileId, annotationId)"
          @load-annotations="(fileId) => emit('load-file-annotations', fileId)"
          @reply-annotation="(annotationId, payload) => emit('reply-file-annotation', annotationId, payload)"
        />

        <NDataTable
          class="max-md:hidden"
          :columns="columns"
          :data="visibleFiles"
          :pagination="false"
          :bordered="false"
          :scroll-x="650"
          size="small"
          :row-key="(row) => row.id"
        />

        <NList class="hidden max-md:block" :show-divider="false">
          <NListItem v-for="file in visibleFiles" :key="file.id" class="!px-4 !py-3">
            <div class="grid gap-2">
              <div class="flex items-start justify-between gap-3">
                <strong class="min-w-0 break-words text-ink text-14px leading-[1.35]">{{ file.name }}</strong>
                <StatusChip :tone="parseTone(file.parse_status)" :label="parseLabel(file.parse_status)" />
              </div>
              <div class="flex flex-wrap gap-1.5">
                <span class="mono-chip">{{ file.type }}</span>
                <span class="mono-chip">权限：{{ file.permission_scope }}</span>
              </div>
              <div class="flex flex-wrap gap-1.5">
                <NTag v-for="tag in file.tags" :key="tag" size="small" round :bordered="false">
                  {{ tag }}
                </NTag>
              </div>
              <div class="flex justify-end gap-2">
                <NButton
                  size="tiny"
                  secondary
                  :disabled="deletingFileId === file.id"
                  :data-testid="`manage-file-${file.id}`"
                  @click="handleOpenLifecyclePanel(file)"
                >
                  <template #icon>
                    <NIcon aria-hidden="true"><PenLine /></NIcon>
                  </template>
                  管理
                </NButton>
                <NButton
                  size="tiny"
                  secondary
                  :loading="downloadingFileId === file.id"
                  :disabled="deletingFileId === file.id"
                  :data-testid="`download-file-${file.id}`"
                  @click="emit('download-file', file)"
                >
                  <template #icon>
                    <NIcon aria-hidden="true"><Download /></NIcon>
                  </template>
                  下载
                </NButton>
                <NButton
                  size="tiny"
                  secondary
                  :disabled="deletingFileId === file.id"
                  :data-testid="`annotate-file-${file.id}`"
                  @click="handleOpenAnnotationPanel(file)"
                >
                  <template #icon>
                    <NIcon aria-hidden="true"><MessageSquareText /></NIcon>
                  </template>
                  批注
                </NButton>
                <NButton
                  size="tiny"
                  type="error"
                  secondary
                  :loading="deletingFileId === file.id"
                  :disabled="downloadingFileId === file.id"
                  :data-testid="`delete-file-${file.id}`"
                  @click="emit('delete-file', file)"
                >
                  <template #icon>
                    <NIcon aria-hidden="true"><Trash2 /></NIcon>
                  </template>
                  删除
                </NButton>
              </div>
            </div>
          </NListItem>
        </NList>

        <PermissionRulesPanel
          :active-folder-id="activeFolderId"
          :active-team-detail="activeTeamDetail"
          :deleting-rule-id="deletingPermissionRuleId"
          :files="files"
          :folders="folders"
          :loading="permissionRulesLoading"
          :rules="permissionRules"
          :saving="permissionRuleSaving"
          @create-rule="emit('create-permission-rule', $event)"
          @delete-rule="emit('delete-permission-rule', $event)"
        />
      </div>
    </div>
  </NCard>
</template>
