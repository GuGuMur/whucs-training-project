<script setup lang="ts">
import { computed, nextTick, onMounted, shallowRef, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useMessage } from 'naive-ui'
import type { Connection } from '@vue-flow/core'
import { onBeforeRouteLeave } from 'vue-router'

import AgentExecutionTimeline from '@/components/workflow/AgentExecutionTimeline.vue'
import AgentTaskCreateModal from '@/components/workflow/AgentTaskCreateModal.vue'
import AgentTaskDetailPanel from '@/components/workflow/AgentTaskDetailPanel.vue'
import AgentTaskList from '@/components/workflow/AgentTaskList.vue'
import ToolCatalogPanel from '@/components/workflow/ToolCatalogPanel.vue'
import ToolResultViewer from '@/components/workflow/ToolResultViewer.vue'
import WorkflowCanvas from '@/components/workflow/WorkflowCanvas.vue'
import WorkflowDebugPanel from '@/components/workflow/WorkflowDebugPanel.vue'
import WorkflowHistoryPanel from '@/components/workflow/WorkflowHistoryPanel.vue'
import WorkflowNodeInspector from '@/components/workflow/WorkflowNodeInspector.vue'
import WorkflowRunPanel from '@/components/workflow/WorkflowRunPanel.vue'
import WorkflowToolbar from '@/components/workflow/WorkflowToolbar.vue'
import { useWorkflowDesigner } from '@/composables/useWorkflowDesigner'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useAgentStore } from '@/stores/agent'
import { useWorkflowStore } from '@/stores/workflow'
import { useWorkspaceStore } from '@/stores/workspace'
import type { ToolDefinition } from '@/client/workspace'

const message = useMessage()
const workspace = useWorkspaceStore()
const workflowStore = useWorkflowStore()
const agent = useAgentStore()
const designer = useWorkflowDesigner()

const { apiState, files, knowledgeBases, summary } = storeToRefs(workspace)
const {
  activeWorkflowExecution,
  activeWorkflowValidation,
  debugSession,
  debugSteps,
  workflowOperationLoading,
  workflowExecutions,
  workflowVersions,
  workflows,
} = storeToRefs(workflowStore)
const {
  activeTask,
  executionSteps,
  finalAnswer,
  loading: agentLoading,
  isStreaming: agentStreaming,
  planPreview,
  resultView,
  taskHistory,
  tools: agentTools,
} = storeToRefs(agent)

const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'workflow')
const workspaceLayout = computed(() => isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout)
const activeTab = shallowRef<'designer' | 'agent'>('designer')
const showAgentTaskModal = shallowRef(false)
const selectedWorkflowId = shallowRef<string | null>(null)
const runInputValues = shallowRef<Record<string, unknown>>({})
let revertingWorkflowSelection = false

const catalogTools = computed<ToolDefinition[]>(() =>
  agentTools.value.length ? agentTools.value : workspace.tools as ToolDefinition[],
)
const editableWorkflows = computed(() => workflows.value.filter((workflow) => workflow.status !== 'template'))
const templateWorkflows = computed(() => workflows.value.filter((workflow) => workflow.status === 'template'))
const canDeleteSelection = computed(() => Boolean(designer.selectedNodeId.value || designer.selectedEdgeId.value))
const workflowInputOptions = computed(() => designer.nodes.value
  .filter((node) => node.data.kind === 'input')
  .flatMap((node) => Object.keys(node.data.parameters).map((key) => ({ key, label: `${node.data.label} · ${key}` }))))
const upstreamOutputOptions = computed(() => {
  const selectedId = designer.selectedNodeId.value
  if (!selectedId) return []
  const incoming = new Map<string, string[]>()
  for (const edge of designer.edges.value) incoming.set(edge.target, [...(incoming.get(edge.target) ?? []), edge.source])
  const upstream = new Set<string>()
  const visit = (id: string) => {
    for (const source of incoming.get(id) ?? []) {
      if (upstream.has(source)) continue
      upstream.add(source)
      visit(source)
    }
  }
  visit(selectedId)
  return designer.nodes.value.filter((node) => upstream.has(node.id)).map((node) => ({
    label: `${node.data.label} · output`, nodeId: node.id, path: 'output',
  }))
})

