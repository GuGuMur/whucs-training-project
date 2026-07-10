<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import AgentWorkflowPanel from '@/components/workflow/AgentWorkflowPanel.vue'
import FileWorkbench from '@/components/files/FileWorkbench.vue'
import RagInsightPanel from '@/components/rag/RagInsightPanel.vue'
import SummaryStrip from '@/components/shared/SummaryStrip.vue'
import TeamAuditPanel from '@/components/team/TeamAuditPanel.vue'
import type {
  WorkspaceFile,
  WorkspaceFileAnnotationCreateInput,
  WorkspaceFileAnnotationReplyInput,
  WorkspaceFileCopyInput,
  WorkspaceFileFilters,
  WorkspaceFileUpdateInput,
  WorkspaceFileUploadInput,
  WorkspaceFolderCreateInput,
  WorkspaceFolderUpdateInput,
  WorkspaceKnowledgeBaseCreateInput,
  WorkspacePermissionRuleCreateInput,
  WorkspaceQuestionInput,
  WorkspaceTeamCreateInput,
  WorkspaceTeamInviteInput,
  WorkspaceTeamRole,
  WorkspaceWorkflowCreateInput,
  WorkspaceWorkflowExecuteInput,
  WorkspaceWorkflowUpdateInput,
} from '@/client/workspace'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const {
  activeFolderId,
  activeKnowledgeBaseId,
  activeKnowledgeDocuments,
  activeTeamDetail,
  activeWorkflowExecution,
  activeWorkflowId,
  activeWorkflowValidation,
  addingKnowledgeDocument,
  annotationFileIdLoading,
  annotationSaving,
  apiState,
  askingQuestion,
  auditLogs,
  creatingFolder,
  copyingFileId,
  deletingAnnotationId,
  deletingFileId,
  deletingFolderId,
  deletingPermissionRuleId,
  downloadingFileId,
  fileFilters,
  fileAnnotationsById,
  fileListLoading,
  fileVersionsById,
  files,
  folderOptions,
  folders,
  folderTreeLoading,
  indexedFiles,
  knowledgeBases,
  knowledgeOperationLoading,
  markingNotificationId,
  narrative,
  notifications,
  notificationsLoading,
  permissionRuleSaving,
  permissionRules,
  permissionRulesLoading,
  summary,
  teams,
  teamOperationLoading,
  tools,
  restoringVersionId,
  updatingFileId,
  updatingFolderId,
  uploadingFile,
  versionFileId,
  workflowOperationLoading,
  workflows,
} = storeToRefs(workspace)
const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState)
const workspaceLayout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

onMounted(() => {
  void workspace.loadWorkspace()
})

async function handleDownloadFile(file: WorkspaceFile) {
  const blob = await workspace.downloadFile(file.id)
  saveBlob(file, blob)
}

async function handleDeleteFile(file: WorkspaceFile) {
  await workspace.deleteFile(file.id)
}

async function handleUpdateFile(fileId: string, payload: WorkspaceFileUpdateInput) {
  await workspace.updateFile(fileId, payload)
}

async function handleCopyFile(fileId: string, payload: WorkspaceFileCopyInput) {
  await workspace.copyFile(fileId, payload)
}

async function handleLoadFileVersions(fileId: string) {
  await workspace.loadFileVersions(fileId)
}

async function handleLoadFileAnnotations(fileId: string) {
  await workspace.loadFileAnnotations(fileId)
}

async function handleCreateFileAnnotation(fileId: string, payload: WorkspaceFileAnnotationCreateInput) {
  await workspace.createFileAnnotation(fileId, payload)
}

async function handleReplyFileAnnotation(annotationId: string, payload: WorkspaceFileAnnotationReplyInput) {
  await workspace.replyFileAnnotation(annotationId, payload)
}

async function handleDeleteFileAnnotation(fileId: string, annotationId: string) {
  await workspace.deleteFileAnnotation(fileId, annotationId)
}

async function handleMarkNotificationRead(notificationId: string) {
  await workspace.markNotificationRead(notificationId)
}

async function handleRestoreFileVersion(fileId: string, versionId: string) {
  await workspace.restoreFileVersion(fileId, versionId)
  await workspace.loadFileVersions(fileId)
}

