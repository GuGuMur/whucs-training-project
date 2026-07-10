<script setup lang="ts">
import { computed, reactive, shallowRef, watch } from 'vue'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { VueFlow } from '@vue-flow/core'
import type { Edge, Node, XYPosition } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { CheckCircle2, GitBranch, PlayCircle, Rocket, Save, Workflow } from '@lucide/vue'

import type {
  AgentStep,
  ToolDefinition,
  WorkspaceFile,
  WorkspaceKnowledgeBase,
  WorkspaceWorkflow,
  WorkspaceWorkflowCreateInput,
  WorkspaceWorkflowEdge,
  WorkspaceWorkflowExecuteInput,
  WorkspaceWorkflowExecution,
  WorkspaceWorkflowNode,
  WorkspaceWorkflowUpdateInput,
  WorkspaceWorkflowValidation,
} from '@/client/workspace'
import StatusChip from '../files/StatusChip.vue'

const props = defineProps<{
  activeWorkflowId: string | null
  agentSteps: AgentStep[]
  agentTaskRunning: boolean
  files: WorkspaceFile[]
  knowledgeBases: WorkspaceKnowledgeBase[]
  tools: ToolDefinition[]
  workflowExecution: WorkspaceWorkflowExecution | null
  workflowOperationLoading: boolean
  workflowValidation: WorkspaceWorkflowValidation | null
  workflows: WorkspaceWorkflow[]
}>()

const emit = defineEmits<{
  'create-agent-task': [payload: { task: string; kbId?: string | null; contextFileIds?: string[] }]
  'create-workflow': [payload: WorkspaceWorkflowCreateInput]
  'execute-workflow': [workflowId: string, payload: WorkspaceWorkflowExecuteInput]
  'publish-workflow': [workflowId: string]
  'select-workflow': [workflowId: string]
  'update-workflow': [workflowId: string, payload: WorkspaceWorkflowUpdateInput]
  'validate-workflow': [workflowId: string]
}>()

const taskInput = shallowRef('')

function handleCreateAgentTask() {
  const task = taskInput.value.trim()
  if (!task) return
  emit('create-agent-task', {
    task,
    kbId: props.knowledgeBases[0]?.id ?? null,
    contextFileIds: [],
  })
  taskInput.value = ''
}

const createForm = reactive({
  description: '',
  name: '',
})
const workflowDescription = shallowRef('')

const activeWorkflow = computed(
  () =>
    props.workflows.find((workflow) => workflow.id === props.activeWorkflowId) ??
    props.workflows[0] ??
    null,
)
const activeFile = computed(() => props.files[0] ?? null)
const activeKnowledgeBase = computed(() => props.knowledgeBases[0] ?? null)
const enabledTools = computed(() => props.tools.filter((tool) => tool.enabled))
const validationType = computed(() => (props.workflowValidation?.valid ? 'success' : 'warning'))
const validationText = computed(() => {
  if (!props.workflowValidation) {
    return '待校验'
  }
  return props.workflowValidation.valid ? '校验通过' : '需要修正'
})
const flowNodes = computed<Node[]>(() =>
  (activeWorkflow.value?.nodes ?? []).map((node, index) => ({
    id: node.id,
    data: {
      label: node.tool_name ? `${node.name} · ${node.tool_name}` : node.name,
    },
    position: workflowNodePosition(node, index),
    type: 'default',
  })),
)
const flowEdges = computed<Edge[]>(() =>
  (activeWorkflow.value?.edges ?? []).map((edge) => ({
    id: edge.id,
    source: edge.source,
    sourceHandle: edge.source_handle ?? undefined,
    target: edge.target,
    targetHandle: edge.target_handle ?? undefined,
  })),
)

watch(
  activeWorkflow,
  (workflow) => {
    workflowDescription.value = workflow?.description ?? ''
  },
  { immediate: true },
)

function handleCreateWorkflow() {
  const name = createForm.name.trim()
  if (!name) {
    return
  }
  const description = createForm.description.trim()
  emit('create-workflow', {
    description: description || null,
    edges: createDefaultWorkflowEdges(),
    name,
    nodes: createDefaultWorkflowNodes(),
    trigger: 'manual',
  })
  createForm.name = ''
  createForm.description = ''
}

function handleSelectWorkflow(workflowId: string) {
  emit('select-workflow', workflowId)
}

function handleSaveWorkflow(workflow: WorkspaceWorkflow) {
  emit('update-workflow', workflow.id, {
    description: workflowDescription.value.trim() || null,
    edges: workflow.edges ?? [],
    name: workflow.name,
    nodes: workflow.nodes ?? [],
    trigger: workflow.trigger,
  })
}

