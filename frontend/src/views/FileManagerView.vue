<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import FileWorkbench from '@/components/files/FileWorkbench.vue'
import type {
  WorkspaceFile, WorkspaceFileContentUpdateInput, WorkspaceFileCopyInput,
  WorkspaceFileFilters, WorkspaceFileUpdateInput, WorkspaceFileUploadInput,
  WorkspaceFileBatchUploadInput,
  WorkspacePermissionRuleCreateInput,
} from '@/client/workspace'
import { useWorkspaceLayoutMode } from '@/composables/useWorkspaceLayoutMode'
import { useWorkspaceNavigation } from '@/composables/useWorkspaceNavigation'
import DesktopWorkspaceLayout from '@/layouts/DesktopWorkspaceLayout.vue'
import MobileWorkspaceLayout from '@/layouts/MobileWorkspaceLayout.vue'
import { useWorkspaceStore } from '@/stores/workspace'

const workspace = useWorkspaceStore()
const {
  activeFolderId, annotationSaving, apiState, copyingFileId,
  deletingAnnotationId, deletingFileId, deletingPermissionRuleId,
  editingFileContentId, fileAnnotationsById, fileContentById, fileContentLoadingId,
  fileFilters, fileListLoading, files,
  fileVersionsById, folderOptions, folders, folderTreeLoading, markingNotificationId,
  notifications, permissionRules, permissionRulesLoading,
  permissionRuleSaving, reparsingFileId, restoringVersionId, summary,
  updatingFileId, uploadingFile, versionFileId,
} = storeToRefs(workspace)

const { isMobileLayout } = useWorkspaceLayoutMode()
const { apiStateLabel, apiStateType, navItems } = useWorkspaceNavigation(apiState, 'files')
const layout = computed(() => (isMobileLayout.value ? MobileWorkspaceLayout : DesktopWorkspaceLayout))

onMounted(() => {
  void workspace.loadWorkspace()
  void workspace.loadPermissionRules()
})

function handleDeleteFile(file: WorkspaceFile) { workspace.deleteFile(file.id) }
function handleDownloadFile(file: WorkspaceFile) {
  workspace.downloadFile(file.id).then((blob) => {
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = file.name; a.click(); URL.revokeObjectURL(url)
  })
}
async function handleUpdateFileContent(fileId: string, payload: WorkspaceFileContentUpdateInput) {
  await workspace.updateFileContent(fileId, payload)
  await workspace.loadFileVersions(fileId)
}
</script>

<template>
  <component :is="layout" :api-state-label="apiStateLabel" :api-state-type="apiStateType" :nav-items="navItems" :unread-notifications="summary.unread_notifications" :notifications="notifications" :marking-notification-id="markingNotificationId" page-title="文件管理" @mark-notification-read="(id: string) => workspace.markNotificationRead(id)">
    <FileWorkbench
      :active-folder-id="activeFolderId"
      :annotation-saving="annotationSaving"
      :copying-file-id="copyingFileId"
      :deleting-annotation-id="deletingAnnotationId"
      :deleting-file-id="deletingFileId"
      :deleting-permission-rule-id="deletingPermissionRuleId"
      :file-annotations-by-id="fileAnnotationsById"
      :file-content-by-id="fileContentById"
      :file-content-loading-id="fileContentLoadingId"
      :file-versions-by-id="fileVersionsById"
      :filters="fileFilters"
      :files="files"
      :folder-options="folderOptions"
      :folder-tree-loading="folderTreeLoading"
      :folders="folders"
      :listing-files="fileListLoading"
      :permission-rules="permissionRules"
      :permissions-loading="permissionRulesLoading"
      :permission-rule-saving="permissionRuleSaving"
      :reparsing-file-id="reparsingFileId"
      :restoring-version-id="restoringVersionId"
      :saving-file-content-id="editingFileContentId"
      :updating-file-id="updatingFileId"
      :uploading-file="uploadingFile"
      :version-file-id="versionFileId"
      @copy-file="(fid: string, p: WorkspaceFileCopyInput) => workspace.copyFile(fid, p)"
      @create-file-annotation="workspace.createFileAnnotation"
      @create-folder="workspace.createFolder"
      @delete-file="handleDeleteFile"
      @delete-file-annotation="workspace.deleteFileAnnotation"
      @delete-folder="(fid: string) => workspace.deleteFolder(fid)"
      @delete-permission-rule="(rid: string) => workspace.deletePermissionRule(rid)"
      @download-file="handleDownloadFile"
      @create-permission-rule="(p: WorkspacePermissionRuleCreateInput) => workspace.createPermissionRule(p)"
      @load-file-content="(fid: string) => workspace.loadFileContent(fid)"
      @load-file-annotations="(fid: string) => workspace.loadFileAnnotations(fid)"
      @load-file-versions="(fid: string) => workspace.loadFileVersions(fid)"
      @reply-file-annotation="(aid: string, p: any) => workspace.replyFileAnnotation(aid, p)"
      @rename-folder="(fid: string, name: string) => workspace.updateFolder(fid, { name })"
      @reparse-file="(file: WorkspaceFile) => workspace.reparseFile(file.id)"
      @restore-file-version="(fid: string, vid: string) => workspace.restoreFileVersion(fid, vid)"
      @search-files="(f: WorkspaceFileFilters) => workspace.searchFiles(f)"
      @select-folder="(fid: string) => workspace.selectFolder(fid)"
      @update-file-content="handleUpdateFileContent"
      @update-file="(fid: string, p: WorkspaceFileUpdateInput) => workspace.updateFile(fid, p)"
      @upload-file="(p: WorkspaceFileUploadInput) => workspace.uploadFile(p)"
      @upload-files="(p: WorkspaceFileBatchUploadInput) => workspace.uploadFiles(p)"
    />
  </component>
</template>
