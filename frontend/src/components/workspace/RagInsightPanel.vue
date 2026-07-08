<script setup lang="ts">
import { ExternalLink } from '@lucide/vue'
import type { WorkspaceNarrative } from '@/client/workspace'
import StatusChip from './StatusChip.vue'

defineProps<{
  narrative: WorkspaceNarrative
}>()
</script>

<template>
  <NCard id="rag" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" size="small">
    <template #header>
      <div class="flex items-center justify-between gap-3">
        <div>
          <h2 class="panel-title">RAG 知识问答</h2>
          <p class="mt-1 panel-subtitle">基于知识库片段生成带引用的回答</p>
        </div>
        <RouterLink class="btn-secondary no-underline" to="/rag">
          <NIcon aria-hidden="true" class="mr-1.5"><ExternalLink /></NIcon>
          完整问答
        </RouterLink>
      </div>
    </template>

    <NAlert type="info" :bordered="false" class="mb-3 border border-#DAD4FF bg-#F1EEFF text-ink">
      示例问题：总结所有用到显微镜的实验步骤
    </NAlert>
    <p class="m-0 text-ink text-14px leading-[1.65]">{{ narrative.answer }}</p>

    <NDivider class="!my-4" />
    <div class="mb-2 flex items-center justify-between gap-3">
      <h3 class="panel-title">引用来源</h3>
      <StatusChip tone="knowledge" label="引用可追溯" />
    </div>
    <NList bordered>
      <NListItem v-for="citation in narrative.citations" :key="citation.chunk_id">
        <NThing :title="citation.title">
          <template #description>第 {{ citation.page_no }} 页 · 第 {{ citation.paragraph_no }} 段</template>
          <p class="m-0 text-ink text-13px leading-[1.55]">{{ citation.snippet }}</p>
        </NThing>
      </NListItem>
    </NList>
  </NCard>
</template>