async function handleSearchFiles(filters: WorkspaceFileFilters) {
  await workspace.searchFiles(filters)
}

async function handleUploadFile(payload: WorkspaceFileUploadInput) {
  await workspace.uploadFile(payload)
}

async function handleCreateFolder(payload: WorkspaceFolderCreateInput) {
  await workspace.createFolder(payload)
}

async function handleUpdateFolder(folderId: string, payload: WorkspaceFolderUpdateInput) {
  await workspace.updateFolder(folderId, payload)
}

async function handleDeleteFolder(folderId: string) {
  await workspace.deleteFolder(folderId)
}

async function handleCreatePermissionRule(payload: WorkspacePermissionRuleCreateInput) {
  await workspace.createPermissionRule(payload)
}

async function handleDeletePermissionRule(ruleId: string) {
  await workspace.deletePermissionRule(ruleId)
}

async function handleCreateKnowledgeBase(payload: WorkspaceKnowledgeBaseCreateInput) {
  await workspace.createKnowledgeBase(payload)
}

async function handleSelectKnowledgeBase(kbId: string) {
  await workspace.selectKnowledgeBase(kbId)
}

async function handleAddKnowledgeDocument(kbId: string, fileId: string) {
  await workspace.addKnowledgeDocument(kbId, fileId)
}

async function handleAskKnowledgeQuestion(payload: WorkspaceQuestionInput) {
  await workspace.askKnowledgeQuestion(payload)
}

async function handleCreateTeam(payload: WorkspaceTeamCreateInput) {
  await workspace.createTeam(payload)
}

async function handleLoadTeamDetail(teamId: string) {
  await workspace.loadTeamDetail(teamId)
}

async function handleInviteTeamMember(teamId: string, payload: WorkspaceTeamInviteInput) {
  await workspace.inviteTeamMember(teamId, payload)
}

async function handleUpdateTeamMemberRole(teamId: string, memberId: string, role: WorkspaceTeamRole) {
  await workspace.updateTeamMemberRole(teamId, memberId, role)
}

async function handleRemoveTeamMember(teamId: string, memberId: string) {
  await workspace.removeTeamMember(teamId, memberId)
}

async function handleCreateWorkflow(payload: WorkspaceWorkflowCreateInput) {
  await workspace.createWorkflow(payload)
}

function handleSelectWorkflow(workflowId: string) {
  workspace.selectWorkflow(workflowId)
}

async function handleUpdateWorkflow(workflowId: string, payload: WorkspaceWorkflowUpdateInput) {
  await workspace.updateWorkflow(workflowId, payload)
}

async function handleValidateWorkflow(workflowId: string) {
  await workspace.validateWorkflow(workflowId)
}

async function handlePublishWorkflow(workflowId: string) {
  await workspace.publishWorkflow(workflowId)
}

async function handleExecuteWorkflow(workflowId: string, payload: WorkspaceWorkflowExecuteInput) {
  await workspace.executeWorkflow(workflowId, payload)
}

function saveBlob(file: WorkspaceFile, blob: Blob) {
  if (
    typeof document === 'undefined' ||
    typeof URL === 'undefined' ||
    typeof URL.createObjectURL !== 'function'
  ) {
    return
  }

  const objectUrl = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = objectUrl
  anchor.download = file.name
  anchor.rel = 'noopener'
  document.body.append(anchor)
  anchor.click()
  anchor.remove()
  URL.revokeObjectURL(objectUrl)
}
</script>

