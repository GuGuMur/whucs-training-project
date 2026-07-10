<script setup lang="ts">
import { computed, shallowRef, watch } from 'vue'
import { Pencil, FolderInput, Copy, Tag, ShieldCheck, History, MessageSquareText, Plus, Trash2, RotateCcw } from '@lucide/vue'
import type {
  WorkspaceFile,
  WorkspaceFileAnnotation, WorkspaceFileAnnotationCreateInput, WorkspaceFileAnnotationReplyInput,
  WorkspaceFileCopyInput, WorkspaceFileUpdateInput, WorkspaceFileVersion,
  WorkspaceFolderOption, WorkspacePermissionRule,
} from '@/client/workspace'

const props = withDefaults(defineProps<{
  file: WorkspaceFile | null
  folderOptions?: WorkspaceFolderOption[]
  versions?: WorkspaceFileVersion[]
  annotations?: WorkspaceFileAnnotation[]
  permissionRules?: WorkspacePermissionRule[]
  show: boolean
  initialTab?: string
  copying?: boolean
  updating?: boolean
  loadingVersions?: boolean
  restoringVersionId?: string | null
  loadingAnnotations?: boolean
  savingAnnotation?: boolean
  deletingAnnotationId?: string | null
  permissionsLoading?: boolean
  deletingPermissionRuleId?: string | null
}>(), {
  file: null, folderOptions: () => [], versions: () => [], annotations: () => [], permissionRules: () => [],
  show: false, initialTab: 'rename', copying: false, updating: false, loadingVersions: false,
  restoringVersionId: null, loadingAnnotations: false, savingAnnotation: false,
  deletingAnnotationId: null, permissionsLoading: false, deletingPermissionRuleId: null,
})

const emit = defineEmits<{
  'update:show': [value: boolean]
  close: []
  'update-file': [fileId: string, payload: WorkspaceFileUpdateInput]
  'copy-file': [fileId: string, payload: WorkspaceFileCopyInput]
  'load-versions': [fileId: string]
  'restore-version': [fileId: string, versionId: string]
  'load-annotations': [fileId: string]
  'create-annotation': [fileId: string, payload: WorkspaceFileAnnotationCreateInput]
  'reply-annotation': [annotationId: string, payload: WorkspaceFileAnnotationReplyInput]
  'delete-annotation': [fileId: string, annotationId: string]
  'delete-permission-rule': [ruleId: string]
}>()

const activeTab = shallowRef(props.initialTab)
const renameValue = shallowRef('')
const moveTarget = shallowRef<string | null>(null)
const copyTarget = shallowRef<string | null>(null)
const editTags = shallowRef<string[]>([])
const annotationContent = shallowRef('')

watch(() => props.show, (v) => {
  if (v && props.file) {
    activeTab.value = props.initialTab
    renameValue.value = props.file.name
    editTags.value = [...(props.file.tags || [])]
    moveTarget.value = null; copyTarget.value = null; annotationContent.value = ''
  }
})

const fileId = computed(() => props.file?.id ?? '')

function close() { emit('update:show', false); emit('close') }
function rename() { if (renameValue.value.trim() && props.file) emit('update-file', props.file.id, { name: renameValue.value.trim() }) }
function doMove() { if (moveTarget.value && props.file) emit('update-file', props.file.id, { folderId: moveTarget.value }) }
function doCopy() { if (copyTarget.value && props.file) emit('copy-file', props.file.id, { targetFolderId: copyTarget.value }) }
function saveTags() { if (props.file) emit('update-file', props.file.id, { tags: [...editTags.value] }) }
function createAnnotation() {
  if (!annotationContent.value.trim() || !props.file) return
  emit('create-annotation', props.file.id, { content: annotationContent.value.trim() })
  annotationContent.value = ''
}
</script>

