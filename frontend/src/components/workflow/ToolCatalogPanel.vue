<script setup lang="ts">
import { computed } from 'vue'
import { Wrench } from '@lucide/vue'

import type { ToolDefinition } from '@/client/workspace'

const props = withDefaults(defineProps<{
  tools?: ToolDefinition[]
}>(), {
  tools: () => [],
})

const groupedTools = computed(() => {
  const groups = new Map<string, ToolDefinition[]>()
  for (const tool of props.tools) {
    const key = tool.category || 'general'
    groups.set(key, [...(groups.get(key) ?? []), tool])
  }
  return Array.from(groups.entries()).map(([category, items]) => ({ category, items }))
})

function requiredParams(tool: ToolDefinition) {
  const required = tool.input_schema.required
  return Array.isArray(required) ? required.map(String) : []
}
</script>

<template>
  <section class="grid gap-3" aria-label="工具目录">
    <div class="flex items-center justify-between gap-3">
      <div class="flex min-w-0 items-center gap-2">
        <NIcon aria-hidden="true"><Wrench /></NIcon>
        <h2 class="m-0 text-ink text-16px font-750">工具目录</h2>
      </div>
      <NTag size="small" round :bordered="false">{{ tools.length }} 个</NTag>
    </div>
    <NEmpty v-if="!tools.length" size="small" description="暂无可用工具" />
    <div v-else class="grid gap-3">
      <section v-for="group in groupedTools" :key="group.category" class="grid gap-2">
        <h3 class="m-0 text-sub text-12px font-700 uppercase">{{ group.category }}</h3>
        <article v-for="tool in group.items" :key="tool.id" class="border border-line rounded-2 bg-surface px-3 py-2">
          <div class="flex items-start justify-between gap-3">
            <div class="min-w-0">
              <p class="m-0 truncate text-ink text-13px font-700">{{ tool.name }}</p>
              <p class="m-0 mt-1 text-sub text-12px leading-[1.65]">{{ tool.description }}</p>
            </div>
            <NTag size="small" round :bordered="false" :type="tool.enabled ? 'success' : 'default'">
              {{ tool.enabled ? '启用' : '停用' }}
            </NTag>
          </div>
          <div class="mt-2 flex flex-wrap gap-1">
            <NTag v-for="param in requiredParams(tool)" :key="param" size="small" round :bordered="false">
              {{ param }}
            </NTag>
          </div>
        </article>
      </section>
    </div>
  </section>
</template>
