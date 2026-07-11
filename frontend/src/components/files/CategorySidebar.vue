<script setup lang="ts">
import { computed, h, nextTick, ref, shallowRef } from 'vue'
import { ChevronDown, ChevronRight, Files, FileText, Folder, FolderArchive, FolderPlus, Image, MoreHorizontal, Pencil, Plus, Share2, Trash2, Video } from '@lucide/vue'
import { NButton, NDropdown, NIcon, NInput, NModal, NSpin } from 'naive-ui'
import type { WorkspaceFolder } from '@/client/workspace'

const props = withDefaults(defineProps<{
  activeCategory?: string
  folders?: WorkspaceFolder[]
  folderTreeLoading?: boolean
}>(), {
  activeCategory: 'all',
  folders: () => [],
  folderTreeLoading: false,
})

const emit = defineEmits<{
  'select-category': [key: string]
  'select-folder': [folderId: string]
  'create-folder': [payload: { name: string; parentId?: string | null; scope?: string }]
  'rename-folder': [folderId: string, name: string]
  'delete-folder': [folderId: string]
}>()

const categories = [
  { key: 'all', label: '全部文件', icon: Files },
  { key: 'image', label: '图片', icon: Image },
  { key: 'document', label: '文档', icon: FileText },
  { key: 'video', label: '视频', icon: Video },
  { key: 'other', label: '其他', icon: FolderArchive },
  { key: 'shared', label: '共享给我的', icon: Share2 },
  { key: 'recycle', label: '回收站', icon: Trash2 },
] as const

const categoryEntries: { key: string; label: string; icon: typeof Files }[] = [...categories]

const personalFolders = computed(() => props.folders.filter(f => f.scope !== 'team'))
const teamFolders = computed(() => props.folders.filter(f => f.scope === 'team'))

// ── Expanded state ──
const expandedIds = shallowRef<Set<string>>(new Set())

function toggleExpand(folderId: string) {
  const next = new Set(expandedIds.value)
  if (next.has(folderId)) { next.delete(folderId) } else { next.add(folderId) }
  expandedIds.value = next
}

// ── Creating folder ──
const creatingParentId = shallowRef<string | null | undefined>(undefined)
const creatingName = ref('')

function startCreate(parentId?: string | null) {
  creatingParentId.value = parentId ?? undefined
  creatingName.value = ''
  nextTick(() => {
    const el = document.querySelector<HTMLInputElement>('[data-testid="folder-create-input"]')
    el?.focus()
  })
}

function confirmCreate() {
  const name = creatingName.value.trim()
  if (!name) { cancelCreate(); return }
  emit('create-folder', { name, parentId: creatingParentId.value ?? null, scope: 'personal' })
  cancelCreate()
}

function cancelCreate() {
  creatingParentId.value = null
  creatingName.value = ''
}

// ── Renaming folder ──
const renamingFolderId = shallowRef<string | null>(null)
const renamingName = ref('')

function startRename(folder: WorkspaceFolder) {
  renamingFolderId.value = folder.id
  renamingName.value = folder.name
  nextTick(() => {
    const el = document.querySelector<HTMLInputElement>('[data-testid="folder-rename-input"]')
    el?.focus()
    el?.select()
  })
}

function confirmRename() {
  const name = renamingName.value.trim()
  if (!name || !renamingFolderId.value) { cancelRename(); return }
  emit('rename-folder', renamingFolderId.value, name)
  cancelRename()
}

function cancelRename() {
  renamingFolderId.value = null
  renamingName.value = ''
}

// ── Delete confirm ──
const deleteTargetId = shallowRef<string | null>(null)
const deleteTargetName = shallowRef('')

function confirmDeleteFolder() {
  if (deleteTargetId.value) {
    emit('delete-folder', deleteTargetId.value)
  }
  deleteTargetId.value = null
  deleteTargetName.value = ''
}

// ── Context menu options ──
function folderMenuOptions(folder: WorkspaceFolder) {
  return [
    { label: '新建子文件夹', key: 'create', icon: () => h(NIcon, { size: 14 }, () => h(FolderPlus)) },
    { label: '重命名', key: 'rename', icon: () => h(NIcon, { size: 14 }, () => h(Pencil)) },
    { type: 'divider' as const, key: 'd1' },
    { label: '删除', key: 'delete', icon: () => h(NIcon, { size: 14 }, () => h(Trash2)) },
  ]
}