function handleValidateWorkflow(workflowId: string) {
  emit('validate-workflow', workflowId)
}

function handlePublishWorkflow(workflowId: string) {
  emit('publish-workflow', workflowId)
}

function handleExecuteWorkflow(workflowId: string) {
  if (!activeFile.value) {
    return
  }
  emit('execute-workflow', workflowId, {
    fileId: activeFile.value.id,
    targetKbId: activeKnowledgeBase.value?.id ?? null,
  })
}

function createDefaultWorkflowNodes(): WorkspaceWorkflowNode[] {
  return []
}

function createDefaultWorkflowEdges(): WorkspaceWorkflowEdge[] {
  return []
}

function workflowNodePosition(node: WorkspaceWorkflowNode, index: number): XYPosition {
  return {
    x: node.position?.x ?? 48 + index * 190,
    y: node.position?.y ?? (index % 2 === 0 ? 40 : 150),
  }
}

function timelineType(status: AgentStep['status']) {
  return {
    needs_clarification: 'warning',
    pending: 'default',
    running: 'info',
    success: 'success',
    failed: 'error',
  }[status ?? 'pending'] as 'default' | 'info' | 'success' | 'warning' | 'error'
}
</script>

<template>
  <NCard id="automation" class="min-w-0 overflow-hidden scroll-mt-24 max-md:scroll-mt-32" size="small">
    <template #header>
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0">
          <h2 class="panel-title">智能体与工具流</h2>
          <p class="mt-1 panel-subtitle">可编辑工作流、工具编排和执行轨迹</p>
        </div>
        <NTag
          size="small"
          :type="validationType"
          round
        >
          {{ validationText }}
        </NTag>
        <RouterLink class="btn-primary no-underline" to="/workflow">
          <NIcon aria-hidden="true" class="mr-1.5"><Play /></NIcon>
          打开编排器
        </RouterLink>
      </div>
    </template>

    <div class="grid gap-4">
      <div class="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.35fr)] gap-4 max-lg:grid-cols-1">
        <section class="grid content-start gap-3 min-w-0">
          <div class="grid gap-2">
            <NInput v-model:value="createForm.name" placeholder="流程名称" clearable />
            <NInput
              v-model:value="createForm.description"
              placeholder="流程说明"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 3 }"
            />
            <NButton
              data-testid="submit-create-workflow"
              type="primary"
              :disabled="!createForm.name.trim()"
              :loading="workflowOperationLoading"
              @click="handleCreateWorkflow"
            >
              <template #icon>
                <NIcon aria-hidden="true"><Workflow /></NIcon>
              </template>
              新建流程
            </NButton>
          </div>

          <NList bordered>
            <NListItem v-for="workflow in workflows" :key="workflow.id">
              <div class="grid gap-2 min-w-0">
                <div class="flex items-start justify-between gap-2">
                  <button
                    class="min-w-0 border-0 bg-transparent p-0 text-left text-ink text-14px font-700"
                    :data-testid="`select-workflow-${workflow.id}`"
                    type="button"
                    @click="handleSelectWorkflow(workflow.id)"
                  >
                    {{ workflow.name }}
                  </button>
                  <StatusChip
                    :tone="workflow.status === 'published' ? 'success' : 'warning'"
                    :label="workflow.status === 'published' ? '已发布' : '草稿'"
                  />
                </div>
                <p class="m-0 text-sub text-12px leading-[1.5]">{{ workflow.description }}</p>
                <div class="flex flex-wrap items-center gap-2">
                  <NTag size="small" round>{{ workflow.trigger }}</NTag>
                  <NTag size="small" round>{{ workflow.node_count }} 节点</NTag>
                  <NButton
                    size="tiny"
                    :data-testid="`validate-workflow-${workflow.id}`"
                    :loading="workflowOperationLoading"
                    @click="handleValidateWorkflow(workflow.id)"
                  >
                    <template #icon>
                      <NIcon aria-hidden="true"><CheckCircle2 /></NIcon>
                    </template>
                    校验
                  </NButton>
                  <NButton
                    size="tiny"
                    :data-testid="`publish-workflow-${workflow.id}`"
                    :loading="workflowOperationLoading"
                    @click="handlePublishWorkflow(workflow.id)"
                  >
                    <template #icon>
                      <NIcon aria-hidden="true"><Rocket /></NIcon>
                    </template>
                    发布
                  </NButton>
                  <NButton
                    size="tiny"
                    type="primary"
                    :data-testid="`execute-workflow-${workflow.id}`"
                    :disabled="!activeFile"
                    :loading="workflowOperationLoading"
                    @click="handleExecuteWorkflow(workflow.id)"
                  >
                    <template #icon>
                      <NIcon aria-hidden="true"><PlayCircle /></NIcon>
                    </template>
                    运行
                  </NButton>
                </div>
              </div>
            </NListItem>
          </NList>
        </section>

        <section class="grid content-start gap-3 min-w-0">
          <div class="border border-line rounded-2 bg-canvas h-260px overflow-hidden">
            <VueFlow :nodes="flowNodes" :edges="flowEdges" fit-view-on-init>
              <Background />
              <Controls />
            </VueFlow>
          </div>

          <div v-if="activeWorkflow" class="grid gap-2">
            <div class="flex items-center justify-between gap-2">
              <div class="min-w-0">
                <p class="m-0 text-ink text-14px font-700">{{ activeWorkflow.name }}</p>
                <p class="m-0 text-sub text-12px">版本 {{ activeWorkflow.version }} · {{ activeWorkflow.trigger }}</p>
              </div>
              <NButton
                size="small"
                :data-testid="`save-workflow-${activeWorkflow.id}`"
                :loading="workflowOperationLoading"
                @click="handleSaveWorkflow(activeWorkflow)"
              >
                <template #icon>
                  <NIcon aria-hidden="true"><Save /></NIcon>
                </template>
                保存
              </NButton>
            </div>
            <NInput
              v-model:value="workflowDescription"
              placeholder="流程描述"
              type="textarea"
              :autosize="{ minRows: 2, maxRows: 3 }"
            />
          </div>

          <NAlert
            v-if="workflowValidation"
            :type="workflowValidation.valid ? 'success' : 'warning'"
            :show-icon="false"
          >
            <div class="flex flex-wrap items-center gap-2 text-13px">
              <span>{{ validationText }}</span>
              <span>{{ workflowValidation.node_count }} 节点</span>
              <span>{{ workflowValidation.edge_count }} 连线</span>
            </div>
            <ul v-if="workflowValidation.issues.length" class="m-0 mt-2 pl-4 text-12px leading-[1.5]">
              <li v-for="issue in workflowValidation.issues" :key="`${issue.code}-${issue.node_id ?? issue.edge_id}`">
                {{ issue.message }}
              </li>
            </ul>
          </NAlert>
        </section>
      </div>

      <div class="grid grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] gap-4 max-lg:grid-cols-1">
        <section class="grid content-start gap-2 min-w-0">
          <div class="flex items-center gap-2">
            <NIcon class="text-knowledge" aria-hidden="true"><GitBranch /></NIcon>
            <h3 class="m-0 text-ink text-14px font-700">工具注册中心</h3>
          </div>
          <NSpace aria-label="内置工具" :size="[8, 8]">
            <NTag
              v-for="tool in enabledTools"
              :key="tool.id"
              round
              :color="{ color: '#F1EEFF', textColor: '#5141D8', borderColor: '#DAD4FF' }"
            >
              {{ tool.name }}
            </NTag>
          </NSpace>
          <p v-if="workflowExecution" class="m-0 text-sub text-12px leading-[1.5]">
            最近执行：{{ workflowExecution.id }} · {{ workflowExecution.status }}
          </p>
        </section>

        <section class="grid gap-2 min-w-0">
          <NInput
            v-model:value="taskInput"
            placeholder="描述你想让智能体完成的任务，如：分析本周实验数据并生成报告"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 4 }"
          />
          <NButton
            type="primary"
            :disabled="!taskInput.trim()"
            :loading="agentTaskRunning"
            @click="handleCreateAgentTask"
          >
            提交任务
          </NButton>
        </section>

        <section class="min-w-0">
          <NTimeline>
            <NTimelineItem
              v-for="step in agentSteps"
              :key="`${step.type}-${step.title}-${step.tool_name ?? 'none'}`"
              :type="timelineType(step.status)"
            >
              <template #header>
                <span class="text-ink text-13px font-700">{{ step.title }}</span>
                <NTag
                  v-if="step.tool_name"
                  size="small"
                  round
                  class="ml-2"
                  :color="{ color: '#F1EEFF', textColor: '#5141D8', borderColor: '#DAD4FF' }"
                >
                  {{ step.tool_name }}
                </NTag>
              </template>
              <template #default>
                <p class="m-0 text-sub text-13px leading-[1.5]">{{ step.type }} · {{ step.content }}</p>
              </template>
            </NTimelineItem>
          </NTimeline>
        </section>
      </div>
    </div>
  </NCard>
</template>
