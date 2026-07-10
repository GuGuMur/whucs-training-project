<script setup lang="ts">
import { computed, h, shallowRef, watch } from 'vue'
import { Search, RefreshCw, Upload, FileText, Image, Video, File } from '@lucide/vue'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NDataTable, NIcon, NTag } from 'naive-ui'

import type {
  WorkspaceFile, WorkspaceFileAnnotation, WorkspaceFileAnnotationCreateInput,
  WorkspaceFileAnnotationReplyInput, WorkspaceFileContent, WorkspaceFileContentUpdateInput,
  WorkspaceFileCopyInput, WorkspaceFileFilters,
  WorkspaceFileUpdateInput, WorkspaceFileUploadInput, WorkspaceFileVersion,
  WorkspaceFolder, WorkspaceFolderOption, WorkspacePermissionRule, WorkspacePermissionRuleCreateInput,
} from '@/client/workspace'
import CategorySidebar from '../files/CategorySidebar.vue'
import FileDrawer from '../files/FileDrawer.vue'
import FileDropdown from '../files/FileDropdown.vue'
import FileUploadModal from '../files/FileUploadModal.vue'
import StatusChip from '../files/StatusChip.vue'

const emptyFilters: WorkspaceFileFilters = { fileType: '', query: '', tag: '', updatedFrom: '', updatedTo: '' }

const props = withDefaults(defineProps<{
  activeFolderId?: string | null
  annotationSaving?: boolean
  copyingFileId?: string | null
  deletingAnnotationId?: string | null
  deletingFileId?: string | null
  deletingPermissionRuleId?: string | null
  fileAnnotationsById?: Record<string, WorkspaceFileAnnotation[]>
  fileContentById?: Record<string, WorkspaceFileContent>
  fileContentLoadingId?: string | null
  fileVersionsById?: Record<string, WorkspaceFileVersion[]>
  files: WorkspaceFile[]
  filters?: WorkspaceFileFilters
  folderOptions?: WorkspaceFolderOption[]
  folderTreeLoading?: boolean
  folders?: WorkspaceFolder[]
  listingFiles?: boolean
  permissionRules?: WorkspacePermissionRule[]
  permissionsLoading?: boolean
  permissionRuleSaving?: boolean
  reparsingFileId?: string | null
  restoringVersionId?: string | null
  savingFileContentId?: string | null
  updatingFileId?: string | null
  uploadingFile?: boolean
  versionFileId?: string | null
}>(), {
  activeFolderId: null, annotationSaving: false, copyingFileId: null, deletingAnnotationId: null,
  deletingFileId: null, deletingPermissionRuleId: null, fileAnnotationsById: () => ({}),
  fileContentById: () => ({}), fileContentLoadingId: null,
  fileVersionsById: () => ({}), filters: () => ({ fileType: '', query: '', tag: '', updatedFrom: '', updatedTo: '' }),
  folderOptions: () => [], folderTreeLoading: false,
  folders: () => [], listingFiles: false, permissionRules: () => [],
  permissionsLoading: false, permissionRuleSaving: false, reparsingFileId: null,
  restoringVersionId: null, savingFileContentId: null, updatingFileId: null,
  uploadingFile: false, versionFileId: null,
})

const emit = defineEmits<{
  'copy-file': [fileId: string, payload: WorkspaceFileCopyInput]
  'create-file-annotation': [fileId: string, payload: WorkspaceFileAnnotationCreateInput]
  'create-folder': [payload: any]
  'delete-file': [file: WorkspaceFile]
  'delete-file-annotation': [fileId: string, annotationId: string]
  'delete-permission-rule': [ruleId: string]
  'download-file': [file: WorkspaceFile]
  'create-permission-rule': [payload: WorkspacePermissionRuleCreateInput]
  'load-file-content': [fileId: string]
  'load-file-annotations': [fileId: string]
  'load-file-versions': [fileId: string]
  'reply-file-annotation': [annotationId: string, payload: WorkspaceFileAnnotationReplyInput]
  'reparse-file': [file: WorkspaceFile]
  'restore-file-version': [fileId: string, versionId: string]
  'search-files': [filters: WorkspaceFileFilters]
  'select-folder': [folderId: string]
  'update-file-content': [fileId: string, payload: WorkspaceFileContentUpdateInput]
  'update-file': [fileId: string, payload: WorkspaceFileUpdateInput]
  'upload-file': [payload: WorkspaceFileUploadInput]
}>()

