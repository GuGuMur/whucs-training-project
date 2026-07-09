<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { GitBranch, Plus, ShieldCheck, Trash2 } from '@lucide/vue'

import type {
  WorkspaceFile,
  WorkspaceFolder,
  WorkspacePermissionRule,
  WorkspacePermissionRuleCreateInput,
  WorkspaceTeamDetail,
} from '@/client/workspace'

type SubjectType = WorkspacePermissionRuleCreateInput['subjectType']
type ResourceType = WorkspacePermissionRuleCreateInput['resourceType']
type RuleAction = WorkspacePermissionRuleCreateInput['action']
type RuleEffect = WorkspacePermissionRuleCreateInput['effect']

interface SelectOption {
  label: string
  value: string
}

const props = withDefaults(defineProps<{
  activeFolderId?: string | null
  activeTeamDetail?: WorkspaceTeamDetail | null
  deletingRuleId?: string | null
  files?: WorkspaceFile[]
  folders?: WorkspaceFolder[]
  loading?: boolean
  rules?: WorkspacePermissionRule[]
  saving?: boolean
}>(), {
  activeFolderId: null,
  activeTeamDetail: null,
  deletingRuleId: null,
  files: () => [],
  folders: () => [],
  loading: false,
  rules: () => [],
  saving: false,
})

const emit = defineEmits<{
  'create-rule': [payload: WorkspacePermissionRuleCreateInput]
  'delete-rule': [ruleId: string]
}>()

const subjectType = shallowRef<SubjectType>('role')
const subjectId = shallowRef('')
const resourceType = shallowRef<ResourceType>('folder')
const resourceId = shallowRef('')
const action = shallowRef<RuleAction>('read')
const effect = shallowRef<RuleEffect>('deny')
const inheritRule = shallowRef(true)
const formError = shallowRef('')

const roleOptions = computed<SelectOption[]>(() => {
  const teamName = props.activeTeamDetail?.name ?? '当前团队'
  const teamId = props.activeTeamDetail?.id
  const roles = [
    ['guest', '访客'],
    ['member', '成员'],
    ['admin', '管理员'],
    ['owner', '所有者'],
  ] as const

  return roles.map(([role, label]) => ({
    label: `${teamName} / ${label}`,
    value: teamId ? `${teamId}:${role}` : role,
  }))
})

const subjectOptions = computed<SelectOption[]>(() => {
  if (subjectType.value === 'role') {
    return roleOptions.value
  }
  if (subjectType.value === 'team') {
    return props.activeTeamDetail
      ? [{ label: props.activeTeamDetail.name, value: props.activeTeamDetail.id }]
      : []
  }
  return (props.activeTeamDetail?.members ?? []).map((member) => ({
    label: `${member.display_name} / ${member.email}`,
    value: String(member.user_id),
  }))
})

const folderOptions = computed<SelectOption[]>(() => {
  const options: SelectOption[] = []
  collectFolderOptions(props.folders, [], options)
  if (props.activeFolderId && !options.some((option) => option.value === props.activeFolderId)) {
    options.unshift({ label: props.activeFolderId, value: props.activeFolderId })
  }
  return options
})

const fileOptions = computed<SelectOption[]>(() =>
  props.files.map((file) => ({
    label: file.name,
    value: file.id,
  })),
)

const resourceOptions = computed<SelectOption[]>(() => {
  if (resourceType.value === 'folder') {
    return folderOptions.value
  }
  if (resourceType.value === 'file') {
    return fileOptions.value
  }
  return []
})

const canSubmit = computed(() => Boolean(subjectId.value && resourceId.value))

watch(subjectOptions, () => ensureSubjectSelection(), { immediate: true })
watch(resourceOptions, () => ensureResourceSelection(), { immediate: true })
watch(
  () => props.activeFolderId,
  () => ensureResourceSelection(true),
  { immediate: true },
)

function ensureSubjectSelection() {
  if (!subjectOptions.value.length) {
    subjectId.value = ''
    return
  }
  if (!subjectOptions.value.some((option) => option.value === subjectId.value)) {
    const firstOption = subjectOptions.value[0]
    if (firstOption) {
      subjectId.value = firstOption.value
    }
  }
}

