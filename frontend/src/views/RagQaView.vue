<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { ArrowLeft, Database, FileText, MessageSquareText, Search, Send, Sparkles } from '@lucide/vue'

import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const { apiState, files, narrative, summary } = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'rag')
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

const question = ref('总结所有用到显微镜的实验步骤')
const lastQuestion = ref(question.value)
const answerText = ref('')

const citationCards = computed(() => narrative.value.citations)
const sourceFiles = computed(() => {
  const citationFileIds = new Set(citationCards.value.map((citation) => citation.file_id))
  return files.value.filter((file) => citationFileIds.has(file.id))
})

onMounted(() => {
  void workspace.loadWorkspace().then(() => {
    answerText.value = narrative.value.answer
  })
})

function submitQuestion() {
  const trimmedQuestion = question.value.trim()
  if (!trimmedQuestion) return

  lastQuestion.value = trimmedQuestion
  answerText.value = narrative.value.answer
}
</script>

<template>
  <component
    :is="workspaceLayout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
  >
    <section class="rag-page">
      <div class="rag-heading">
        <div>
          <RouterLink class="btn-secondary no-underline" to="/">
            <NIcon aria-hidden="true" class="mr-1.5"><ArrowLeft /></NIcon>
            返回主页
          </RouterLink>
          <p class="eyebrow">知识库检索增强问答</p>
          <h2>RAG 知识问答</h2>
          <span>围绕当前工作台文件进行提问，回答区展示可追溯引用和命中文档。</span>
        </div>
        <NTag type="info" round>
          <template #icon><NIcon><Database /></NIcon></template>
          {{ citationCards.length }} 条引用
        </NTag>
      </div>

      <div class="rag-shell">
        <main class="chat-panel">
          <NCard :bordered="false" class="rag-card ask-card">
            <template #header>
              <div class="card-title"><NIcon><MessageSquareText /></NIcon>提问</div>
            </template>
            <NInput
              v-model:value="question"
              type="textarea"
              :autosize="{ minRows: 3, maxRows: 6 }"
              placeholder="输入你想问知识库的问题"
              @keydown.ctrl.enter.prevent="submitQuestion"
            />
            <div class="ask-actions">
              <NButton secondary>
                <template #icon><NIcon><Search /></NIcon></template>
                搜索上下文
              </NButton>
              <NButton type="primary" @click="submitQuestion">
                <template #icon><NIcon><Send /></NIcon></template>
                发送问题
              </NButton>
            </div>
          </NCard>

          <NCard :bordered="false" class="rag-card answer-card">
            <template #header>
              <div class="card-title"><NIcon><Sparkles /></NIcon>回答</div>
            </template>
            <div class="question-bubble">{{ lastQuestion }}</div>
            <p class="answer-text">{{ answerText || narrative.answer }}</p>
          </NCard>

          <NCard :bordered="false" class="rag-card">
            <template #header>
              <div class="card-title"><NIcon><FileText /></NIcon>引用来源</div>
            </template>
            <NList bordered>
              <NListItem v-for="citation in citationCards" :key="citation.chunk_id">
                <NThing :title="citation.title">
                  <template #description>
                    第 {{ citation.page_no ?? '-' }} 页 · 第 {{ citation.paragraph_no ?? '-' }} 段
                  </template>
                  <p class="citation-text">{{ citation.snippet }}</p>
                </NThing>
              </NListItem>
            </NList>
          </NCard>
        </main>

        <aside class="context-panel">
          <NCard :bordered="false" class="rag-card">
            <template #header>
              <div class="card-title"><NIcon><Database /></NIcon>命中文档</div>
            </template>
            <div class="source-list">
              <div v-for="file in sourceFiles" :key="file.id" class="source-item">
                <strong>{{ file.name }}</strong>
                <span>{{ file.permission_scope }} · {{ file.parse_status }}</span>
                <NSpace size="small">
                  <NTag v-for="tag in file.tags" :key="tag" size="small" round>{{ tag }}</NTag>
                </NSpace>
              </div>
              <NEmpty v-if="sourceFiles.length === 0" description="暂无命中文档" />
            </div>
          </NCard>

          <NCard :bordered="false" class="rag-card">
            <template #header>检索策略</template>
            <NDescriptions :column="1" bordered size="small">
              <NDescriptionsItem label="范围">当前用户可访问文件</NDescriptionsItem>
              <NDescriptionsItem label="返回">答案、引用、页码与段落</NDescriptionsItem>
              <NDescriptionsItem label="状态">{{ apiStateLabel }}</NDescriptionsItem>
            </NDescriptions>
          </NCard>
        </aside>
      </div>
    </section>
  </component>
</template>

<style scoped>
.rag-page { display: grid; gap: 14px; }
.rag-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.rag-heading .eyebrow { margin: 14px 0 4px; color: #64748b; font-size: 13px; }
.rag-heading h2 { margin: 0; color: #172033; font-size: 30px; font-weight: 800; line-height: 1.2; }
.rag-heading span { display: block; margin-top: 6px; color: #64748b; font-size: 14px; }
.rag-shell { display: grid; grid-template-columns: minmax(0, 1fr) 340px; gap: 14px; align-items: start; }
.chat-panel, .context-panel { display: grid; gap: 12px; min-width: 0; }
.rag-card { overflow: hidden; border: 1px solid #e8eef6; border-radius: 8px; box-shadow: 0 8px 22px rgba(15, 23, 42, 0.045); }
.card-title { display: inline-flex; align-items: center; gap: 8px; color: #172033; font-weight: 800; }
.ask-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 12px; }
.question-bubble { display: inline-block; max-width: 76%; margin-bottom: 14px; padding: 10px 12px; color: #1d4ed8; background: #eff6ff; border: 1px solid #dbeafe; border-radius: 8px; font-weight: 700; }
.answer-text { margin: 0; color: #172033; font-size: 15px; line-height: 1.75; }
.citation-text { margin: 0; color: #334155; font-size: 13px; line-height: 1.6; }
.source-list { display: grid; gap: 10px; }
.source-item { display: grid; gap: 8px; padding: 12px; background: #f8fafc; border: 1px solid #e8eef6; border-radius: 8px; }
.source-item strong { color: #172033; font-size: 14px; }
.source-item span { color: #64748b; font-size: 12px; }
@media (max-width: 980px) { .rag-heading { align-items: flex-start; flex-direction: column; } .rag-shell { grid-template-columns: 1fr; } .question-bubble { max-width: 100%; } }
</style>
