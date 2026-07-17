<script setup lang="ts">
import { computed } from 'vue'
import { Handle, Position, type NodeProps } from '@vue-flow/core'
import { Box, FileInput, GitBranch, IterationCcw, Merge, Play, Shuffle, Wrench } from '@lucide/vue'

import type { WorkflowDesignerNodeData } from './workflowDesignerTypes'

const props = defineProps<NodeProps<WorkflowDesignerNodeData>>()

const icon = computed(() => ({
  input: FileInput,
  trigger: Play,
  tool: Wrench,
  condition: GitBranch,
  transform: Shuffle,
  loop: IterationCcw,
  aggregate: Merge,
  output: Box,
}[props.data.kind]))

const acceptsInput = computed(() => !['input', 'trigger'].includes(props.data.kind))
const emitsOutput = computed(() => props.data.kind !== 'output')
</script>

<template>
  <article class="graph-node" :class="[`graph-node--${data.kind}`, `is-${data.status}`]">
    <Handle v-if="acceptsInput" id="input" type="target" :position="Position.Left" />
    <div class="graph-node__icon"><component :is="icon" :size="16" /></div>
    <div class="graph-node__copy">
      <strong>{{ data.label }}</strong>
      <small>{{ data.description || data.kind }}</small>
    </div>
    <template v-if="data.kind === 'condition'">
      <Handle id="true" type="source" :position="Position.Right" :style="{ top: '35%' }" />
      <Handle id="false" type="source" :position="Position.Right" :style="{ top: '70%' }" />
    </template>
    <Handle v-else-if="emitsOutput" id="output" type="source" :position="Position.Right" />
  </article>
</template>

<style scoped>
.graph-node {
  display: grid;
  grid-template-columns: 30px minmax(100px, 1fr);
  gap: 9px;
  align-items: center;
  min-width: 170px;
  padding: 10px 12px;
  color: #172033;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 9px;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}
.graph-node--input { border-left: 4px solid #0f766e; }
.graph-node--tool { border-left: 4px solid #246bfe; }
.graph-node--condition { border-left: 4px solid #d97706; }
.graph-node--transform { border-left: 4px solid #7c3aed; }
.graph-node--loop { border-left: 4px solid #0891b2; }
.graph-node--aggregate { border-left: 4px solid #db2777; }
.graph-node--output { border-left: 4px solid #16a34a; }
.graph-node.is-running { box-shadow: 0 0 0 3px rgba(36, 107, 254, 0.16); }
.graph-node.is-error { border-color: #dc2626; }
.graph-node.is-skipped { opacity: 0.55; filter: grayscale(0.7); border-style: dashed; }
.graph-node__icon { display: grid; place-items: center; width: 30px; height: 30px; color: #246bfe; background: #eff6ff; border-radius: 7px; }
.graph-node__copy { display: grid; gap: 2px; min-width: 0; }
.graph-node__copy strong { overflow: hidden; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.graph-node__copy small { overflow: hidden; color: #64748b; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
</style>
