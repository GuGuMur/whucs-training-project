<script setup lang="ts">
import { computed, nextTick, shallowRef, watch } from 'vue'
import { MessageSquarePlus, MessageSquareText, Send, Trash2 } from '@lucide/vue'

import { renderMarkdown } from '@/composables/useMarkdown'
import type {
  WorkspaceKnowledgeConversation,
  WorkspaceKnowledgeMessage,
  WorkspaceQuestionInput,
  WorkspaceStreamEvent,
} from '@/client/workspace'
import KnowledgeCitationList from './KnowledgeCitationList.vue'

const props = withDefaults(defineProps<{
  activeConversationId?: string | null
  activeKbId?: string | null
  asking?: boolean
  conversations?: WorkspaceKnowledgeConversation[]
  deletingConversationId?: string | null
  isStreaming?: boolean
  loading?: boolean
  messages?: WorkspaceKnowledgeMessage[]
  streamingAnswer?: string
  streamingCitations?: WorkspaceStreamEvent['citations']
}>(), {
  activeConversationId: null,
  activeKbId: null,
  asking: false,
  conversations: () => [],
  deletingConversationId: null,
  isStreaming: false,
  loading: false,
  messages: () => [],
  streamingAnswer: '',
  streamingCitations: () => [],
})

const emit = defineEmits<{
  'ask-question': [payload: WorkspaceQuestionInput]
  'ask-question-stream': [payload: WorkspaceQuestionInput]
  'delete-conversation': [conversationId: string]
  'start-new-conversation': []
  'select-conversation': [conversationId: string]
}>()

const question = shallowRef('')
const messagesContainer = shallowRef<HTMLElement | null>(null)

const activeConversation = computed(
  () => props.conversations.find((conversation) => conversation.id === props.activeConversationId) ?? null,
)
const conversationTitle = computed(() => activeConversation.value?.title || '新对话')
const latestAssistantMessage = computed(
  () => [...props.messages].reverse().find((message) => message.role === 'assistant') ?? null,
)
const emptyMessage = computed(() => {
  if (!props.activeKbId) return '选择知识库后开始提问'
  return props.activeConversationId ? '该对话暂无消息' : '输入问题会创建一个新对话'
})

// Auto-scroll when streaming tokens arrive
watch(() => props.streamingAnswer, async () => {
  if (props.isStreaming) {
    await nextTick()
    messagesContainer.value?.scrollTo({ top: messagesContainer.value.scrollHeight, behavior: 'smooth' })
  }
})

function submitQuestion() {
  const text = question.value.trim()
  if (!props.activeKbId || !text) return
  emit('ask-question-stream', {
    conversationId: props.activeConversationId ?? null,
    kbId: props.activeKbId,
    question: text,
    topK: 8,
  })
  question.value = ''
}

function roleLabel(role: WorkspaceKnowledgeMessage['role']) {
  return role === 'assistant' ? '回答' : '问题'
}

function deleteConversation(conversationId: string) {
  emit('delete-conversation', conversationId)
}
</script>