<template>
  <NDrawer :show="show" :width="420" placement="right" @update:show="(v: boolean) => v ? null : close()">
    <NDrawerContent :title="file?.name ?? '文件操作'" closable @close="close">
      <NTabs v-model:value="activeTab" type="line" size="small" class="mb-4">
        <NTabPane name="rename" tab="重命名">
          <div class="grid gap-3 pt-2">
            <p class="m-0 text-sub text-13px">当前名称：{{ file?.name }}</p>
            <NInput v-model:value="renameValue" placeholder="新文件名" />
            <NButton type="primary" size="small" :loading="updating" @click="rename">保存</NButton>
          </div>
        </NTabPane>

        <NTabPane name="move" tab="移动">
          <div class="grid gap-3 pt-2">
            <p class="m-0 text-sub text-13px">移动到目标文件夹</p>
            <NTreeSelect v-model:value="moveTarget" :options="folderOptions" placeholder="选择目标文件夹" clearable filterable />
            <NButton type="primary" size="small" :disabled="!moveTarget" :loading="updating" @click="doMove">移动</NButton>
          </div>
        </NTabPane>

        <NTabPane name="copy" tab="复制">
          <div class="grid gap-3 pt-2">
            <p class="m-0 text-sub text-13px">复制到目标文件夹</p>
            <NTreeSelect v-model:value="copyTarget" :options="folderOptions" placeholder="选择目标文件夹" clearable filterable />
            <NButton type="primary" size="small" :disabled="!copyTarget" :loading="copying" @click="doCopy">复制</NButton>
          </div>
        </NTabPane>

        <NTabPane name="tags" tab="标签">
          <div class="grid gap-3 pt-2">
            <p class="m-0 text-sub text-13px">编辑文件标签</p>
            <NDynamicTags v-model:value="editTags" />
            <NButton type="primary" size="small" :loading="updating" @click="saveTags">保存标签</NButton>
          </div>
        </NTabPane>

        <NTabPane name="versions" tab="版本">
          <div class="grid gap-3 pt-2">
            <NButton size="small" secondary :loading="loadingVersions" @click="emit('load-versions', fileId)">
              <template #icon><NIcon :size="14"><History /></NIcon></template> 加载版本
            </NButton>
            <NEmpty v-if="!versions.length && !loadingVersions" size="small" description="暂无版本" />
            <NList v-else :show-divider="false">
              <NListItem v-for="v in versions" :key="v.id" class="!px-0 !py-2">
                <div class="flex items-center justify-between gap-3 w-full">
                  <div class="min-w-0">
                    <p class="m-0 text-ink text-13px font-650 truncate">{{ v.name }}</p>
                    <p class="m-0 mt-0.5 text-sub text-11px">v{{ v.version_no }} · {{ v.created_by }}</p>
                  </div>
                  <NButton size="tiny" secondary :loading="restoringVersionId === v.id" @click="emit('restore-version', fileId, v.id)">
                    <template #icon><NIcon :size="12"><RotateCcw /></NIcon></template> 恢复
                  </NButton>
                </div>
              </NListItem>
            </NList>
          </div>
        </NTabPane>

        <NTabPane name="permissions" tab="权限">
          <div class="grid gap-3 pt-2">
            <NSpin :show="permissionsLoading">
              <NEmpty v-if="!permissionRules.length" size="small" description="暂无权限规则" />
              <NList v-else :show-divider="false">
                <NListItem v-for="rule in permissionRules" :key="rule.id" class="!px-0 !py-2">
                  <div class="flex items-center justify-between gap-3 w-full">
                    <div class="min-w-0">
                      <p class="m-0 text-ink text-13px font-650 truncate">{{ rule.subject_label }} · {{ rule.action }}</p>
                      <p class="m-0 mt-0.5 text-sub text-11px">{{ rule.resource_label }} / {{ rule.effect === 'allow' ? '允许' : '拒绝' }}{{ rule.inherit ? ' · 继承' : '' }}</p>
                    </div>
                    <NButton size="tiny" secondary type="error" :loading="deletingPermissionRuleId === rule.id" @click="emit('delete-permission-rule', rule.id)">
                      <template #icon><NIcon :size="12"><Trash2 /></NIcon></template>
                    </NButton>
                  </div>
                </NListItem>
              </NList>
            </NSpin>
          </div>
        </NTabPane>

        <NTabPane name="annotations" tab="批注">
          <div class="grid gap-3 pt-2">
            <NButton size="small" secondary :loading="loadingAnnotations" @click="emit('load-annotations', fileId)">
              <template #icon><NIcon :size="14"><MessageSquareText /></NIcon></template> 加载批注
            </NButton>
            <NEmpty v-if="!annotations.length && !loadingAnnotations" size="small" description="暂无批注" />
            <div v-else class="grid gap-3 max-h-300px overflow-y-auto">
              <div v-for="a in annotations" :key="a.id" class="rounded-2 bg-muted p-3">
                <div class="flex items-start justify-between gap-2">
                  <div class="min-w-0">
                    <p class="m-0 text-ink text-13px font-650">{{ a.author_name }}</p>
                    <p class="m-0 mt-1 text-12px leading-[1.65]">{{ a.content }}</p>
                  </div>
                  <NButton size="tiny" text type="error" :loading="deletingAnnotationId === a.id" @click="emit('delete-annotation', fileId, a.id)">
                    <template #icon><NIcon :size="12"><Trash2 /></NIcon></template>
                  </NButton>
                </div>
              </div>
            </div>
            <div class="flex gap-2">
              <NInput v-model:value="annotationContent" placeholder="添加批注..." size="small" @keyup.enter="createAnnotation" />
              <NButton size="small" type="primary" :loading="savingAnnotation" :disabled="!annotationContent.trim()" @click="createAnnotation">
                <template #icon><NIcon :size="14"><Plus /></NIcon></template>
              </NButton>
            </div>
          </div>
        </NTabPane>
      </NTabs>
    </NDrawerContent>
  </NDrawer>
</template>
