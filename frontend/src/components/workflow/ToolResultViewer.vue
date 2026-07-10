<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  finalAnswer?: string
  resultView?: Record<string, unknown> | null
}>(), {
  finalAnswer: '',
  resultView: null,
})

const rows = computed(() => {
  const value = props.resultView?.rows
  return Array.isArray(value) ? value.filter(isRecord) : []
})
const columns = computed(() => {
  const explicitColumns = props.resultView?.columns
  if (Array.isArray(explicitColumns)) return explicitColumns.map(String)
  return Object.keys(rows.value[0] ?? {})
})
const numericEntries = computed(() =>
  Object.entries(props.resultView ?? {}).filter(([, value]) => typeof value === 'number') as Array<[string, number]>,
)
const textResult = computed(() => {
  const text = props.resultView?.text
  return typeof text === 'string' && text.trim() ? text : props.finalAnswer
})

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}
</script>

<template>
  <section class="grid gap-3" aria-label="工具执行结果">
    <div class="flex items-center justify-between gap-3">
      <h2 class="m-0 text-ink text-16px font-750">结果</h2>
      <NTag v-if="resultView?.kind" size="small" round :bordered="false">{{ resultView.kind }}</NTag>
    </div>

    <NEmpty v-if="!textResult && !rows.length && !numericEntries.length" size="small" description="暂无结果" />

    <p v-if="textResult" class="m-0 whitespace-pre-wrap text-ink text-14px leading-[1.7]">{{ textResult }}</p>

    <div v-if="rows.length" class="overflow-auto">
      <table class="w-full border-collapse text-left text-13px">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column" class="border-b border-line px-2 py-1 text-sub">
              {{ column }}
            </th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, rowIndex) in rows" :key="rowIndex">
            <td v-for="column in columns" :key="column" class="border-b border-line px-2 py-1">
              {{ row[column] }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-if="numericEntries.length" class="grid grid-cols-3 gap-2 max-md:grid-cols-1">
      <NStatistic
        v-for="[key, value] in numericEntries"
        :key="key"
        :label="key"
        :value="value"
      />
    </div>
  </section>
</template>
