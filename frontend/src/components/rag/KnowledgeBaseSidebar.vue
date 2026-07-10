<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { Database, Edit3, Plus, Trash2 } from '@lucide/vue'

import type { WorkspaceKnowledgeBase } from '@/client/workspace'

const props = withDefaults(defineProps<{
  activeKbId?: string | null
  knowledgeBases?: WorkspaceKnowledgeBase[]
  loading?: boolean
}>(), {
  activeKbId: null,
  knowledgeBases: () => [],
  loading: false,
})

const emit = defineEmits<{
  create: []
  delete: [kbId: string]
  edit: [kb: WorkspaceKnowledgeBase]
  select: [kbId: string]
}>()

const keyword = shallowRef('')

const filteredKnowledgeBases = computed(() => {
  const query = keyword.value.trim().toLowerCase()
  if (!query) return props.knowledgeBases
  return props.knowledgeBases.filter((kb) =>
    [kb.name, kb.description, kb.category ?? '', ...(kb.tags ?? [])]
      .join(' ')
      .toLowerCase()
      .includes(query),
  )
})

function scopeLabel(kb: WorkspaceKnowledgeBase) {
  return kb.scope_type === 'team' ? '团队' : '个人'
}
</script>

<template>
  <aside class="grid gap-3" aria-label="知识库导航">
    <div class="flex items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-2">
        <NIcon aria-hidden="true"><Database /></NIcon>
        <h2 class="m-0 truncate text-ink text-16px font-750">知识库</h2>
      </div>
      <NButton size="small" type="primary" ghost :loading="loading" @click="emit('create')">
        <template #icon><NIcon aria-hidden="true"><Plus /></NIcon></template>
      </NButton>
    </div>

    <NInput v-model:value="keyword" clearable size="small" placeholder="搜索名称、分类或标签" />

    <NEmpty v-if="!filteredKnowledgeBases.length" size="small" description="暂无知识库" />
    <div v-else class="grid gap-2">
      <article
        v-for="kb in filteredKnowledgeBases"
        :key="kb.id"
        class="group relative rounded-2 bg-#F7F9FC px-3 py-2 transition-colors hover:bg-#EEF5FF"
        :class="kb.id === activeKbId ? 'bg-#EEF5FF shadow-[inset_3px_0_0_#2F6BFF]' : ''"
      >
        <button
          type="button"
          class="w-full border-0 bg-transparent p-0 text-left outline-none"
          @click="emit('select', kb.id)"
        >
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="m-0 truncate text-ink text-14px font-700">{{ kb.name }}</p>
              <p class="m-0 mt-1 line-clamp-2 text-sub text-12px leading-[1.65]">
                {{ kb.description || '未填写说明' }}
              </p>
            </div>
            <NTag size="small" round :bordered="false">{{ scopeLabel(kb) }}</NTag>
          </div>
        </button>
        <div class="mt-2 flex flex-wrap items-center gap-1">
          <NTag v-if="kb.category" size="small" round :bordered="false" type="info">{{ kb.category }}</NTag>
          <NTag v-for="tag in kb.tags ?? []" :key="tag" size="small" round :bordered="false">{{ tag }}</NTag>
          <span class="ml-auto text-sub text-11px">{{ kb.document_count }} 文档 · {{ kb.chunk_count }} 片段</span>
        </div>
        <div class="mt-2 flex justify-end gap-2">
          <NButton size="tiny" text quaternary @click="emit('edit', kb)">
            <template #icon><NIcon aria-hidden="true"><Edit3 /></NIcon></template>
          </NButton>
          <NButton size="tiny" text quaternary type="error" @click="emit('delete', kb.id)">
            <template #icon><NIcon aria-hidden="true"><Trash2 /></NIcon></template>
          </NButton>
        </div>
      </article>
    </div>
  </aside>
</template>
