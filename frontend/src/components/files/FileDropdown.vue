<script setup lang="ts">
import { MoreHorizontal, Download, Pencil, FolderInput, Copy, Tag, MessageSquareText, ShieldCheck, History, Trash2, RefreshCw, Eye } from '@lucide/vue'
import { h } from 'vue'
import { NButton, NIcon } from 'naive-ui'
import type { WorkspaceFile } from '@/client/workspace'

defineProps<{
  file: WorkspaceFile
  annotationCount?: number
  reparsing?: boolean
  versionCount?: number
}>()

const emit = defineEmits<{
  download: [file: WorkspaceFile]
  rename: [file: WorkspaceFile]
  move: [file: WorkspaceFile]
  copy: [file: WorkspaceFile]
  tags: [file: WorkspaceFile]
  reparse: [file: WorkspaceFile]
  annotate: [file: WorkspaceFile]
  permissions: [file: WorkspaceFile]
  preview: [file: WorkspaceFile]
  versions: [file: WorkspaceFile]
  delete: [file: WorkspaceFile]
}>()

type DropdownOption = {
  label: string
  key: string
  icon?: () => ReturnType<typeof h>
}

function handleSelect(key: string) {
  // file is accessed via template — we get it passed via data attribute or closure
  // Actually, we need the file reference. We'll use a different approach.
}
</script>

<template>
  <NPopover trigger="click" placement="bottom-end" :show-arrow="false" :width="200">
    <template #trigger>
      <NButton text size="tiny" class="text-sub hover:text-ink">
        <template #icon><NIcon :size="18"><MoreHorizontal /></NIcon></template>
      </NButton>
    </template>
    <div class="grid gap-1 py-1">
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('download', file)">
        <NIcon :size="16"><Download /></NIcon><span>下载</span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('preview', file)">
        <NIcon :size="16"><Eye /></NIcon><span>预览/编辑</span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('rename', file)">
        <NIcon :size="16"><Pencil /></NIcon><span>重命名</span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('move', file)">
        <NIcon :size="16"><FolderInput /></NIcon><span>移动到...</span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('copy', file)">
        <NIcon :size="16"><Copy /></NIcon><span>复制到...</span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('tags', file)">
        <NIcon :size="16"><Tag /></NIcon><span>修改标签</span>
      </button>
      <button v-if="file.parse_status === 'queued' || file.parse_status === 'failed'" class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full disabled:cursor-not-allowed disabled:opacity-55" :disabled="reparsing" @click="emit('reparse', file)">
        <NIcon :size="16" :class="{ 'animate-spin': reparsing }"><RefreshCw /></NIcon><span>{{ reparsing ? '解析中' : '重新解析' }}</span>
      </button>
      <div class="my-1 border-t border-line" />
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('annotate', file)">
        <NIcon :size="16"><MessageSquareText /></NIcon><span>批注<span v-if="annotationCount" class="ml-1 text-11px text-sub">({{ annotationCount }})</span></span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('permissions', file)">
        <NIcon :size="16"><ShieldCheck /></NIcon><span>权限设置</span>
      </button>
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-ink transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('versions', file)">
        <NIcon :size="16"><History /></NIcon><span>版本历史<span v-if="versionCount" class="ml-1 text-11px text-sub">({{ versionCount }})</span></span>
      </button>
      <div class="my-1 border-t border-line" />
      <button class="flex items-center gap-2 rounded-1 px-3 py-2 text-left text-13px text-danger transition-colors hover:bg-primarySoft border-none bg-transparent cursor-pointer w-full" @click="emit('delete', file)">
        <NIcon :size="16"><Trash2 /></NIcon><span>删除</span>
      </button>
    </div>
  </NPopover>
</template>
