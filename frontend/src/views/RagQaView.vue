<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { storeToRefs } from 'pinia'
import { Database, FileText, Send, Sparkles } from '@lucide/vue'

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
</script>

<template>
  <component :is="layout" :api-state-label="apiStateLabel" :api-state-type="apiStateType" :nav-items="navItems" :unread-notifications="summary.unread_notifications" page-title="RAG 知识问答">
    <div class="mb-4">
      <p class="m-0 text-sub text-13px">知识库检索增强问答</p>
      <h2 class="m-0 mt-1 text-ink text-30px font-800 leading-[1.2]">RAG 知识问答</h2>
      <p class="m-0 mt-1 text-sub text-15px">选择知识库，输入问题，获取基于文档内容的带引用回答。</p>
    </div>
    <div class="grid gap-4">
      <div class="flex flex-wrap items-center gap-3">
        <NSelect v-model:value="selectedKbId" :options="kbOptions" :placeholder="knowledgeBases.length ? '选择知识库' : '暂无知识库'" style="width:240px" />
        <NButton size="small" secondary @click="showCreateKb = true">
          <template #icon><NIcon :size="16"><Database /></NIcon></template>
          新建知识库
        </NButton>
      </div>

      <NCard size="small">
        <div class="flex items-start gap-3">
          <NInput v-model:value="question" type="textarea" placeholder="输入问题，系统将从知识库检索相关内容并生成回答..." :autosize="{ minRows: 2, maxRows: 4 }" class="flex-1" @keydown.enter.exact.prevent="submitQuestion" />
          <NButton type="primary" :loading="askingQuestion" @click="submitQuestion">
            <template #icon><NIcon :size="18"><Send /></NIcon></template>
            提问
          </NButton>
        </div>
      </NCard>

      <NCard v-if="answerText" size="small" title="回答">
        <p class="m-0 whitespace-pre-wrap text-15px leading-[1.7]">{{ answerText }}</p>
      </NCard>

      <NCard v-if="citations.length" size="small" title="引用来源">
        <div class="grid gap-2">
          <div v-for="(c, i) in citations" :key="i" class="flex items-start gap-2 rounded-1 border border-line bg-muted p-3">
            <NIcon :size="16" class="mt-0.5 text-primary"><FileText /></NIcon>
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
          <div v-for="f in indexedFiles" :key="f.id" class="flex items-center justify-between rounded-1 border border-line bg-muted p-2">
            <span class="text-14px">{{ f.name }}</span>
            <NButton size="tiny" secondary @click="handleIndexDocument(f.id)">
              <template #icon><NIcon :size="14"><Sparkles /></NIcon></template>
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
            <NButton type="primary" @click="workspace.createKnowledgeBase({ name: newKbName || '新知识库', description: newKbDesc }); showCreateKb = false">创建</NButton>
          </NSpace>
        </NCard>
      </NModal>
  </component>
</template>
