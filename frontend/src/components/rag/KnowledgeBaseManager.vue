<script setup lang="ts">
import { computed, reactive, watch } from 'vue'

import type {
  WorkspaceKnowledgeBase,
  WorkspaceKnowledgeBaseCreateInput,
  WorkspaceKnowledgeBaseUpdateInput,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  knowledgeBase?: WorkspaceKnowledgeBase | null
  loading?: boolean
  mode?: 'create' | 'edit'
}>(), {
  knowledgeBase: null,
  loading: false,
  mode: 'create',
})

const emit = defineEmits<{
  archive: [kbId: string]
  create: [payload: WorkspaceKnowledgeBaseCreateInput]
  delete: [kbId: string]
  update: [kbId: string, payload: WorkspaceKnowledgeBaseUpdateInput]
}>()

const form = reactive({
  category: '',
  description: '',
  freshnessPolicy: 'manual' as NonNullable<WorkspaceKnowledgeBaseCreateInput['freshnessPolicy']>,
  name: '',
  scopeId: '',
  scopeType: 'personal' as NonNullable<WorkspaceKnowledgeBaseCreateInput['scopeType']>,
  tags: [] as string[],
})

const isEditMode = computed(() => props.mode === 'edit' && props.knowledgeBase)
const canSubmit = computed(() => Boolean(form.name.trim()))

watch(
  () => props.knowledgeBase,
  (kb) => {
    form.category = kb?.category ?? ''
    form.description = kb?.description ?? ''
    form.freshnessPolicy = kb?.freshness_policy ?? 'manual'
    form.name = kb?.name ?? ''
    form.scopeId = kb?.scope_id ?? ''
    form.scopeType = kb?.scope_type ?? 'personal'
    form.tags = [...(kb?.tags ?? [])]
  },
  { immediate: true },
)

function submit() {
  if (!canSubmit.value) return
  const payload = {
    category: form.category.trim() || null,
    description: form.description.trim() || null,
    freshnessPolicy: form.freshnessPolicy,
    name: form.name.trim(),
    scopeId: form.scopeType === 'team' ? form.scopeId.trim() || null : null,
    scopeType: form.scopeType,
    tags: form.tags.map((tag) => tag.trim()).filter(Boolean),
  }
  if (isEditMode.value && props.knowledgeBase) {
    emit('update', props.knowledgeBase.id, payload)
    return
  }
  emit('create', payload)
}
</script>

<template>
  <section class="grid gap-3" aria-label="知识库配置">
    <NForm label-placement="top" size="small">
      <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <NFormItem label="名称">
          <NInput v-model:value="form.name" placeholder="知识库名称" />
        </NFormItem>
        <NFormItem label="分类">
          <NInput v-model:value="form.category" placeholder="例如：课程资料" />
        </NFormItem>
      </div>

      <NFormItem label="说明">
        <NInput
          v-model:value="form.description"
          type="textarea"
          placeholder="知识库用途、更新范围或维护说明"
          :autosize="{ minRows: 2, maxRows: 4 }"
        />
      </NFormItem>

      <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
        <NFormItem label="空间">
          <NRadioGroup v-model:value="form.scopeType" button-style="solid">
            <NRadioButton value="personal">个人</NRadioButton>
            <NRadioButton value="team">团队</NRadioButton>
          </NRadioGroup>
        </NFormItem>
        <NFormItem v-if="form.scopeType === 'team'" label="团队 ID">
          <NInput v-model:value="form.scopeId" placeholder="team id" />
        </NFormItem>
        <NFormItem label="更新策略">
          <NRadioGroup v-model:value="form.freshnessPolicy" button-style="solid">
            <NRadioButton value="manual">手动</NRadioButton>
            <NRadioButton value="on_file_update">文件更新时</NRadioButton>
          </NRadioGroup>
        </NFormItem>
      </div>

      <NFormItem label="标签">
        <NDynamicTags v-model:value="form.tags" />
      </NFormItem>
    </NForm>

    <div class="flex flex-wrap justify-end gap-2">
      <NButton
        v-if="isEditMode && knowledgeBase"
        secondary
        :loading="loading"
        @click="emit('archive', knowledgeBase.id)"
      >
        归档
      </NButton>
      <NButton
        v-if="isEditMode && knowledgeBase"
        secondary
        type="error"
        :loading="loading"
        @click="emit('delete', knowledgeBase.id)"
      >
        删除
      </NButton>
      <NButton type="primary" :disabled="!canSubmit" :loading="loading" @click="submit">
        {{ isEditMode ? '保存' : '创建' }}
      </NButton>
    </div>
  </section>
</template>