watch(selectedWorkflowId, async (workflowId, previousWorkflowId) => {
  if (revertingWorkflowSelection) {
    revertingWorkflowSelection = false
    return
  }
  if (!workflowId) return
  if (designer.isDirty.value && !window.confirm('当前流程有未保存修改，确定放弃并切换吗？')) {
    revertingWorkflowSelection = true
    selectedWorkflowId.value = previousWorkflowId
    return
  }
  try {
    const workflow = await workflowStore.loadWorkflow(workflowId)
    designer.hydrate(workflow)
    await nextTick()
  } catch {
    message.error('流程加载失败')
  }
})

onMounted(async () => {
  await Promise.allSettled([
    workspace.loadWorkspace(),
    workflowStore.listWorkflows(),
    agent.loadTools(),
    agent.loadTaskHistory(),
  ])
  const first = editableWorkflows.value[0]
  if (first) selectedWorkflowId.value = first.id
})

function createFlow() {
  if (designer.isDirty.value && !window.confirm('当前流程有未保存修改，确定放弃并新建吗？')) return
  selectedWorkflowId.value = null
  designer.reset()
}

async function loadTemplate(workflowId: string) {
  if (designer.isDirty.value && !window.confirm('当前流程有未保存修改，确定放弃并加载模板吗？')) return
  try {
    const workflow = await workflowStore.loadWorkflow(workflowId)
    designer.hydrate({ ...workflow, id: '', name: `${workflow.name} 副本`, status: 'draft' })
    designer.workflowId.value = null
    selectedWorkflowId.value = null
    message.success('模板已载入为新草稿')
  } catch {
    message.error('模板加载失败')
  }
}

onBeforeRouteLeave(() => {
  if (!designer.isDirty.value) return true
  return window.confirm('当前流程有未保存修改，确定离开吗？')
})

async function saveFlow() {
  try {
    const payload = designer.payload()
    const saved = designer.workflowId.value
      ? await workflowStore.updateWorkflow(designer.workflowId.value, {
          ...payload,
          expectedRevision: designer.revision.value,
        })
      : await workflowStore.createWorkflow(payload)
    designer.markSaved(saved)
    selectedWorkflowId.value = saved.id
    message.success('流程已保存')
    return saved
  } catch {
    message.error('流程保存失败')
    return null
  }
}

async function validateFlow() {
  const saved = designer.isDirty.value || !designer.workflowId.value ? await saveFlow() : null
  const workflowId = saved?.id ?? designer.workflowId.value
  if (!workflowId) return null
  try {
    const validation = await workflowStore.validateWorkflow(workflowId)
    if (validation.valid) message.success('服务端校验通过')
    else message.warning(`发现 ${validation.issues.length} 个问题`)
    return validation
  } catch {
    message.error('流程校验失败')
    return null
  }
}

async function publishFlow() {
  const validation = await validateFlow()
  if (!validation?.valid || !designer.workflowId.value) return
  try {
    const published = await workflowStore.publishWorkflow(designer.workflowId.value)
    designer.markSaved(published)
    message.success(`已发布 ${published.version}`)
  } catch {
    message.error('发布失败，请先修复校验问题')
  }
}

async function executeFlow() {
  if (designer.isDirty.value) {
    message.warning('请先保存并发布当前修改')
    return
  }
  if (!designer.workflowId.value) return
  try {
    const inputs = { ...collectDefaultInputs(), ...runInputValues.value }
    const execution = await workflowStore.executeWorkflow(designer.workflowId.value, { inputs })
    const statuses = new Map(execution.node_executions.map((item) => [item.node_id, item.status]))
    designer.nodes.value = designer.nodes.value.map((node) => ({
      ...node,
      data: {
        ...node.data,
        status: statuses.get(node.id) === 'failed'
          ? 'error'
          : statuses.get(node.id) === 'skipped'
            ? 'skipped'
            : statuses.has(node.id) ? 'success' : 'idle',
      },
    }))
    message.success('流程执行完成')
  } catch {
    message.error('流程执行失败')
  }
}

