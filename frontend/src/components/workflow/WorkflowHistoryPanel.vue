<script setup lang="ts">
import type { WorkspaceWorkflowExecutionRecord, WorkspaceWorkflowVersion } from '@/client/workspace'

defineProps<{
  executions: WorkspaceWorkflowExecutionRecord[]
  versions: WorkspaceWorkflowVersion[]
}>()
const emit = defineEmits<{ restore: [versionId: string] }>()
</script>

<template>
  <NCard size="small" title="版本与执行历史">
    <NTabs type="line" size="small">
      <NTabPane name="versions" :tab="`发布版本 ${versions.length}`">
        <NEmpty v-if="!versions.length" size="small" description="尚未发布版本" />
        <NList v-else bordered>
          <NListItem v-for="item in versions" :key="item.id">
            <NThing :title="`v${item.version} · ${item.name}`" :description="new Date(item.published_at).toLocaleString()">
              <template #header-extra>
                <NSpace align="center">
                  <NTag size="small">{{ item.nodes?.length ?? 0 }} 节点</NTag>
                  <NButton size="tiny" quaternary @click="emit('restore', item.id)">恢复为草稿</NButton>
                </NSpace>
              </template>
            </NThing>
          </NListItem>
        </NList>
      </NTabPane>
      <NTabPane name="executions" :tab="`执行记录 ${executions.length}`">
        <NEmpty v-if="!executions.length" size="small" description="尚无执行记录" />
        <NList v-else bordered>
          <NListItem v-for="item in executions" :key="item.id">
            <NThing :title="`${item.id} · v${item.workflow_version}`" :description="new Date(item.created_at).toLocaleString()">
              <template #header-extra>
                <NTag :type="item.status === 'completed' ? 'success' : 'error'" size="small">{{ item.status }}</NTag>
              </template>
              <NText depth="3">{{ item.node_executions?.length ?? 0 }} 个节点</NText>
            </NThing>
          </NListItem>
        </NList>
      </NTabPane>
    </NTabs>
  </NCard>
</template>