// ── Filters ──
const queryText = shallowRef('')
const selectedFileType = shallowRef('')
const selectedTag = shallowRef('')
const updatedFromText = shallowRef('')
const updatedToText = shallowRef('')
const activeCategory = shallowRef('all')

watch(() => props.filters, (f) => {
  queryText.value = f.query; selectedFileType.value = f.fileType
  selectedTag.value = f.tag; updatedFromText.value = f.updatedFrom; updatedToText.value = f.updatedTo
}, { immediate: true })

// ── Drawer / Modal state ──
const drawerShow = shallowRef(false)
const drawerFile = shallowRef<WorkspaceFile | null>(null)
const drawerTab = shallowRef('rename')
const uploadModalShow = shallowRef(false)
const deleteConfirmShow = shallowRef(false)
const deleteTarget = shallowRef<WorkspaceFile | null>(null)

function openDrawer(file: WorkspaceFile, tab: string) {
  drawerFile.value = file; drawerTab.value = tab; drawerShow.value = true
  if (tab === 'preview') emit('load-file-content', file.id)
}

function handleUpload(payload: WorkspaceFileUploadInput) {
  emit('upload-file', payload); uploadModalShow.value = false
}

function confirmDelete() {
  if (deleteTarget.value) { emit('delete-file', deleteTarget.value); deleteConfirmShow.value = false; deleteTarget.value = null }
}

watch(() => props.files, (files) => {
  if (!drawerFile.value) return
  drawerFile.value = files.find((file) => file.id === drawerFile.value?.id) ?? drawerFile.value
})

// ── Tag / type options ──
const tagOptions = computed(() => {
  const tags = new Set(props.files.flatMap(f => f.tags))
  return [{ label: '全部标签', value: '' }, ...[...tags].sort().map(t => ({ label: t, value: t }))]
})
const fileTypeOptions = computed(() => {
  const types = new Set(props.files.map(f => f.type))
  return [{ label: '全部类型', value: '' }, ...[...types].sort().map(t => ({ label: t, value: t }))]
})

// ── Visible files ──
const categoryFiltered = computed(() => {
  switch (activeCategory.value) {
    case 'image': return props.files.filter(f => ['jpg','jpeg','png','gif','svg','webp','bmp'].includes(f.type))
    case 'document': return props.files.filter(f => ['pdf','docx','doc','pptx','ppt','xlsx','xls','md','txt'].includes(f.type))
    case 'video': return props.files.filter(f => ['mp4','avi','mov','mkv','webm'].includes(f.type))
    case 'other': return props.files.filter(f => !['jpg','jpeg','png','gif','svg','webp','bmp','pdf','docx','doc','pptx','ppt','xlsx','xls','md','txt','mp4','avi','mov','mkv','webm'].includes(f.type))
    default: return props.files
  }
})
const visibleFiles = computed(() => {
  if (!props.activeFolderId) return categoryFiltered.value
  const ids = new Set<string>()
  const f = props.folders.find(x => x.id === props.activeFolderId)
  if (!f) return categoryFiltered.value
  function collect(n: WorkspaceFolder) { ids.add(n.id); n.children?.forEach(collect) }
  collect(f); return categoryFiltered.value.filter(x => ids.has(x.folder_id))
})