function handleFolderMenuSelect(key: string, folder: WorkspaceFolder) {
  switch (key) {
    case 'create': startCreate(folder.id); break
    case 'rename': startRename(folder); break
    case 'delete': deleteTargetId.value = folder.id; deleteTargetName.value = folder.name; break
  }
}

// ── Recursive folder node render ──
const FOLDER_ITEM_CLASS = 'flex items-center gap-1 rounded-1 px-2 py-1.5 cursor-pointer text-13px text-sub hover:bg-muted transition-colors group/fol'

function renderFolderNode(folder: WorkspaceFolder, depth: number): ReturnType<typeof h> {
  const isExpanded = expandedIds.value.has(folder.id)
  const isCreating = creatingParentId.value === folder.id
  const isRenaming = renamingFolderId.value === folder.id
  const hasChildren = folder.children && folder.children.length > 0

  const children: any[] = []
  const rowChildren: any[] = []

  // Indent spacer
  for (let i = 0; i < depth; i++) {
    rowChildren.push(h('span', { class: 'w-4 shrink-0' }))
  }

  // Expand/collapse chevron
  if (hasChildren) {
    rowChildren.push(
      h(NButton, {
        size: 'tiny', text: true, class: '!w-4 !h-4 !p-0 shrink-0',
        onClick: (e: Event) => { e.stopPropagation(); toggleExpand(folder.id) },
      }, () => h(NIcon, { size: 10 }, () => h(isExpanded ? ChevronDown : ChevronRight)))
    )
  } else {
    rowChildren.push(h('span', { class: 'w-4 shrink-0' }))
  }

  // Folder icon
  rowChildren.push(
    h(NIcon, { size: 14, color: 'var(--sub-color, #5D6B82)' }, () => h(Folder))
  )

  // Name or rename input
  if (isRenaming) {
    rowChildren.push(
      h('span', { class: 'flex-1 min-w-0' }, [
        h(NInput, {
          size: 'tiny', value: renamingName.value,
          'data-testid': 'folder-rename-input',
          onUpdateValue: (v: string) => { renamingName.value = v },
          onKeyup: (e: KeyboardEvent) => {
            if (e.key === 'Enter') confirmRename()
            if (e.key === 'Escape') cancelRename()
          },
          onBlur: confirmRename,
          style: { height: '22px' },
        }),
      ])
    )
  } else {
    rowChildren.push(
      h('span', {
        class: 'flex-1 min-w-0 truncate font-550',
        onClick: () => emit('select-folder', folder.id),
      }, folder.name)
    )
  }

  // Hover actions (only when not editing)
  if (!isRenaming && !isCreating) {
    rowChildren.push(
      h(NDropdown, {
        options: folderMenuOptions(folder),
        trigger: 'click',
        placement: 'right-start',
        size: 'small',
        onSelect: (key: string) => handleFolderMenuSelect(key, folder),
      }, () =>
        h(NButton, {
          size: 'tiny', text: true,
          class: '!w-5 !h-5 !p-0 shrink-0 opacity-0 group-hover/fol:opacity-100 transition-opacity',
          onClick: (e: Event) => e.stopPropagation(),
        }, () => h(NIcon, { size: 12 }, () => h(MoreHorizontal)))
      )
    )
  }

  children.push(
    h('div', { class: FOLDER_ITEM_CLASS, key: folder.id }, rowChildren)
  )

  // Inline create input below this folder
  if (isCreating) {
    children.push(
      h('div', {
        class: 'flex items-center gap-1 px-2 py-0.5',
        style: { paddingLeft: `${(depth + 1) * 16 + 8}px` },
      }, [
        h(NIcon, { size: 12, color: 'var(--sub-color)' }, () => h(FolderPlus)),
        h(NInput, {
          size: 'tiny', value: creatingName.value, placeholder: '文件夹名称',
          'data-testid': 'folder-create-input',
          onUpdateValue: (v: string) => { creatingName.value = v },
          onKeyup: (e: KeyboardEvent) => {
            if (e.key === 'Enter') confirmCreate()
            if (e.key === 'Escape') cancelCreate()
          },
          onBlur: confirmCreate,
          style: { height: '24px', flex: 1 },
        }),
      ])
    )
  }

  // Children
  if (isExpanded && hasChildren) {
    for (const child of folder.children ?? []) {
      children.push(renderFolderNode(child, depth + 1))
    }
  }

  return h('div', { key: folder.id }, children)
}
</script>