<template>
  <section class="grid gap-4" aria-label="知识库会话">
    <div class="flex items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-2">
        <NIcon aria-hidden="true"><MessageSquareText /></NIcon>
        <h2 class="m-0 truncate text-ink text-16px font-750">多轮问答</h2>
      </div>
      <NButton
        data-testid="start-new-conversation"
        size="small"
        secondary
        :disabled="!activeKbId"
        @click="emit('start-new-conversation')"
      >
        <template #icon><NIcon aria-hidden="true"><MessageSquarePlus /></NIcon></template>
        新对话
      </NButton>
    </div>

    <div class="grid grid-cols-[260px_minmax(0,1fr)] gap-4 max-lg:grid-cols-1">
      <aside class="min-w-0 rounded-2 bg-#F7F9FC p-3" aria-label="历史对话">
        <div class="mb-2 flex items-center justify-between gap-2">
          <h3 class="m-0 text-ink text-14px font-700">历史对话</h3>
          <NTag size="small" round :bordered="false">{{ conversations.length }}</NTag>
        </div>
        <NEmpty v-if="!conversations.length" size="small" description="暂无历史对话" />
        <div v-else class="grid gap-2">
          <article
            v-for="conversation in conversations"
            :key="conversation.id"
            class="rounded-2 bg-white px-3 py-2 shadow-[inset_0_0_0_1px_#E6EAF2]"
            :class="conversation.id === activeConversationId ? 'shadow-[inset_3px_0_0_#2F6BFF]' : ''"
          >
            <button
              type="button"
              class="w-full border-0 bg-transparent p-0 text-left outline-none"
              :data-testid="`select-conversation-${conversation.id}`"
              @click="emit('select-conversation', conversation.id)"
            >
              <p class="m-0 truncate text-ink text-13px font-700">{{ conversation.title }}</p>
              <p class="m-0 mt-1 text-sub text-11px">
                {{ conversation.message_count }} 条 · {{ new Date(conversation.updated_at).toLocaleString() }}
              </p>
            </button>
            <div class="mt-2 flex items-center justify-between gap-2">
              <NButton
                size="tiny"
                text
                type="primary"
                :disabled="conversation.id === activeConversationId"
                @click="emit('select-conversation', conversation.id)"
              >
                {{ conversation.id === activeConversationId ? '继续中' : '查看并继续' }}
              </NButton>
              <NButton
                size="tiny"
                text
                type="error"
                :data-testid="`delete-conversation-${conversation.id}`"
                :loading="deletingConversationId === conversation.id"
                @click="deleteConversation(conversation.id)"
              >
                <template #icon><NIcon aria-hidden="true"><Trash2 /></NIcon></template>
              </NButton>
            </div>
          </article>
        </div>
      </aside>

      <div class="grid min-w-0 gap-3">
        <div class="flex items-center justify-between gap-3 rounded-2 bg-#F7F9FC px-3 py-2">
          <div class="min-w-0">
            <p class="m-0 truncate text-ink text-14px font-750">{{ conversationTitle }}</p>
            <p class="m-0 mt-1 text-sub text-12px">
              {{ activeConversation ? '正在查看并继续旧对话' : '准备开始新对话' }}
            </p>
          </div>
          <NTag size="small" round :bordered="false" type="info">
            {{ activeConversation ? '旧对话' : '新对话' }}
          </NTag>
        </div>

        <div ref="messagesContainer" class="grid max-h-520px gap-2 overflow-auto pr-1">
          <NEmpty v-if="!messages.length && !isStreaming" size="small" :description="emptyMessage" />
          <template v-if="messages.length">
            <article
              v-for="message in messages"
              :key="message.id"
              class="rounded-2 bg-surface px-3 py-2 shadow-[inset_0_0_0_1px_#E6EAF2]"
            >
              <div class="mb-1 flex items-center justify-between gap-2">
                <NTag size="small" round :bordered="false" :type="message.role === 'assistant' ? 'success' : 'info'">
                  {{ roleLabel(message.role) }}
                </NTag>
                <span class="text-sub text-11px">{{ new Date(message.created_at).toLocaleString() }}</span>
              </div>
              <div
                v-if="message.role === 'assistant'"
                class="markdown-body text-14px leading-[1.7]"
                v-html="renderMarkdown(message.content)"
              />
              <p v-else class="m-0 whitespace-pre-wrap text-ink text-14px leading-[1.7]">{{ message.content }}</p>
              <KnowledgeCitationList
                v-if="message.role === 'assistant' && message.citations?.length"
                class="mt-3"
                :citations="message.citations"
              />
            </article>
          </template>

          <!-- Streaming answer -->
          <article
            v-if="isStreaming"
            class="rounded-2 border border-primary/30 bg-surface px-3 py-2"
          >
            <div class="mb-1 flex items-center justify-between gap-2">
              <NTag size="small" round :bordered="false" type="success">
                回答 <span class="ml-1 inline-block h-2 w-2 animate-pulse rounded-full bg-green-500" />
              </NTag>
              <span class="text-sub text-11px">正在生成...</span>
            </div>
            <div
              class="markdown-body text-14px leading-[1.7]"
              v-html="renderMarkdown(streamingAnswer || '思考中...')"
            />
            <KnowledgeCitationList
              v-if="streamingCitations?.length"
              class="mt-3"
              :citations="streamingCitations.map(c => ({
                file_id: c.file_id,
                document_id: c.document_id,
                chunk_id: c.chunk_id || '',
                title: c.title,
                page_no: c.page_no ?? 1,
                paragraph_no: c.paragraph_no ?? 1,
                snippet: c.snippet,
              }))"
            />
          </article>
        </div>

        <div class="grid gap-2">
          <NInput
            v-model:value="question"
            data-testid="rag-question-input"
            type="textarea"
            placeholder="输入问题，选择旧对话时会继续上下文；新对话会自动创建"
            :autosize="{ minRows: 3, maxRows: 5 }"
            :disabled="!activeKbId || asking || loading || isStreaming"
            @keydown.enter.exact.prevent="submitQuestion"
          />
          <div class="flex items-center justify-between gap-3">
            <p class="m-0 text-sub text-12px">
              {{ latestAssistantMessage ? '当前对话上下文会继续保留' : '首次提问会创建新会话' }}
            </p>
            <NButton
              data-testid="submit-rag-question"
              type="primary"
              :disabled="!activeKbId || !question.trim() || isStreaming"
              :loading="asking || isStreaming"
              @click="submitQuestion"
            >
              <template #icon><NIcon aria-hidden="true"><Send /></NIcon></template>
              提问
            </NButton>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.markdown-body :deep(.citation-badge) {
  display: inline-flex;
  align-items: center;
  margin: 0 2px;
  border-radius: 999px;
  background: #eaf1ff;
  padding: 1px 6px;
  color: #2454d6;
  font-size: 12px;
  font-weight: 700;
  line-height: 1.5;
  text-decoration: none;
}

.markdown-body :deep(.citation-badge:hover) {
  background: #dbe8ff;
  text-decoration: underline;
}
</style>
