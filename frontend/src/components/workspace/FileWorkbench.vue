<script setup lang="ts">
import { computed, h, shallowRef } from 'vue'
import { FolderPlus, Upload } from '@lucide/vue'
import type { DataTableColumns } from 'naive-ui'
import { NButton, NDataTable, NTag } from 'naive-ui'

import type { WorkspaceFile } from '@/client/workspace'
import StatusChip from './StatusChip.vue'

const props = defineProps<{
  files: WorkspaceFile[]
}>()

const selectedTag = shallowRef('全部')

const tagOptions = computed(() => ['全部', ...new Set(props.files.flatMap((file) => file.tags))])
const visibleFiles = computed(() =>
  selectedTag.value === '全部'
    ? props.files
    : props.files.filter((file) => file.tags.includes(selectedTag.value)),
)

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
          <NButton type="primary">
            <template #icon>
              <NIcon aria-hidden="true"><Upload /></NIcon>
            </template>
            上传文件
          </NButton>
          <NButton>
            <template #icon>
              <NIcon aria-hidden="true"><FolderPlus /></NIcon>
            </template>
            新建文件夹
          </NButton>
        </NSpace>
      </div>
    </template>

    <div class="border-b border-line bg-muted p-3">
      <NSpace>
        <NButton
          v-for="tag in tagOptions"
          :key="tag"
          size="small"
          :type="selectedTag === tag ? 'primary' : 'default'"
          secondary
          @click="selectedTag = tag"
        >
          {{ tag }}
        </NButton>
      </NSpace>
    </div>

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
        </div>
      </NListItem>
    </NList>
  </NCard>
</template>