// ── Helpers ──
function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}
function parseLabel(s: WorkspaceFile['parse_status']) {
  return { queued: '待解析', parsing: '解析中', indexed: '已入库', failed: '解析失败' }[s]
}
function parseTone(s: WorkspaceFile['parse_status']) {
  return { queued: 'muted' as const, parsing: 'warning' as const, indexed: 'success' as const, failed: 'danger' as const }[s]
}
function fileTypeIcon(t: string) {
  if (['jpg','jpeg','png','gif','svg','webp'].includes(t)) return Image
  if (['mp4','avi','mov','mkv'].includes(t)) return Video
  if (['pdf','docx','doc','md','txt','pptx','xlsx'].includes(t)) return FileText
  return File
}
function handleSearch() {
  emit('search-files', { query: queryText.value, fileType: selectedFileType.value, tag: selectedTag.value, updatedFrom: updatedFromText.value, updatedTo: updatedToText.value })
}
function handleReset() {
  queryText.value = ''; selectedFileType.value = ''; selectedTag.value = ''; updatedFromText.value = ''; updatedToText.value = ''
  emit('search-files', { ...emptyFilters })
}

// ── Drawer computed ──
const drawerAnnotations = computed(() => drawerFile.value ? props.fileAnnotationsById[drawerFile.value.id] ?? [] : [])
const drawerContent = computed(() => drawerFile.value ? props.fileContentById[drawerFile.value.id] ?? null : null)
const drawerPermissionRules = computed(() => {
  const file = drawerFile.value
  if (!file) return []
  return props.permissionRules.filter((rule) => {
    if (rule.resource_type === 'file') return rule.resource_id === file.id
    return rule.resource_type === 'folder' && rule.resource_id === file.folder_id && rule.inherit
  })
})
const drawerVersions = computed(() => drawerFile.value ? props.fileVersionsById[drawerFile.value.id] ?? [] : [])

// ── Table columns ──
const columns = computed<DataTableColumns<WorkspaceFile>>(() => [
  { type: 'selection', width: 44 },
  {
    title: '文件名', key: 'name', minWidth: 240,
    render: (row) => h('div', { class: 'flex items-center gap-2' }, [
      h(NIcon, { size: 18, color: '#94a3b8' }, () => h(fileTypeIcon(row.type))),
      h('div', { class: 'min-w-0' }, [
        h('p', { class: 'm-0 text-ink text-13px font-650 truncate' }, row.name),
        h('div', { class: 'flex flex-wrap gap-1 mt-0.5' }, row.tags.map(t => h(NTag, { size: 'tiny', round: true, bordered: false }, () => t))),
      ]),
    ]),
  },
  { title: '大小', key: 'size', width: 90, render: (row) => h('span', { class: 'text-sub text-12px' }, formatSize(row.size)) },
  { title: '类型', key: 'type', width: 80, render: (row) => h('span', { class: 'text-sub text-12px' }, row.type.toUpperCase()) },
  {
    title: '状态', key: 'parse_status', width: 90,
    render: (row) => h(StatusChip, { tone: parseTone(row.parse_status), label: parseLabel(row.parse_status) }),
  },
  {
    title: '时间', key: 'updated_at', width: 140,
    render: (row) => h('span', { class: 'text-sub text-12px' }, new Date(row.updated_at).toLocaleDateString('zh-CN')),
  },
  {
    title: '', key: 'actions', width: 48, align: 'right',
    render: (row) => h(FileDropdown, {
      file: row,
      annotationCount: 0,
      versionCount: props.fileVersionsById[row.id]?.length ?? 0,
      reparsing: props.reparsingFileId === row.id,
      onDownload: (f: WorkspaceFile) => emit('download-file', f),
      onPreview: (f: WorkspaceFile) => openDrawer(f, 'preview'),
      onRename: (f: WorkspaceFile) => openDrawer(f, 'rename'),
      onMove: (f: WorkspaceFile) => openDrawer(f, 'move'),
      onCopy: (f: WorkspaceFile) => openDrawer(f, 'copy'),
      onTags: (f: WorkspaceFile) => openDrawer(f, 'tags'),
      onAnnotate: (f: WorkspaceFile) => { emit('load-file-annotations', f.id); openDrawer(f, 'annotations') },
      onPermissions: (f: WorkspaceFile) => openDrawer(f, 'permissions'),
      onVersions: (f: WorkspaceFile) => { emit('load-file-versions', f.id); openDrawer(f, 'versions') },
      onDelete: (f: WorkspaceFile) => { deleteTarget.value = f; deleteConfirmShow.value = true },
      onReparse: (f: WorkspaceFile) => emit('reparse-file', f),
    }),
  },
])
</script>

