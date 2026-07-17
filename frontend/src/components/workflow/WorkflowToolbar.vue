<script setup lang="ts">
import { Bug, CheckCircle2, Play, Plus, Redo2, Save, Send, Trash2, Undo2 } from '@lucide/vue'

defineProps<{
  dirty: boolean
  loading: boolean
  canDelete: boolean
  canRedo: boolean
  canUndo: boolean
}>()

const emit = defineEmits<{
  create: []
  deleteSelection: []
  execute: []
  debug: []
  publish: []
  save: []
  validate: []
  redo: []
  undo: []
}>()

const name = defineModel<string>('name', { required: true })
const trigger = defineModel<string>('trigger', { required: true })

const triggerOptions = [
  { label: '手动触发', value: 'manual' },
  { label: '文件上传后', value: 'file_upload' },
  { label: '定时任务', value: 'schedule' },
  { label: 'WebSocket 事件', value: 'websocket' },
]
</script>

<template>
  <header class="workflow-toolbar">
    <NButton secondary @click="emit('create')"><template #icon><NIcon><Plus /></NIcon></template>新建</NButton>
    <NInput v-model:value="name" class="workflow-toolbar__name" placeholder="流程名称" />
    <NSelect v-model:value="trigger" class="workflow-toolbar__trigger" :options="triggerOptions" />
    <NTag :type="dirty ? 'warning' : 'success'" round>{{ dirty ? '未保存' : '已保存' }}</NTag>
    <span class="workflow-toolbar__spacer" />
    <NButton :disabled="!canUndo" quaternary aria-label="撤销" @click="emit('undo')"><template #icon><NIcon><Undo2 /></NIcon></template></NButton>
    <NButton :disabled="!canRedo" quaternary aria-label="重做" @click="emit('redo')"><template #icon><NIcon><Redo2 /></NIcon></template></NButton>
    <NButton :disabled="!canDelete" quaternary @click="emit('deleteSelection')"><template #icon><NIcon><Trash2 /></NIcon></template>删除</NButton>
    <NButton :loading="loading" @click="emit('save')"><template #icon><NIcon><Save /></NIcon></template>保存</NButton>
    <NButton :loading="loading" @click="emit('validate')"><template #icon><NIcon><CheckCircle2 /></NIcon></template>校验</NButton>
    <NButton :loading="loading" type="primary" secondary @click="emit('publish')"><template #icon><NIcon><Send /></NIcon></template>发布</NButton>
    <NButton :loading="loading" type="primary" @click="emit('execute')"><template #icon><NIcon><Play /></NIcon></template>运行</NButton>
    <NButton :loading="loading" secondary @click="emit('debug')"><template #icon><NIcon><Bug /></NIcon></template>调试</NButton>
  </header>
</template>

<style scoped>
.workflow-toolbar { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; padding: 10px; background: #fff; border: 1px solid #d8e0ea; border-radius: 8px; }
.workflow-toolbar__name { width: min(300px, 100%); }
.workflow-toolbar__trigger { width: 160px; }
.workflow-toolbar__spacer { flex: 1; }
</style>
