<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import AgentWorkflowPanel from '@/components/workspace/AgentWorkflowPanel.vue'
import FileWorkbench from '@/components/workspace/FileWorkbench.vue'
import RagInsightPanel from '@/components/workspace/RagInsightPanel.vue'
import SummaryStrip from '@/components/workspace/SummaryStrip.vue'
import TeamAuditPanel from '@/components/workspace/TeamAuditPanel.vue'
import type {
  WorkspaceFile,
  WorkspaceFileCopyInput,
  WorkspaceFileFilters,
  WorkspaceFileUpdateInput,
  WorkspaceFileUploadInput,
  WorkspaceFolderCreateInput,
  WorkspaceFolderUpdateInput,
  WorkspaceTeamCreateInput,
  WorkspaceTeamInviteInput,
  WorkspaceTeamRole,
} from '@/client/workspace'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const {
  activeFolderId,
  activeTeamDetail,
  apiState,
  auditLogs,
  creatingFolder,
  copyingFileId,
  deletingFileId,
  deletingFolderId,
  downloadingFileId,
  fileFilters,
  fileListLoading,
  fileVersionsById,
  files,
  folderOptions,
  folders,
  folderTreeLoading,
  narrative,
  summary,
  teams,
  teamOperationLoading,
  tools,
  restoringVersionId,
  updatingFileId,
  updatingFolderId,
  uploadingFile,
  versionFileId,
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
          :copying-file-id="copyingFileId"
          :creating-folder="creatingFolder"
          :deleting-file-id="deletingFileId"
          :deleting-folder-id="deletingFolderId"
          :downloading-file-id="downloadingFileId"
          :filters="fileFilters"
          :file-versions-by-id="fileVersionsById"
          :files="files"
          :folder-options="folderOptions"
          :folder-tree-loading="folderTreeLoading"
          :folders="folders"
          :listing-files="fileListLoading"
          :restoring-version-id="restoringVersionId"
          :updating-file-id="updatingFileId"
          :updating-folder-id="updatingFolderId"
          :uploading-file="uploadingFile"
          :version-file-id="versionFileId"
          @copy-file="handleCopyFile"
          @create-folder="handleCreateFolder"
          @delete-file="handleDeleteFile"
          @delete-folder="handleDeleteFolder"
          @download-file="handleDownloadFile"
          @load-file-versions="handleLoadFileVersions"
          @restore-file-version="handleRestoreFileVersion"
          @search-files="handleSearchFiles"
          @select-folder="workspace.selectFolder"
          @update-file="handleUpdateFile"
          @update-folder="handleUpdateFolder"
          @upload-file="handleUploadFile"
        />
        <AgentWorkflowPanel
          id="automation"
          :agent-steps="narrative.agentSteps"
          :tools="tools"
          :workflows="workflows"
        />
      </div>

      <div class="grid content-start gap-4 min-w-0">
        <RagInsightPanel id="rag" :narrative="narrative" />
        <TeamAuditPanel
          id="teams"
          :active-team-detail="activeTeamDetail"
          :audit-logs="auditLogs"
          :team-operation-loading="teamOperationLoading"
          :teams="teams"
          @create-team="handleCreateTeam"
          @invite-team-member="handleInviteTeamMember"
          @load-team-detail="handleLoadTeamDetail"
          @remove-team-member="handleRemoveTeamMember"
          @update-team-member-role="handleUpdateTeamMemberRole"
        />
      </div>
    </div>
  </component>
</template>