<template>
  <aside class="flex flex-col gap-0.5 overflow-y-auto px-3 py-3" aria-label="分类导航">
    <!-- Category buttons -->
    <button
      v-for="cat in categoryEntries.slice(0, 5)" :key="cat.key"
      class="flex w-full cursor-pointer items-center gap-2.5 rounded-1.5 border-none px-3 py-2.5 text-left text-13px font-550 transition-colors"
      :class="activeCategory === cat.key ? 'bg-primarySoft text-primary' : 'text-sub hover:bg-muted'"
      @click="emit('select-category', cat.key)"
    >
      <NIcon :size="16"><component :is="cat.icon" /></NIcon>
      <span>{{ cat.label }}</span>
    </button>

    <div class="my-1.5 border-t border-line" />

    <!-- Shared + Recycle -->
    <button
      v-for="cat in categoryEntries.slice(5, 7)" :key="cat.key"
      class="flex w-full cursor-pointer items-center gap-2.5 rounded-1.5 border-none px-3 py-2.5 text-left text-13px font-550 transition-colors"
      :class="activeCategory === cat.key ? 'bg-primarySoft text-primary' : 'text-sub hover:bg-muted'"
      @click="emit('select-category', cat.key)"
    >
      <NIcon :size="16"><component :is="cat.icon" /></NIcon>
      <span>{{ cat.label }}</span>
    </button>

    <div class="my-1.5 border-t border-line" />

    <!-- Personal folders header -->
    <div class="flex items-center justify-between px-3 py-1">
      <p class="text-11px text-sub font-650 uppercase tracking-wider my-0">个人文件</p>
      <NButton size="tiny" text class="!w-5 !h-5 !p-0" @click="startCreate()" data-testid="folder-create-root-btn">
        <NIcon :size="14"><Plus /></NIcon>
      </NButton>
    </div>

    <!-- Root-level create input -->
    <div v-if="creatingParentId === undefined" class="flex items-center gap-2 px-3 py-1 mb-1">
      <NIcon :size="14" color="var(--sub-color)"><FolderPlus /></NIcon>
      <NInput
        size="tiny" v-model:value="creatingName" placeholder="文件夹名称"
        data-testid="folder-create-input" style="height:24px; flex:1"
        @keyup.enter="confirmCreate" @keyup.escape="cancelCreate"
        @blur="confirmCreate"
      />
    </div>

    <!-- Personal folder tree -->
    <NSpin :show="folderTreeLoading" size="small">
      <div v-if="personalFolders.length" class="flex flex-col">
        <component
          :is="renderFolderNode(f, 0)"
          v-for="f in personalFolders"
          :key="f.id"
        />
      </div>
      <p v-else-if="!folderTreeLoading && creatingParentId === undefined" class="px-3 py-2 text-12px text-sub">
        暂无个人文件夹，点击 + 创建
      </p>
    </NSpin>

    <!-- Team folders -->
    <div v-if="teamFolders.length" class="my-1.5 border-t border-line" />
    <p v-if="teamFolders.length" class="px-3 py-1 text-11px text-sub font-650 uppercase tracking-wider">团队空间</p>
    <NSpin v-if="teamFolders.length" :show="folderTreeLoading" size="small">
      <div class="flex flex-col">
        <component
          :is="renderFolderNode(f, 0)"
          v-for="f in teamFolders"
          :key="f.id"
        />
      </div>
    </NSpin>

    <!-- Delete confirmation modal -->
    <NModal :show="!!deleteTargetId" preset="card" title="确认删除" style="width: 400px" @update:show="(v: boolean) => { if (!v) deleteTargetId = null }">
      <p class="m-0 text-ink">确定要删除文件夹 <strong>{{ deleteTargetName }}</strong> 吗？子文件夹和文件将被移回个人空间根目录。</p>
      <template #footer>
        <div class="flex justify-end gap-2">
          <NButton @click="deleteTargetId = null">取消</NButton>
          <NButton type="error" @click="confirmDeleteFolder">确认删除</NButton>
        </div>
      </template>
    </NModal>
  </aside>
</template>
