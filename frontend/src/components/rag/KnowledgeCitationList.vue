<script setup lang="ts">
import { FileText } from '@lucide/vue'

import type { Citation } from '@/client/workspace'

withDefaults(defineProps<{
  citations?: Citation[]
}>(), {
  citations: () => [],
})
</script>

<template>
  <section class="grid gap-2" aria-label="引用来源">
    <div class="flex items-center justify-between gap-3">
      <h3 class="m-0 text-ink text-15px font-700">引用来源</h3>
      <NTag size="small" round :bordered="false" type="info">{{ citations.length }} 条</NTag>
    </div>
    <NEmpty v-if="!citations.length" size="small" description="暂无引用片段" />
    <div v-else class="grid gap-2">
      <article
        v-for="(citation, index) in citations"
        :id="`citation-${index + 1}`"
        :key="`${citation.document_id}-${citation.chunk_id}-${index}`"
        class="border border-line rounded-2 bg-#F8FAFD px-3 py-2"
      >
        <div class="flex items-start gap-2">
          <NIcon :size="16" class="mt-0.5 shrink-0 text-primary" aria-hidden="true">
            <FileText />
          </NIcon>
          <div class="min-w-0">
            <p class="m-0 truncate text-ink text-13px font-700">{{ citation.title }}</p>
            <p class="m-0 mt-1 text-sub text-12px leading-[1.65]">{{ citation.snippet }}</p>
            <p class="m-0 mt-1 text-sub text-11px">
              第 {{ citation.page_no }} 页 · 段落 {{ citation.paragraph_no }}
            </p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