function ensureResourceSelection(preferActiveFolder = false) {
  if (!resourceOptions.value.length) {
    resourceId.value = ''
    return
  }
  if (preferActiveFolder && resourceType.value === 'folder' && props.activeFolderId) {
    const activeOption = resourceOptions.value.find((option) => option.value === props.activeFolderId)
    if (activeOption) {
      resourceId.value = activeOption.value
      return
    }
  }
  if (!resourceOptions.value.some((option) => option.value === resourceId.value)) {
    const firstOption = resourceOptions.value[0]
    if (firstOption) {
      resourceId.value = firstOption.value
    }
  }
}

function handleSubmit() {
  if (!canSubmit.value) {
    formError.value = '请选择权限主体和资源'
    return
  }

  formError.value = ''
  emit('create-rule', {
    action: action.value,
    effect: effect.value,
    inherit: inheritRule.value,
    resourceId: resourceId.value,
    resourceType: resourceType.value,
    subjectId: subjectId.value,
    subjectType: subjectType.value,
  })
}

function collectFolderOptions(folders: WorkspaceFolder[], parents: string[], options: SelectOption[]) {
  for (const folder of folders) {
    const path = [...parents, folder.name]
    options.push({ label: path.join(' / '), value: folder.id })
    collectFolderOptions(folder.children ?? [], path, options)
  }
}

function actionLabel(value: RuleAction) {
  return {
    delete: '删除',
    execute: '执行',
    manage: '管理',
    read: '读取',
    write: '写入',
  }[value]
}

function effectLabel(value: RuleEffect) {
  return value === 'deny' ? '拒绝' : '允许'
}

function subjectTypeLabel(value: SubjectType) {
  return {
    role: '角色',
    team: '团队',
    user: '用户',
  }[value]
}

function resourceTypeLabel(value: ResourceType) {
  return {
    file: '文件',
    folder: '目录',
    knowledge_base: '知识库',
    tool: '工具',
    workflow: '流程',
  }[value]
}

function ruleScopeLabel(rule: WorkspacePermissionRule) {
  return rule.inherit ? '继承' : '直接覆盖'
}

function effectTagType(value: RuleEffect) {
  return value === 'deny' ? 'error' : 'success'
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('zh-CN', {
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    month: '2-digit',
  }).format(new Date(value))
}
</script>

