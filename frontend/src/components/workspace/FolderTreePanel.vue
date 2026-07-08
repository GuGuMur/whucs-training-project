<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { ChevronRight, Edit3, Folder, FolderOpen, FolderPlus, MoveRight, Trash2 } from '@lucide/vue'

import type {
  WorkspaceFolder,
  WorkspaceFolderCreateInput,
  WorkspaceFolderOption,
  WorkspaceFolderUpdateInput,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  activeFolderId?: string | null
  creatingFolder?: boolean
  deletingFolderId?: string | null
  folderTreeLoading?: boolean
  folders: WorkspaceFolder[]
  updatingFolderId?: string | null
}>(), {
  activeFolderId: null,
  creatingFolder: false,
  deletingFolderId: null,
  folderTreeLoading: false,
  updatingFolderId: null,
})

const emit = defineEmits<{
  'create-folder': [payload: WorkspaceFolderCreateInput]
  'delete-folder': [folderId: string]
  'select-folder': [folderId: string]
  'update-folder': [folderId: string, payload: WorkspaceFolderUpdateInput]
}>()

const createPanelOpen = shallowRef(false)
const createName = shallowRef('')
const createParentId = shallowRef<string | null>(null)
const createError = shallowRef('')
const editName = shallowRef('')
const editParentId = shallowRef<string | null>(null)
const editError = shallowRef('')

const folderRows = computed(() => flattenFolderRows(props.folders))
const activeFolder = computed(() => findFolderById(props.folders, props.activeFolderId))
const activeBreadcrumbs = computed(() => buildFolderBreadcrumbs(props.folders, props.activeFolderId))
const parentOptions = computed(() => flattenFolderOptions(props.folders))
const activeFolderIsRoot = computed(() => Boolean(activeFolder.value && !activeFolder.value.parent_id))
const createParentFolder = computed(() => findFolderById(props.folders, createParentId.value))
const createScopeLabel = computed(() => (createParentFolder.value?.scope === 'team' ? '团队目录' : '个人目录'))
const moveTargetOptions = computed(() => {
  if (!activeFolder.value) {
    return []
  }
  return flattenFolderOptions(props.folders, activeFolder.value)
})
const updateDisabled = computed(() => {
  const folder = activeFolder.value
  return !folder || activeFolderIsRoot.value || !editName.value.trim()
})

watch(
  activeFolder,
  (folder) => {
    editName.value = folder?.name ?? ''
    editParentId.value = folder?.parent_id ?? null
    editError.value = ''
  },
  { immediate: true },
)

watch(
  () => props.activeFolderId,
  (folderId) => {
    createParentId.value = folderId ?? findFirstFolderId(props.folders)
  },
  { immediate: true },
)

function openCreatePanel() {
  createPanelOpen.value = true
  createParentId.value = props.activeFolderId ?? findFirstFolderId(props.folders)
  createName.value = ''
  createError.value = ''
}

function handleCreateFolder() {
  const name = createName.value.trim()
  const parent = findFolderById(props.folders, createParentId.value)
  if (!name) {
    createError.value = '请输入文件夹名称'
    return
  }
  if (!parent) {
    createError.value = '请选择父级目录'
    return
  }

  emit('create-folder', {
    name,
    parentId: parent.id,
    scope: parent.scope,
  })
  createName.value = ''
  createError.value = ''
}

function handleUpdateFolder() {
  const folder = activeFolder.value
  const name = editName.value.trim()
  if (!folder || activeFolderIsRoot.value) {
    return
  }
  if (!name) {
    editError.value = '目录名称不能为空'
    return
  }

  emit('update-folder', folder.id, {
    name,
    parentId: editParentId.value ?? folder.parent_id,
  })
  editError.value = ''
}

function handleDeleteFolder() {
  const folder = activeFolder.value
  if (!folder || activeFolderIsRoot.value) {
    return
  }
  emit('delete-folder', folder.id)
}

function isFolderActive(folderId: string) {
  return props.activeFolderId === folderId
}

interface FolderRow {
  depth: number
  folder: WorkspaceFolder
}

function flattenFolderRows(folders: WorkspaceFolder[], depth = 0): FolderRow[] {
  return folders.flatMap((folder) => [
    { depth, folder },
    ...flattenFolderRows(folder.children ?? [], depth + 1),
  ])
}

function flattenFolderOptions(
  folders: WorkspaceFolder[],
  movingFolder?: WorkspaceFolder,
  parents: string[] = [],
): WorkspaceFolderOption[] {
  const blockedIds = movingFolder ? collectDescendantIds(movingFolder) : new Set<string>()
  if (movingFolder) {
    blockedIds.add(movingFolder.id)
  }

  return folders.flatMap((folder) => {
    const path = [...parents, folder.name]
    const children = flattenFolderOptions(folder.children ?? [], movingFolder, path)
    if (blockedIds.has(folder.id) || (movingFolder && folder.scope !== movingFolder.scope)) {
      return children
    }
    return [{ label: path.join(' / '), value: folder.id }, ...children]
  })
}

function buildFolderBreadcrumbs(folders: WorkspaceFolder[], folderId: string | null): WorkspaceFolder[] {
  if (!folderId) {
    return []
  }

  for (const folder of folders) {
    if (folder.id === folderId) {
      return [folder]
    }
    const childPath = buildFolderBreadcrumbs(folder.children ?? [], folderId)
    if (childPath.length) {
      return [folder, ...childPath]
    }
  }
  return []
}

