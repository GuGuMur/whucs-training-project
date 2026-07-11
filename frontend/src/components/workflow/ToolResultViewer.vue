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
const sections = computed(() => {
  const value = props.resultView?.sections
  return Array.isArray(value) ? value.filter(isRecord) : []
})
const keyResults = computed(() => {
  const value = props.resultView?.key_results
  return Array.isArray(value) ? value.map(String) : []
})
const chartSeries = computed(() => {
  const chart = props.resultView?.chart
  if (!isRecord(chart)) return []
  const series = chart.series
  if (!isRecord(series)) return []
  return Object.entries(series).map(([name, value]) => ({ name, value: isRecord(value) ? value : { value } }))
})
const resultType = computed(() => {
  const type = props.resultView?.type ?? props.resultView?.kind
  return typeof type === 'string' ? type : ''
})
const textResult = computed(() => {
  const content = props.resultView?.content ?? props.resultView?.text
  return typeof content === 'string' && content.trim() ? content : props.finalAnswer
})

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function formatValue(value: unknown) {
  if (isRecord(value)) {
    return Object.entries(value).map(([key, item]) => `${key}: ${item}`).join(' / ')
  }
  return String(value)
}
</script>

<template>
  <section class="grid gap-3" aria-label="工具执行结果">
    <div class="flex items-center justify-between gap-3">
      <h2 class="m-0 text-ink text-16px font-750">结果</h2>
      <NTag v-if="resultType" size="small" round :bordered="false">{{ resultType }}</NTag>
    </div>

    <NEmpty v-if="!textResult && !rows.length && !numericEntries.length && !sections.length && !chartSeries.length" size="small" description="暂无结果" />

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

    <div v-if="keyResults.length" class="grid gap-2">
      <div v-for="item in keyResults" :key="item" class="rounded-1 bg-#F8FAFD px-2 py-1 text-13px text-ink">
        {{ item }}
      </div>
    </div>

    <div v-if="chartSeries.length" class="grid gap-2">
      <div v-for="entry in chartSeries" :key="entry.name" class="grid gap-1">
        <div class="flex justify-between gap-3 text-12px text-sub">
          <span>{{ entry.name }}</span>
          <span>{{ formatValue(entry.value) }}</span>
        </div>
        <div class="h-2 overflow-hidden rounded-1 bg-#E8EEF8">
          <div class="h-full w-1/2 bg-primary" />
        </div>
      </div>
    </div>

    <div v-if="sections.length" class="grid gap-2">
      <article v-for="(section, index) in sections" :key="index" class="rounded-1 border border-line px-3 py-2">
        <div class="text-12px text-sub">{{ section.tool }}</div>
        <p class="m-0 mt-1 whitespace-pre-wrap text-13px text-ink leading-[1.65]">{{ section.observation }}</p>
      </article>
    </div>
  </section>
</template>