<template>
  <component
    :is="workspaceLayout"
    :api-state-label="apiStateLabel"
    :api-state-type="apiStateType"
    :nav-items="navItems"
    :unread-notifications="summary.unread_notifications"
  >
    <SummaryStrip :summary="summary" />

    <div class="mt-4 grid grid-cols-[minmax(0,1.55fr)_minmax(320px,0.9fr)] gap-4 max-xl:grid-cols-1">
      <div class="grid content-start gap-4 min-w-0">
        <FileWorkbench
          id="files"
          :active-folder-id="activeFolderId"
          :active-team-detail="activeTeamDetail"
          :annotation-file-id-loading="annotationFileIdLoading"
          :annotation-saving="annotationSaving"
          :copying-file-id="copyingFileId"
          :creating-folder="creatingFolder"
          :deleting-file-id="deletingFileId"
          :deleting-annotation-id="deletingAnnotationId"
          :deleting-folder-id="deletingFolderId"
          :deleting-permission-rule-id="deletingPermissionRuleId"
          :downloading-file-id="downloadingFileId"
          :filters="fileFilters"
          :file-annotations-by-id="fileAnnotationsById"
          :file-versions-by-id="fileVersionsById"
          :files="files"
          :folder-options="folderOptions"
          :folder-tree-loading="folderTreeLoading"
          :folders="folders"
          :listing-files="fileListLoading"
          :permission-rule-saving="permissionRuleSaving"
          :permission-rules="permissionRules"
          :permission-rules-loading="permissionRulesLoading"
          :restoring-version-id="restoringVersionId"
          :updating-file-id="updatingFileId"
          :updating-folder-id="updatingFolderId"
          :uploading-file="uploadingFile"
          :version-file-id="versionFileId"
          @copy-file="handleCopyFile"
          @create-file-annotation="handleCreateFileAnnotation"
          @create-folder="handleCreateFolder"
          @create-permission-rule="handleCreatePermissionRule"
          @delete-file="handleDeleteFile"
          @delete-file-annotation="handleDeleteFileAnnotation"
          @delete-folder="handleDeleteFolder"
          @delete-permission-rule="handleDeletePermissionRule"
          @download-file="handleDownloadFile"
          @load-file-annotations="handleLoadFileAnnotations"
          @load-file-versions="handleLoadFileVersions"
          @reply-file-annotation="handleReplyFileAnnotation"
          @restore-file-version="handleRestoreFileVersion"
          @search-files="handleSearchFiles"
          @select-folder="workspace.selectFolder"
          @update-file="handleUpdateFile"
          @update-folder="handleUpdateFolder"
          @upload-file="handleUploadFile"
        />
        <AgentWorkflowPanel
          id="automation"
          :active-workflow-id="activeWorkflowId"
          :agent-steps="narrative.agentSteps"
          :files="files"
          :knowledge-bases="knowledgeBases"
          :tools="tools"
          :workflow-execution="activeWorkflowExecution"
          :workflow-operation-loading="workflowOperationLoading"
          :workflow-validation="activeWorkflowValidation"
          :workflows="workflows"
          @create-workflow="handleCreateWorkflow"
          @execute-workflow="handleExecuteWorkflow"
          @publish-workflow="handlePublishWorkflow"
          @select-workflow="handleSelectWorkflow"
          @update-workflow="handleUpdateWorkflow"
          @validate-workflow="handleValidateWorkflow"
        />
      </div>

      <div class="grid content-start gap-4 min-w-0">
        <RagInsightPanel
          id="rag"
          :active-knowledge-base-id="activeKnowledgeBaseId"
          :adding-knowledge-document="addingKnowledgeDocument"
          :asking-question="askingQuestion"
          :indexed-files="indexedFiles"
          :knowledge-bases="knowledgeBases"
          :knowledge-documents="activeKnowledgeDocuments"
          :loading-knowledge="knowledgeOperationLoading"
          :narrative="narrative"
          @add-knowledge-document="handleAddKnowledgeDocument"
          @ask-question="handleAskKnowledgeQuestion"
          @create-knowledge-base="handleCreateKnowledgeBase"
          @select-knowledge-base="handleSelectKnowledgeBase"
        />
        <TeamAuditPanel
          id="teams"
          :active-team-detail="activeTeamDetail"
          :audit-logs="auditLogs"
          :marking-notification-id="markingNotificationId"
          :notifications="notifications"
          :notifications-loading="notificationsLoading"
          :team-operation-loading="teamOperationLoading"
          :teams="teams"
          @create-team="handleCreateTeam"
          @invite-team-member="handleInviteTeamMember"
          @load-team-detail="handleLoadTeamDetail"
          @mark-notification-read="handleMarkNotificationRead"
          @remove-team-member="handleRemoveTeamMember"
          @update-team-member-role="handleUpdateTeamMemberRole"
        />
      </div>
    </div>
  </component>
</template>