async function startDebug() {
  if (designer.isDirty.value || !designer.workflowId.value) {
    message.warning('请先保存并发布流程')
    return
  }
  try {
    await workflowStore.startDebug(designer.workflowId.value, { inputs: runInputValues.value })
    message.success('调试会话已启动')
  } catch {
    message.error('调试启动失败，请确认流程已发布')
  }
}

async function stepDebug() {
  if (!designer.workflowId.value) return
  try {
    const step = await workflowStore.stepDebug(designer.workflowId.value)
    designer.nodes.value = designer.nodes.value.map((node) => node.id === step.node_id
      ? { ...node, data: { ...node.data, status: step.status === 'success' ? 'success' : step.status === 'skipped' ? 'skipped' : 'error' } }
      : node)
  } catch {
    message.error('单步调试失败')
  }
}

async function cancelDebug() {
  if (!designer.workflowId.value) return
  try {
    await workflowStore.cancelDebug(designer.workflowId.value)
    message.success('调试会话已结束')
  } catch {
    message.error('结束调试失败')
  }
}

async function restoreVersion(versionId: string) {
  if (!designer.workflowId.value) return
  if (designer.isDirty.value && !window.confirm('当前修改尚未保存，确定用历史版本覆盖吗？')) return
  try {
    const workflow = await workflowStore.restoreVersion(designer.workflowId.value, versionId)
    designer.hydrate(workflow)
    message.success('历史版本已恢复为草稿')
  } catch {
    message.error('版本恢复失败')
  }
}

function collectDefaultInputs() {
  const inputs: Record<string, unknown> = {}
  for (const node of designer.nodes.value) {
    if (node.data.kind !== 'input') continue
    for (const [key, binding] of Object.entries(node.data.parameters)) {
      if (binding && typeof binding === 'object' && 'defaultValue' in binding) {
        inputs[key] = (binding as { defaultValue: unknown }).defaultValue
      }
    }
  }
  return inputs
}

function connectNodes(connection: Connection) {
  if (!designer.connect(connection)) message.warning('该连线无效或已经存在')
}

function selectNode(nodeId: string | null) {
  designer.selectedNodeId.value = nodeId
  if (nodeId) designer.selectedEdgeId.value = null
}

function selectEdge(edgeId: string | null) {
  designer.selectedEdgeId.value = edgeId
  if (edgeId) designer.selectedNodeId.value = null
}

function openAgentTaskModal() {
  agent.clearPlanPreview()
  showAgentTaskModal.value = true
}

async function submitAgentTask(payload: { task: string; kbId?: string | null; contextFileIds?: string[] }) {
  await agent.createTask(payload).catch(() => message.error('智能体任务执行失败'))
}
</script>

