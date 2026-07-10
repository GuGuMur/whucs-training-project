<script setup lang="ts">
import { computed, shallowRef } from 'vue'
import { BookOpenText, FilePlus2, Plus, Send, Sparkles } from '@lucide/vue'

import type {
  WorkspaceFile,
  WorkspaceKnowledgeBase,
  WorkspaceKnowledgeBaseCreateInput,
  WorkspaceKnowledgeDocument,
  WorkspaceNarrative,
  WorkspaceQuestionInput,
} from '@/client/workspace'
import StatusChip from '../files/StatusChip.vue'

const props = withDefaults(defineProps<{
  activeKnowledgeBaseId?: string | null
  addingKnowledgeDocument?: boolean
  askingQuestion?: boolean
  indexedFiles?: WorkspaceFile[]
  knowledgeBases?: WorkspaceKnowledgeBase[]
  knowledgeDocuments?: WorkspaceKnowledgeDocument[]
  loadingKnowledge?: boolean
  narrative: WorkspaceNarrative
}>(), {
  activeKnowledgeBaseId: null,
  addingKnowledgeDocument: false,
  askingQuestion: false,
  indexedFiles: () => [],
  knowledgeBases: () => [],
  knowledgeDocuments: () => [],
  loadingKnowledge: false,
})

const emit = defineEmits<{
  'add-knowledge-document': [kbId: string, fileId: string]
  'ask-question': [payload: WorkspaceQuestionInput]
  'create-knowledge-base': [payload: WorkspaceKnowledgeBaseCreateInput]
  'select-knowledge-base': [kbId: string]
}>()

const createName = shallowRef('')
const createDescription = shallowRef('')
const questionText = shallowRef('')

const activeKnowledgeBase = computed(
  () => props.knowledgeBases.find((knowledgeBase) => knowledgeBase.id === props.activeKnowledgeBaseId) ?? props.knowledgeBases[0] ?? null,
)
const activeKnowledgeBaseId = computed(() => activeKnowledgeBase.value?.id ?? '')
const addableFiles = computed(() =>
  props.indexedFiles.filter((file) => !activeKnowledgeBaseId.value || !file.knowledge_base_ids.includes(activeKnowledgeBaseId.value)),
)
const canCreateKnowledgeBase = computed(() => Boolean(createName.value.trim()))
const canAskQuestion = computed(() => Boolean(activeKnowledgeBaseId.value && questionText.value.trim()))

function handleCreateKnowledgeBase() {
  const name = createName.value.trim()
  if (!name) {
    return
  }

  const description = createDescription.value.trim()
  emit('create-knowledge-base', {
    description: description || null,
    name,
  })
  createName.value = ''
  createDescription.value = ''
}

function handleAskQuestion() {
  const question = questionText.value.trim()
  if (!activeKnowledgeBaseId.value || !question) {
    return
  }

  emit('ask-question', {
    kbId: activeKnowledgeBaseId.value,
    question,
    topK: 5,
  })
}

function statusLabel(status: WorkspaceKnowledgeDocument['index_status']) {
  if (status === 'indexed') {
    return '已索引'
  }
  if (status === 'indexing') {
    return '索引中'
  }
  if (status === 'failed') {
    return '索引失败'
  }
  return '等待索引'
}

function statusType(status: WorkspaceKnowledgeDocument['index_status']) {
  if (status === 'indexed') {
    return 'success'
  }
  if (status === 'failed') {
    return 'error'
  }
  return 'warning'
}
</script>

