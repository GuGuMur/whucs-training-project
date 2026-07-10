<script setup lang="ts">
import { computed, h } from 'vue'
import { ChevronDown, ChevronRight, Files, FileText, Folder, FolderArchive, Image, Share2, Trash2, Video } from '@lucide/vue'
import { NIcon, NSpin, NTree, type TreeOption } from 'naive-ui'
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

function toTree(folders: WorkspaceFolder[]): TreeOption[] {
  return folders.map((f) => ({
    key: f.id,
    label: f.name,
    prefix: () =>
      h(
        NIcon,
        { size: 14, color: 'var(--sub-color, #5D6B82)' },
        () => h(Folder),
      ),
    children: f.children?.length ? toTree(f.children) : undefined,
  }))
}

const treeOptions = computed(() => toTree(props.folders))
const personalFolders = computed(() => toTree(props.folders.filter(f => f.scope !== 'team')))
const teamFolders = computed(() => toTree(props.folders.filter(f => f.scope === 'team')))

const categoryEntries: { key: string; label: string; icon: typeof Files }[] = [
  ...categories,
]
</script>

<template>
  <aside
    class="flex flex-col gap-0.5 overflow-y-auto px-3 py-3"
    aria-label="分类导航"
  >
    <!-- Category buttons: all, image, document, video, other -->
    <button
      v-for="cat in categoryEntries.slice(0, 5)"
      :key="cat.key"
      class="flex w-full cursor-pointer items-center gap-2.5 rounded-1.5 border-none px-3 py-2.5 text-left text-13px font-550 transition-colors"
      :class="activeCategory === cat.key ? 'bg-primarySoft text-primary' : 'text-sub hover:bg-muted'"
      @click="emit('select-category', cat.key)"
    >
      <NIcon :size="16">
        <component :is="cat.icon" />
      </NIcon>
      <span>{{ cat.label }}</span>
    </button>

    <!-- Divider before shared/recycle -->
    <div class="my-1.5 border-t border-line" />

    <!-- Shared + Recycle -->
    <button
      v-for="cat in categoryEntries.slice(5, 7)"
      :key="cat.key"
      class="flex w-full cursor-pointer items-center gap-2.5 rounded-1.5 border-none px-3 py-2.5 text-left text-13px font-550 transition-colors"
      :class="activeCategory === cat.key ? 'bg-primarySoft text-primary' : 'text-sub hover:bg-muted'"
      @click="emit('select-category', cat.key)"
    >
      <NIcon :size="16">
        <component :is="cat.icon" />
      </NIcon>
      <span>{{ cat.label }}</span>
    </button>

    <!-- Divider before folder tree -->
    <div class="my-1.5 border-t border-line" />

    <!-- Personal folders -->
    <p class="px-3 py-1 text-11px text-sub font-650 uppercase tracking-wider">个人文件</p>
    <NSpin :show="folderTreeLoading" size="small">
      <NTree v-if="personalFolders.length" :data="personalFolders" :default-expand-all="false" block-line selectable
        :render-switcher-icon="({ expanded }: { expanded: boolean }) => h(NIcon, { size: 14 }, () => h(expanded ? ChevronDown : ChevronRight))"
        @update:selected-keys="(keys: string[]) => keys[0] && emit('select-folder', keys[0])" />
      <p v-else class="px-3 py-2 text-12px text-sub">暂无个人文件夹</p>
    </NSpin>

    <!-- Team folders -->
    <div v-if="teamFolders.length" class="my-1.5 border-t border-line" />
    <p v-if="teamFolders.length" class="px-3 py-1 text-11px text-sub font-650 uppercase tracking-wider">团队空间</p>
    <NSpin v-if="teamFolders.length" :show="folderTreeLoading" size="small">
      <NTree :data="teamFolders" :default-expand-all="false" block-line selectable
        :render-switcher-icon="({ expanded }: { expanded: boolean }) => h(NIcon, { size: 14 }, () => h(expanded ? ChevronDown : ChevronRight))"
        @update:selected-keys="(keys: string[]) => keys[0] && emit('select-folder', keys[0])" />
    </NSpin>
  </aside>
</template>