<template>
  <NCard id="files" class="min-w-0 overflow-hidden" :bordered="true" size="small" content-class="!p-0">
    <template #header>
      <div class="flex items-center gap-3">
        <span class="text-sub text-13px">个人文件、团队文件、解析状态和权限范围</span>
      </div>
    </template>

    <div class="grid grid-cols-[220px_minmax(0,1fr)] max-lg:grid-cols-1">
      <CategorySidebar
        :active-category="activeCategory"
        :folder-tree-loading="folderTreeLoading"
        :folders="folders"
        @select-category="(k: string) => activeCategory = k"
        @select-folder="(id: string) => emit('select-folder', id)"
      />

      <div class="min-w-0 border-l border-line">
        <!-- Toolbar -->
        <div class="border-b border-line bg-muted px-4 py-2">
          <div class="flex items-center gap-2 overflow-x-auto">
            <NInput v-model:value="queryText" clearable placeholder="搜索…" class="flex-1 min-w-140px" size="small" @keyup.enter="handleSearch">
              <template #prefix><NIcon :size="14"><Search /></NIcon></template>
            </NInput>
            <NSelect v-model:value="selectedFileType" :options="fileTypeOptions" placeholder="类型" size="small" class="w-80px shrink-0" clearable />
            <NSelect v-model:value="selectedTag" :options="tagOptions" placeholder="标签" size="small" class="w-80px shrink-0" clearable />
            <NButton size="small" type="primary" class="shrink-0" :loading="listingFiles" @click="handleSearch">
              <template #icon><NIcon :size="14"><Search /></NIcon></template>
            </NButton>
            <NButton size="small" class="shrink-0" :disabled="listingFiles" @click="handleReset">
              <template #icon><NIcon :size="14"><RefreshCw /></NIcon></template>
            </NButton>
            <NButton size="small" type="warning" class="shrink-0" @click="uploadModalShow = true">
              <template #icon><NIcon :size="14"><Upload /></NIcon></template>
              上传
            </NButton>
          </div>
        </div>

        <!-- Desktop table -->
        <NDataTable
          class="max-md:hidden"
          :columns="columns" :data="visibleFiles" :pagination="false" :bordered="false"
          :scroll-x="720" size="small" :row-key="(row: WorkspaceFile) => row.id"
        />

        <!-- Mobile rows -->
        <NList class="hidden max-md:block" :show-divider="false">
          <NListItem v-for="file in visibleFiles" :key="file.id" class="!px-3 !py-2.5">
            <div class="grid gap-1.5 w-full">
              <div class="flex items-start justify-between gap-2">
                <strong class="min-w-0 break-words text-ink text-13px leading-[1.35]">{{ file.name }}</strong>
                <FileDropdown
                  :file="file" :annotation-count="0"
                  :version-count="fileVersionsById[file.id]?.length ?? 0"
                  :reparsing="reparsingFileId === file.id"
                  @download="(f: WorkspaceFile) => emit('download-file', f)"
                  @preview="(f: WorkspaceFile) => openDrawer(f, 'preview')"
                  @rename="(f: WorkspaceFile) => openDrawer(f, 'rename')"
                  @move="(f: WorkspaceFile) => openDrawer(f, 'move')"
                  @copy="(f: WorkspaceFile) => openDrawer(f, 'copy')"
                  @tags="(f: WorkspaceFile) => openDrawer(f, 'tags')"
                  @annotate="(f: WorkspaceFile) => { emit('load-file-annotations', f.id); openDrawer(f, 'annotations') }"
                  @permissions="(f: WorkspaceFile) => openDrawer(f, 'permissions')"
                  @versions="(f: WorkspaceFile) => { emit('load-file-versions', f.id); openDrawer(f, 'versions') }"
                  @delete="(f: WorkspaceFile) => { deleteTarget = f; deleteConfirmShow = true }"
                  @reparse="(f: WorkspaceFile) => emit('reparse-file', f)"
                />
              </div>
              <div class="flex flex-wrap gap-1.5 text-11px text-sub">
                <span>{{ formatSize(file.size) }}</span><span>·</span>
                <span>{{ file.type.toUpperCase() }}</span><span>·</span>
                <span>{{ new Date(file.updated_at).toLocaleDateString('zh-CN') }}</span>
              </div>
            </div>
          </NListItem>
        </NList>
      </div>
    </div>
  </NCard>

  <!-- Upload Modal -->
  <FileUploadModal
    :show="uploadModalShow" :folder-options="folderOptions" :uploading="uploadingFile"
    @update:show="(v: boolean) => uploadModalShow = v"
    @submit="handleUpload"
  />

  <!-- Drawer -->
  <FileDrawer
    :show="drawerShow" :file="drawerFile" :folder-options="folderOptions"
    :versions="drawerVersions" :annotations="drawerAnnotations" :permission-rules="drawerPermissionRules"
    :file-content="drawerContent"
    :initial-tab="drawerTab"
    :copying="copyingFileId === drawerFile?.id"
    :updating="updatingFileId === drawerFile?.id"
    :loading-content="fileContentLoadingId === drawerFile?.id"
    :loading-versions="versionFileId === drawerFile?.id"
    :restoring-version-id="restoringVersionId"
    :saving-content="savingFileContentId === drawerFile?.id"
    :saving-annotation="annotationSaving"
    :deleting-annotation-id="deletingAnnotationId"
    :permissions-loading="permissionsLoading"
    :permission-saving="permissionRuleSaving"
    :deleting-permission-rule-id="deletingPermissionRuleId"
    @update:show="(v: boolean) => drawerShow = v"
    @close="drawerShow = false"
    @update-file="(fid, p) => emit('update-file', fid, p)"
    @copy-file="(fid, p) => emit('copy-file', fid, p)"
    @create-permission-rule="(p) => emit('create-permission-rule', p)"
    @load-content="(fid) => emit('load-file-content', fid)"
    @load-versions="(fid) => emit('load-file-versions', fid)"
    @restore-version="(fid, vid) => emit('restore-file-version', fid, vid)"
    @load-annotations="(fid) => emit('load-file-annotations', fid)"
    @create-annotation="(fid, p) => emit('create-file-annotation', fid, p)"
    @reply-annotation="(aid, p) => emit('reply-file-annotation', aid, p)"
    @delete-annotation="(fid, aid) => emit('delete-file-annotation', fid, aid)"
    @delete-permission-rule="(rid) => emit('delete-permission-rule', rid)"
    @save-content="(fid, p) => emit('update-file-content', fid, p)"
  />

  <!-- Delete confirm -->
  <NModal v-model:show="deleteConfirmShow" preset="card" title="确认删除" style="width: 400px">
    <p class="m-0 text-ink">确定要删除 <strong>{{ deleteTarget?.name }}</strong> 吗？此操作不可撤销。</p>
    <template #footer>
      <NSpace justify="end">
        <NButton @click="deleteConfirmShow = false">取消</NButton>
        <NButton type="error" :loading="deletingFileId === deleteTarget?.id" @click="confirmDelete">确认删除</NButton>
      </NSpace>
    </template>
  </NModal>
</template>