<template>
  <component
    :is="workspaceLayout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
    page-title="工具流编排"
  >
    <NTabs v-model:value="activeTab" type="segment" animated>
      <NTabPane name="designer" tab="可视化编排">
        <section class="designer-page">
          <WorkflowToolbar
            v-model:name="designer.name.value"
            v-model:trigger="designer.trigger.value"
            :can-delete="canDeleteSelection"
            :can-redo="designer.canRedo.value"
            :can-undo="designer.canUndo.value"
            :dirty="designer.isDirty.value"
            :loading="workflowOperationLoading"
            @create="createFlow"
            @delete-selection="designer.removeSelection"
            @debug="startDebug"
            @execute="executeFlow"
            @publish="publishFlow"
            @redo="designer.redo"
            @save="saveFlow"
            @validate="validateFlow"
            @undo="designer.undo"
          />

          <div class="workflow-picker">
            <NSelect
              v-model:value="selectedWorkflowId"
              clearable
              filterable
              placeholder="打开已有流程"
              :options="editableWorkflows.map((item) => ({ label: `${item.name} · ${item.status}`, value: item.id }))"
            />
            <NDropdown
              trigger="click"
              :options="templateWorkflows.map((item) => ({ label: item.name, key: item.id }))"
              @select="loadTemplate"
            >
              <NButton secondary>从模板创建</NButton>
            </NDropdown>
            <NAlert v-if="activeWorkflowValidation && !activeWorkflowValidation.valid" type="warning" :bordered="false">
              {{ activeWorkflowValidation.issues.map((item) => item.message).join('；') }}
            </NAlert>
          </div>

          <div class="designer-grid">
            <WorkflowCanvas
              v-model:nodes="designer.nodes.value"
              v-model:edges="designer.edges.value"
              :tools="catalogTools"
              @add-input="designer.addInputNode"
              @add-output="designer.addOutputNode"
              @add-tool="designer.addToolNode"
              @add-advanced="designer.addAdvancedNode"
              @connect="connectNodes"
              @checkpoint="designer.checkpoint"
              @delete-selection="designer.removeSelection"
              @select-edge="selectEdge"
              @select-node="selectNode"
            />
            <WorkflowNodeInspector
              :node="designer.selectedNode.value"
              :tools="catalogTools"
              :available-inputs="workflowInputOptions"
              :available-node-outputs="upstreamOutputOptions"
              @update="designer.updateSelectedNode"
            />
          </div>

          <NCard v-if="activeWorkflowExecution" size="small" title="最近执行">
            <NText>{{ activeWorkflowExecution.id }} · {{ activeWorkflowExecution.status }}</NText>
          </NCard>
          <WorkflowRunPanel
            v-model:values="runInputValues"
            :execution="activeWorkflowExecution"
            :inputs="workflowInputOptions"
            :loading="workflowOperationLoading"
            @run="executeFlow"
          />
          <WorkflowDebugPanel
            :loading="workflowOperationLoading"
            :session="debugSession"
            :steps="debugSteps"
            @start="startDebug"
            @step="stepDebug"
            @cancel="cancelDebug"
          />
          <WorkflowHistoryPanel :executions="workflowExecutions" :versions="workflowVersions" @restore="restoreVersion" />
        </section>
      </NTabPane>

      <NTabPane name="agent" tab="智能体任务">
        <section class="agent-page">
          <div class="agent-page__heading">
            <div><h1>智能体任务</h1><p>创建、查看和管理自然语言工具流任务</p></div>
            <NButton type="primary" @click="openAgentTaskModal">创建任务</NButton>
          </div>
          <div class="agent-page__grid">
            <AgentTaskList
              :active-task-id="activeTask?.id"
              :loading="agentLoading || agentStreaming"
              :tasks="taskHistory"
              @delete-task="agent.deleteTask"
              @select-task="agent.loadTask"
            />
            <section class="agent-page__results">
              <AgentExecutionTimeline v-if="executionSteps.length" :steps="executionSteps" />
              <NEmpty v-else size="small" description="提交任务后展示执行轨迹" />
              <ToolResultViewer :final-answer="finalAnswer" :result-view="resultView" />
            </section>
            <aside class="agent-page__side">
              <AgentTaskDetailPanel :active-task="activeTask" :loading="agentLoading" @cancel="agent.cancelTask" @continue="agent.continueTask(activeTask!.id, $event)" />
              <ToolCatalogPanel :tools="catalogTools" />
            </aside>
          </div>
        </section>
      </NTabPane>
    </NTabs>

    <AgentTaskCreateModal
      v-model:show="showAgentTaskModal"
      :files="files"
      :knowledge-bases="knowledgeBases"
      :loading="agentLoading || agentStreaming"
      :plan-preview="planPreview"
      @preview="agent.previewTaskPlan"
      @stream="agent.createTaskStream"
      @submit="submitAgentTask"
    />
  </component>
</template>

<style scoped>
.designer-page, .agent-page { display: grid; gap: 12px; padding-top: 12px; }
.workflow-picker { display: grid; grid-template-columns: minmax(240px, 420px) auto minmax(0, 1fr); gap: 8px; align-items: center; }
.designer-grid { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 12px; min-width: 0; min-height: 0; align-items: start; }
.agent-page__heading { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
.agent-page__heading h1 { margin: 0; color: #172033; font-size: 20px; }
.agent-page__heading p { margin: 3px 0 0; color: #64748b; font-size: 13px; }
.agent-page__grid { display: grid; grid-template-columns: 280px minmax(0, 1fr) 340px; gap: 12px; align-items: start; }
.agent-page__results, .agent-page__side { display: grid; gap: 12px; min-width: 0; }
@media (max-width: 1100px) {
  .designer-grid, .agent-page__grid { grid-template-columns: 1fr; }
  .workflow-picker { grid-template-columns: 1fr; }
}
</style>