<template>
  <section class="border-t border-line bg-#FBFCFE px-4 py-4">
    <div class="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-3 max-md:grid-cols-1">
      <div class="min-w-0">
        <div class="flex items-center gap-2">
          <NIcon class="text-primary" aria-hidden="true"><ShieldCheck /></NIcon>
          <h3 class="m-0 text-ink text-16px font-700">权限规则</h3>
        </div>
        <p class="m-0 mt-1 text-13px text-sub leading-[1.55]">
          配置当前目录或文件的允许、拒绝、继承和直接覆盖规则
        </p>
      </div>
      <NTag round :bordered="false" type="warning">
        deny 优先
      </NTag>
    </div>

    <NAlert v-if="formError" class="mt-3" type="warning" :bordered="false">
      {{ formError }}
    </NAlert>

    <div class="mt-4 grid grid-cols-[minmax(0,1fr)_minmax(300px,0.78fr)] gap-4 max-xl:grid-cols-1">
      <section class="border border-line rounded-2 bg-surface p-3">
        <div class="mb-3">
          <h4 class="m-0 text-ink text-15px font-700">新增规则</h4>
          <p class="m-0 mt-1 text-12px text-sub">默认面向团队访客，拒绝读取当前目录并向下继承</p>
        </div>

        <NForm :show-feedback="false" label-placement="top">
          <div class="grid grid-cols-[120px_minmax(0,1fr)] gap-3 max-md:grid-cols-1">
            <NFormItem label="主体类型">
              <NSelect
                v-model:value="subjectType"
                :options="[
                  { label: '角色', value: 'role' },
                  { label: '团队', value: 'team' },
                  { label: '用户', value: 'user' },
                ]"
              />
            </NFormItem>
            <NFormItem label="主体">
              <NSelect v-model:value="subjectId" :options="subjectOptions" placeholder="选择主体" />
            </NFormItem>
          </div>

          <div class="grid grid-cols-[120px_minmax(0,1fr)] gap-3 max-md:grid-cols-1">
            <NFormItem label="资源类型">
              <NSelect
                v-model:value="resourceType"
                :options="[
                  { label: '目录', value: 'folder' },
                  { label: '文件', value: 'file' },
                ]"
              />
            </NFormItem>
            <NFormItem label="资源">
              <NSelect v-model:value="resourceId" :options="resourceOptions" placeholder="选择资源" />
            </NFormItem>
          </div>

          <div class="grid grid-cols-[1fr_1fr_auto] items-end gap-3 max-md:grid-cols-1">
            <NFormItem label="动作">
              <NSelect
                v-model:value="action"
                :options="[
                  { label: '读取', value: 'read' },
                  { label: '写入', value: 'write' },
                  { label: '删除', value: 'delete' },
                  { label: '管理', value: 'manage' },
                  { label: '执行', value: 'execute' },
                ]"
              />
            </NFormItem>
            <NFormItem label="效果">
              <NRadioGroup v-model:value="effect">
                <NRadioButton value="deny">拒绝</NRadioButton>
                <NRadioButton value="allow">允许</NRadioButton>
              </NRadioGroup>
            </NFormItem>
            <NCheckbox v-model:checked="inheritRule" class="mb-6px">
              继承到子资源
            </NCheckbox>
          </div>

          <div class="flex justify-end">
            <NButton
              data-testid="submit-permission-rule"
              type="primary"
              :disabled="!canSubmit"
              :loading="saving"
              @click="handleSubmit"
            >
              <template #icon>
                <NIcon aria-hidden="true"><Plus /></NIcon>
              </template>
              添加规则
            </NButton>
          </div>
        </NForm>
      </section>

      <section class="min-w-0 border border-line rounded-2 bg-surface p-3">
        <div class="mb-3 flex items-center justify-between gap-2">
          <div>
            <h4 class="m-0 text-ink text-15px font-700">当前规则</h4>
            <p class="m-0 mt-1 text-12px text-sub">列表顺序仅用于审阅，后端判定以 deny 优先</p>
          </div>
          <NSpin v-if="loading" size="small" />
        </div>

        <NEmpty v-if="!rules.length && !loading" size="small" description="暂无权限规则" />
        <NList v-else :show-divider="false">
          <NListItem v-for="rule in rules" :key="rule.id" class="!px-0 !py-2">
            <div class="grid gap-2 border border-line rounded-1.5 bg-#FBFCFE p-2">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <div class="flex flex-wrap items-center gap-1.5">
                    <NTag size="small" round :bordered="false" :type="effectTagType(rule.effect)">
                      {{ effectLabel(rule.effect) }}
                    </NTag>
                    <NTag size="small" round :bordered="false">
                      {{ actionLabel(rule.action) }}
                    </NTag>
                    <NTag size="small" round :bordered="false" type="info">
                      {{ ruleScopeLabel(rule) }}
                    </NTag>
                  </div>
                  <p class="m-0 mt-2 break-words text-13px text-ink leading-[1.45]">
                    {{ subjectTypeLabel(rule.subject_type) }}：{{ rule.subject_label }}
                    <span class="text-sub"> -> </span>
                    {{ resourceTypeLabel(rule.resource_type) }}：{{ rule.resource_label }}
                  </p>
                  <p class="m-0 mt-1 text-12px text-sub">
                    {{ formatTime(rule.created_at) }} · {{ rule.created_by }}
                  </p>
                </div>
                <NButton
                  :data-testid="`delete-permission-rule-${rule.id}`"
                  size="tiny"
                  type="error"
                  secondary
                  :loading="deletingRuleId === rule.id"
                  @click="emit('delete-rule', rule.id)"
                >
                  <template #icon>
                    <NIcon aria-hidden="true"><Trash2 /></NIcon>
                  </template>
                  删除
                </NButton>
              </div>
              <div class="flex items-center gap-1.5 text-12px text-sub">
                <NIcon aria-hidden="true"><GitBranch /></NIcon>
                <span>{{ rule.inherit ? '会作用于子目录和文件' : '仅覆盖当前资源' }}</span>
              </div>
            </div>
          </NListItem>
        </NList>
      </section>
    </div>
  </section>
</template>
