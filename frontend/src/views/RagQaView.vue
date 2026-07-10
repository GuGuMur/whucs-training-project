<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Database, FileText, Send, Sparkles } from '@lucide/vue'

import { renderMarkdown } from '@/composables/useMarkdown'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const {
  activeKnowledgeBaseId, apiState, askingQuestion, indexedFiles,
  knowledgeBases, summary,
} = storeToRefs(workspace)

const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'rag')
const layout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const question = ref('')
const answerText = ref('')
const citations = ref<Array<{ title: string; snippet: string; page_no: number; file_id: string }>>([])
const selectedKbId = ref<string | null>(null)
const showCreateKb = ref(false)
const newKbName = ref('')
const newKbDesc = ref('')

const kbOptions = computed(() => knowledgeBases.value.map((kb) => ({ label: kb.name, value: kb.id })))

onMounted(() => { void workspace.loadWorkspace() })

async function submitQuestion() {
  const q = question.value.trim()
  if (!q) return
  const kbId = selectedKbId.value ?? activeKnowledgeBaseId.value ?? knowledgeBases.value[0]?.id
  if (!kbId) return
  try {
    const result = await workspace.askKnowledgeQuestion({ kbId, question: q, topK: 3 })
    answerText.value = result.answer
    citations.value = (result.citations ?? []).map((c: any) => ({
      title: c.title ?? '', snippet: c.snippet ?? '', page_no: c.page_no ?? 1, file_id: c.file_id ?? '',
    }))
  } catch { answerText.value = '查询失败，请确认知识库中有已索引文档。' }
}

async function handleIndexDocument(fileId: string) {
  const kbId = selectedKbId.value ?? knowledgeBases.value[0]?.id
  if (!kbId) return
  try { await workspace.addKnowledgeDocument(kbId, fileId) } catch { /* ignore */ }
}

function handleCitationClick(event: MouseEvent) {
  const target = event.target as HTMLElement
  const badge = target.closest('.citation-badge') as HTMLElement | null
  if (!badge) return
  const citationId = badge.dataset.citation
  if (!citationId) return
  const el = document.getElementById(`citation-${citationId}`)
  if (!el) return
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  el.classList.add('citation-flash')
  setTimeout(() => el.classList.remove('citation-flash'), 1500)
}
</script>

<template>
  <component :is="layout" :api-state-label="apiStateLabel" :api-state-type="apiStateType" :nav-items="navItems"
    :unread-notifications="summary.unread_notifications" page-title="RAG 知识问答">
    <div class="grid gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <NSelect v-model:value="selectedKbId" :options="kbOptions"
          :placeholder="knowledgeBases.length ? '选择知识库' : '暂无知识库'" style="width:240px" />
        <NButton size="small" secondary @click="showCreateKb = true">
          <template #icon>
            <NIcon :size="16">
              <Database />
            </NIcon>
          </template>
          新建知识库
        </NButton>
      </div>

      <NCard size="small">
        <div class="flex items-start gap-3">
          <NInput v-model:value="question" type="textarea" placeholder="输入问题，系统将从知识库检索相关内容并生成回答..."
            :autosize="{ minRows: 2, maxRows: 4 }" class="flex-1" @keydown.enter.exact.prevent="submitQuestion" />
          <NButton type="primary" :loading="askingQuestion" @click="submitQuestion">
            <template #icon>
              <NIcon :size="18">
                <Send />
              </NIcon>
            </template>
            提问
          </NButton>
        </div>
      </NCard>

      <NCard v-if="answerText" size="small" title="回答">
        <div class="markdown-body text-15px leading-[1.7]" v-html="renderMarkdown(answerText)" @click="handleCitationClick" />
      </NCard>

      <NCard v-if="citations.length" size="small" title="引用来源">
        <div class="grid gap-2">
          <div v-for="(c, i) in citations" :key="i" :id="`citation-${i + 1}`"
            class="citation-item flex items-start gap-2 rounded-1 border border-line bg-muted p-3 transition-colors">
            <NIcon :size="16" class="mt-0.5 text-primary">
              <FileText />
            </NIcon>
            <div>
              <p class="m-0 text-ink text-14px font-650">{{ c.title }}</p>
              <p class="m-0 mt-0.5 text-sub text-13px">{{ c.snippet }}</p>
            </div>
          </div>
        </div>
      </NCard>

      <NCard size="small" title="可索引文件">
        <div v-if="indexedFiles.length === 0" class="text-sub text-14px">暂无已解析文件，请先在文件管理中上传文件。</div>
        <div v-else class="grid gap-2">
          <div v-for="f in indexedFiles" :key="f.id"
            class="flex items-center justify-between rounded-1 border border-line bg-muted p-2">
            <span class="text-14px">{{ f.name }}</span>
            <NButton size="tiny" secondary @click="handleIndexDocument(f.id)">
              <template #icon>
                <NIcon :size="14">
                  <Sparkles />
                </NIcon>
              </template>
              索引
            </NButton>
          </div>
        </div>
      </NCard>
    </div>

    <!-- Create KB Modal -->
    <NModal v-model:show="showCreateKb" title="新建知识库">
      <NCard style="width:400px" title="新建知识库" :bordered="false" size="small">
        <NFormItem label="名称">
          <NInput v-model:value="newKbName" placeholder="知识库名称" />
        </NFormItem>
        <NFormItem label="描述">
          <NInput v-model:value="newKbDesc" placeholder="可选描述" />
        </NFormItem>
        <NSpace justify="end">
          <NButton @click="showCreateKb = false">取消</NButton>
          <NButton type="primary"
            @click="workspace.createKnowledgeBase({ name: newKbName || '新知识库', description: newKbDesc }); showCreateKb = false">
            创建</NButton>
        </NSpace>
      </NCard>
    </NModal>
  </component>
</template>

<style>
.markdown-body { color: #172033; }
.markdown-body h1, .markdown-body h2, .markdown-body h3 { margin: 0.75em 0 0.4em; font-weight: 800; }
.markdown-body h2 { font-size: 1.1em; }
.markdown-body h3 { font-size: 1em; }
.markdown-body p { margin: 0.4em 0; }
.markdown-body ul, .markdown-body ol { margin: 0.3em 0; padding-left: 1.5em; }
.markdown-body li { margin: 0.15em 0; }
.markdown-body code { padding: 0.15em 0.4em; font-size: 0.9em; background: #f1f5f9; border-radius: 4px; }
.markdown-body pre { padding: 0.8em 1em; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; overflow-x: auto; }
.markdown-body pre code { padding: 0; background: none; }
.markdown-body blockquote { margin: 0.5em 0; padding: 0.3em 0.8em; border-left: 3px solid #246BFE; color: #64748b; }
.citation-badge { display: inline-block; padding: 0.1em 0.5em; font-size: 0.82em; font-weight: 650; color: #246BFE; background: rgba(36,107,254,0.08); border-radius: 6px; cursor: pointer; transition: background 0.15s; user-select: none; }
.citation-badge:hover { background: rgba(36,107,254,0.18); }
.citation-item { transition: background 0.3s, box-shadow 0.3s; }
.citation-flash { background: rgba(36,107,254,0.12) !important; box-shadow: 0 0 0 2px rgba(36,107,254,0.3); }
</style>