function findFolderById(folders: WorkspaceFolder[], folderId: string | null | undefined): WorkspaceFolder | null {
  if (!folderId) {
    return null
  }

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

function findFirstFolderId(folders: WorkspaceFolder[]) {
  return folders[0]?.id ?? null
}

function collectDescendantIds(folder: WorkspaceFolder): Set<string> {
  const ids = new Set<string>()
  for (const child of folder.children ?? []) {
    ids.add(child.id)
    for (const descendantId of collectDescendantIds(child)) {
      ids.add(descendantId)
    }
  }
  return ids
}
</script>

<template>
  <section class="min-w-0 border-r border-line bg-surface max-lg:border-b max-lg:border-r-0">
    <div class="border-b border-line px-3 py-3">
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <h3 class="m-0 text-ink text-15px font-700">目录导航</h3>
          <p class="mt-1 panel-subtitle">树形目录、面包屑和上传目标</p>
        </div>
        <NButton data-testid="open-create-folder" size="small" secondary @click="openCreatePanel">
          <template #icon>
            <NIcon aria-hidden="true"><FolderPlus /></NIcon>
          </template>
          新建
        </NButton>
      </div>

      <div
        data-testid="folder-breadcrumbs"
        class="mt-3 flex min-h-24px flex-wrap items-center gap-1 text-12px text-sub"
      >
        <template v-if="activeBreadcrumbs.length">
          <template v-for="(folder, index) in activeBreadcrumbs" :key="folder.id">
            <NButton text size="tiny" @click="emit('select-folder', folder.id)">
              {{ folder.name }}
            </NButton>
            <NIcon v-if="index < activeBreadcrumbs.length - 1" aria-hidden="true" size="13">
              <ChevronRight />
            </NIcon>
          </template>
        </template>
        <span v-else>未选择目录</span>
      </div>
    </div>

    <div v-if="createPanelOpen" class="border-b border-line bg-muted px-3 py-3">
      <div class="grid gap-2">
        <NInput v-model:value="createName" placeholder="文件夹名称" :disabled="creatingFolder" />
        <NSelect
          v-model:value="createParentId"
          :options="parentOptions"
          :disabled="creatingFolder"
          placeholder="父级目录"
        />
        <div class="flex items-center justify-between gap-2">
          <span class="mono-chip">{{ createScopeLabel }}</span>
          <NSpace :wrap="false">
            <NButton size="small" :disabled="creatingFolder" @click="createPanelOpen = false">取消</NButton>
            <NButton
              data-testid="submit-create-folder"
              size="small"
              type="primary"
              :loading="creatingFolder"
              @click="handleCreateFolder"
            >
              创建
            </NButton>
          </NSpace>
        </div>
        <NAlert v-if="createError" type="warning" :bordered="false">
          {{ createError }}
        </NAlert>
      </div>
    </div>

    <div class="grid max-h-360px gap-1 overflow-auto p-2">
      <NSpin v-if="folderTreeLoading" size="small" />
      <div v-for="row in folderRows" :key="row.folder.id" :style="{ paddingLeft: `${row.depth * 12}px` }">
        <NButton
          :data-testid="`folder-node-${row.folder.id}`"
          class="!h-34px !justify-start"
          block
          :secondary="isFolderActive(row.folder.id)"
          :quaternary="!isFolderActive(row.folder.id)"
          :type="isFolderActive(row.folder.id) ? 'primary' : 'default'"
          @click="emit('select-folder', row.folder.id)"
        >
          <template #icon>
            <NIcon aria-hidden="true">
              <FolderOpen v-if="isFolderActive(row.folder.id)" />
              <Folder v-else />
            </NIcon>
          </template>
          <span class="min-w-0 truncate text-13px">{{ row.folder.name }}</span>
        </NButton>
      </div>
    </div>

    <div class="border-t border-line px-3 py-3">
      <div class="flex items-center gap-2">
        <NIcon aria-hidden="true" class="text-primary"><Edit3 /></NIcon>
        <h3 class="m-0 text-ink text-15px font-700">当前目录</h3>
      </div>

      <div v-if="activeFolder" class="mt-3 grid gap-2">
        <NInput
          v-model:value="editName"
          placeholder="重命名目录"
          :disabled="activeFolderIsRoot || updatingFolderId === activeFolder.id"
        />
        <NSelect
          v-model:value="editParentId"
          :options="moveTargetOptions"
          :disabled="activeFolderIsRoot || updatingFolderId === activeFolder.id"
          placeholder="移动到"
        />
        <div class="flex flex-wrap items-center justify-between gap-2">
          <span class="mono-chip">{{ activeFolder.permission }}</span>
          <NSpace :wrap="false">
            <NButton
              data-testid="submit-update-folder"
              size="small"
              secondary
              :disabled="updateDisabled"
              :loading="updatingFolderId === activeFolder.id"
              @click="handleUpdateFolder"
            >
              <template #icon>
                <NIcon aria-hidden="true"><MoveRight /></NIcon>
              </template>
              保存变更
            </NButton>
            <NButton
              :data-testid="`delete-folder-${activeFolder.id}`"
              size="small"
              type="error"
              secondary
              :disabled="activeFolderIsRoot"
              :loading="deletingFolderId === activeFolder.id"
              @click="handleDeleteFolder"
            >
              <template #icon>
                <NIcon aria-hidden="true"><Trash2 /></NIcon>
              </template>
              删除
            </NButton>
          </NSpace>
        </div>
        <p v-if="activeFolderIsRoot" class="m-0 text-12px text-sub leading-[1.5]">
          根目录用于区分个人空间和团队空间，不能重命名、移动或删除。
        </p>
        <NAlert v-if="editError" type="warning" :bordered="false">
          {{ editError }}
        </NAlert>
      </div>
      <p v-else class="m-0 mt-3 text-13px text-sub">请选择一个目录后编辑。</p>
    </div>
  </section>
</template>
