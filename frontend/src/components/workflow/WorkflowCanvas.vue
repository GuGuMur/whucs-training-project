<script setup lang="ts">
import { nextTick, useTemplateRef } from 'vue'
import { VueFlow, useVueFlow, type Connection } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import type { ToolDefinition } from '@/client/workspace'
import WorkflowGraphNode from './WorkflowGraphNode.vue'
import WorkflowNodePalette from './WorkflowNodePalette.vue'
import type {
  AdvancedWorkflowNodeKind,
  WorkflowDesignerEdge,
  WorkflowDesignerNode,
  WorkflowPaletteNodePayload,
} from './workflowDesignerTypes'

defineProps<{ tools: ToolDefinition[] }>()
const emit = defineEmits<{
  addInput: [position?: { x: number; y: number }]
  addOutput: [position?: { x: number; y: number }]
  addTool: [tool: ToolDefinition, position?: { x: number; y: number }]
  addAdvanced: [kind: AdvancedWorkflowNodeKind, position?: { x: number; y: number }]
  connect: [connection: Connection]
  selectEdge: [edgeId: string | null]
  selectNode: [nodeId: string | null]
  checkpoint: []
  deleteSelection: []
}>()

const nodes = defineModel<WorkflowDesignerNode[]>('nodes', { required: true })
const edges = defineModel<WorkflowDesignerEdge[]>('edges', { required: true })
const { fitView, project } = useVueFlow()
const canvasShell = useTemplateRef<HTMLElement>('canvasShell')

function isEditableTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false
  return Boolean(target.closest('input, textarea, select, [contenteditable="true"], [role="textbox"]'))
}

function activateKeyboardScope() {
  canvasShell.value?.focus({ preventScroll: true })
}

function onKeydown(event: KeyboardEvent) {
  if (!['Delete', 'Backspace'].includes(event.key) || isEditableTarget(event.target)) return
  event.preventDefault()
  emit('deleteSelection')
}

function addFromPalette(payload: WorkflowPaletteNodePayload, position?: { x: number; y: number }) {
  if (payload.kind === 'input') emit('addInput', position)
  else if (payload.kind === 'tool') emit('addTool', payload.tool, position)
  else emit('addAdvanced', payload.kind, position)
}

function onDrop(event: DragEvent) {
  const raw = event.dataTransfer?.getData('application/x-whucs-workflow-node')
  if (!raw) return
  try {
    const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect()
    const position = project({ x: event.clientX - bounds.left, y: event.clientY - bounds.top })
    addFromPalette(JSON.parse(raw) as WorkflowPaletteNodePayload, position)
  } catch {
    // Ignore malformed external drag payloads.
  }
}

function fit() {
  nextTick(() => fitView({ padding: 0.2 }))
}

defineExpose({ fit })
</script>

<template>
  <section ref="canvasShell" class="workflow-canvas-shell" tabindex="0" @keydown="onKeydown" @pointerdown="activateKeyboardScope">
    <aside class="workflow-canvas-shell__palette">
      <WorkflowNodePalette :tools="tools" @add-node="addFromPalette" />
      <NButton block secondary @click="emit('addOutput')">添加输出节点</NButton>
    </aside>
    <div class="workflow-canvas" @dragover.prevent @drop="onDrop">
      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :delete-key-code="null"
        fit-view-on-init
        @connect="emit('connect', $event)"
        @edge-click="emit('selectEdge', $event.edge.id)"
        @node-click="emit('selectNode', $event.node.id)"
        @node-drag-start="emit('checkpoint')"
        @pane-click="emit('selectNode', null); emit('selectEdge', null)"
      >
        <template #node-workflow="nodeProps">
          <WorkflowGraphNode v-bind="nodeProps" />
        </template>
        <Background :gap="20" pattern-color="#dbe5f1" />
        <Controls />
        <MiniMap pannable zoomable />
      </VueFlow>
    </div>
  </section>
</template>

<style scoped>
.workflow-canvas-shell { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 12px; width: 100%; height: clamp(380px, calc(100dvh - 300px), 620px); min-height: 0; outline: none; }
.workflow-canvas-shell__palette { min-height: 0; overflow: auto; padding: 12px; background: #f8fafc; border: 1px solid #d8e0ea; border-radius: 8px; }
.workflow-canvas { min-width: 0; min-height: 0; height: 100%; overflow: hidden; background: #fbfdff; border: 1px solid #d8e0ea; border-radius: 8px; }
@media (max-width: 900px) {
  .workflow-canvas-shell { grid-template-columns: 1fr; height: auto; }
  .workflow-canvas-shell__palette { max-height: 260px; }
  .workflow-canvas { height: clamp(360px, 55dvh, 520px); }
}
</style>