<template>
  <NCard id="rag" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" size="small">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div class="flex min-w-0 items-center gap-2">
          <NIcon aria-hidden="true"><Sparkles /></NIcon>
          <h2 class="panel-title truncate">RAG 知识问答</h2>
        </div>
        <StatusChip tone="knowledge" label="引用可追溯" />
      </div>
    </template>

    <div class="grid gap-4">
      <section class="grid gap-2" aria-label="创建知识库">
        <div class="grid grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)_auto] gap-2 max-lg:grid-cols-1">
          <NInput v-model:value="createName" clearable placeholder="知识库名称" :disabled="loadingKnowledge" />
          <NInput
            v-model:value="createDescription"
            clearable
            placeholder="知识库说明"
            type="textarea"
            :autosize="{ minRows: 1, maxRows: 2 }"
            :disabled="loadingKnowledge"
          />
          <NButton
            data-testid="submit-create-kb"
            type="primary"
            :disabled="!canCreateKnowledgeBase"
            :loading="loadingKnowledge"
            @click="handleCreateKnowledgeBase"
          >
            <template #icon>
              <NIcon aria-hidden="true"><Plus /></NIcon>
            </template>
            创建
          </NButton>
        </div>
      </section>

      <section class="grid gap-2" aria-label="知识库列表">
        <div class="flex items-center justify-between gap-3">
          <h3 class="m-0 text-ink text-15px font-700">知识库</h3>
          <span class="text-sub text-12px">{{ knowledgeBases.length }} 个</span>
        </div>
        <NEmpty v-if="!knowledgeBases.length" size="small" description="暂无知识库" />
        <div v-else class="grid gap-2">
          <button
            v-for="knowledgeBase in knowledgeBases"
            :key="knowledgeBase.id"
            type="button"
            :data-testid="`select-kb-${knowledgeBase.id}`"
            class="w-full border rounded-2 px-3 py-2 text-left transition-colors"
            :class="knowledgeBase.id === activeKnowledgeBaseId ? 'border-knowledge bg-#F1EEFF' : 'border-line bg-surface hover:bg-muted'"
            @click="emit('select-knowledge-base', knowledgeBase.id)"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="m-0 truncate text-ink text-14px font-700">{{ knowledgeBase.name }}</p>
                <p class="m-0 mt-1 line-clamp-2 text-sub text-12px leading-[1.65]">
                  {{ knowledgeBase.description || '未填写知识库说明' }}
                </p>
              </div>
              <div class="shrink-0 text-right text-sub text-12px leading-[1.5]">
                <div>{{ knowledgeBase.document_count }} 文档</div>
                <div>{{ knowledgeBase.chunk_count }} 片段</div>
              </div>
            </div>
          </button>
        </div>
      </section>

      <section class="grid gap-2" aria-label="知识库文档">
        <div class="flex items-center justify-between gap-3">
          <div class="flex min-w-0 items-center gap-2">
            <NIcon aria-hidden="true"><BookOpenText /></NIcon>
            <h3 class="m-0 truncate text-ink text-15px font-700">入库文档</h3>
          </div>
          <NTag size="small" round :bordered="false" type="info">
            {{ activeKnowledgeBase?.name || '未选择' }}
          </NTag>
        </div>

        <NEmpty v-if="!knowledgeDocuments.length" size="small" description="当前知识库暂无文档" />
        <NList v-else :show-divider="false">
          <NListItem v-for="document in knowledgeDocuments" :key="document.id" class="!px-0 !py-2">
            <div class="flex items-center justify-between gap-3 border border-line rounded-2 bg-#F8FAFD px-3 py-2">
              <div class="min-w-0">
                <p class="m-0 truncate text-ink text-13px font-700">{{ document.file_name }}</p>
                <p class="m-0 mt-0.5 text-sub text-12px">{{ document.chunk_count }} 个片段</p>
              </div>
              <NTag size="small" round :bordered="false" :type="statusType(document.index_status)">
                {{ statusLabel(document.index_status) }}
              </NTag>
            </div>
          </NListItem>
        </NList>

        <div v-if="addableFiles.length && activeKnowledgeBaseId" class="grid gap-2">
          <p class="m-0 text-sub text-12px">可入库文件</p>
          <div class="grid gap-2">
            <NButton
              v-for="file in addableFiles.slice(0, 3)"
              :key="file.id"
              :data-testid="`add-kb-document-${file.id}`"
              secondary
              size="small"
              :loading="addingKnowledgeDocument"
              @click="emit('add-knowledge-document', activeKnowledgeBaseId, file.id)"
            >
              <template #icon>
                <NIcon aria-hidden="true"><FilePlus2 /></NIcon>
              </template>
              {{ file.name }}
            </NButton>
          </div>
        </div>
      </section>

      <section class="grid gap-2" aria-label="知识库提问">
        <NInput
          v-model:value="questionText"
          placeholder="输入问题"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 4 }"
          :disabled="askingQuestion"
        />
        <NButton
          data-testid="submit-rag-question"
          type="primary"
          :disabled="!canAskQuestion"
          :loading="askingQuestion"
          @click="handleAskQuestion"
        >
          <template #icon>
            <NIcon aria-hidden="true"><Send /></NIcon>
          </template>
          提问
        </NButton>
      </section>

      <section class="grid gap-3" aria-label="问答结果">
        <p class="m-0 text-ink text-14px leading-[1.65]">{{ narrative.answer }}</p>

        <NDivider class="!my-1" />
        <h3 class="m-0 panel-title">引用来源</h3>
        <NEmpty v-if="!narrative.citations.length" size="small" description="暂无引用" />
        <NList v-else bordered>
          <NListItem v-for="citation in narrative.citations" :key="citation.chunk_id">
            <NThing :title="citation.title">
              <template #description>第 {{ citation.page_no }} 页 · 第 {{ citation.paragraph_no }} 段</template>
              <p class="m-0 text-ink text-13px leading-[1.55]">{{ citation.snippet }}</p>
            </NThing>
          </NListItem>
        </NList>
      </section>
    </div>
  </NCard>
</template>
