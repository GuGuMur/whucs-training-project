import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { resolveWorkspaceToken } from '@/auth'
import {
  copyWorkspaceFile,
  createWorkspaceTeam,
  createWorkspaceFolder,
  demoWorkspaceFileVersions,
  demoWorkspaceNarrative,
  demoWorkspaceFolders,
  demoWorkspaceSnapshot,
  demoWorkspaceTeamDetail,
  deleteWorkspaceFile,
  deleteWorkspaceFolder,
  downloadWorkspaceFile,
  fetchWorkspaceSnapshot,
  createWorkspaceTeamInvite,
  joinWorkspaceTeam,
  listWorkspaceTeams,
  listWorkspaceFileVersions,
  listWorkspaceFolders,
  listWorkspaceFiles,
  loadWorkspaceTeamDetail,
  removeWorkspaceTeamMember,
  restoreWorkspaceFileVersion,
  updateWorkspaceTeamMember,
  updateWorkspaceFile,
  updateWorkspaceFolder,
  uploadWorkspaceFile,
  type WorkspaceFile,
  type WorkspaceFileCopyInput,
  type WorkspaceFileFilters,
  type WorkspaceFileUpdateInput,
  type WorkspaceFileUploadInput,
  type WorkspaceFileVersion,
  type WorkspaceFolder,
  type WorkspaceFolderCreateInput,
  type WorkspaceFolderOption,
  type WorkspaceFolderUpdateInput,
  type WorkspaceNarrative,
  type WorkspaceSnapshot,
  type TeamSummary,
  type WorkspaceTeamCreateInput,
  type WorkspaceTeamDetail,
  type WorkspaceTeamInviteInput,
  type WorkspaceTeamMember,
  type WorkspaceTeamRole,
} from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'

export type WorkspaceApiState = 'demo' | 'live' | 'fallback'

const emptyFileFilters: WorkspaceFileFilters = {
  fileType: '',
  query: '',
  tag: '',
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const snapshot = shallowRef<WorkspaceSnapshot>(demoWorkspaceSnapshot)
  const folders = shallowRef<WorkspaceFolder[]>(cloneFolderTree(demoWorkspaceFolders.items))
  const fileVersionsById = shallowRef<Record<string, WorkspaceFileVersion[]>>(cloneVersionMap(demoWorkspaceFileVersions))
  const narrative = shallowRef<WorkspaceNarrative>(demoWorkspaceNarrative)
  const activeTeamDetail = shallowRef<WorkspaceTeamDetail | null>(demoWorkspaceTeamDetail)
  const loading = shallowRef(false)
  const folderTreeLoading = shallowRef(false)
  const activeFolderId = shallowRef<string | null>('personal-root')
  const creatingFolder = shallowRef(false)
  const updatingFolderId = shallowRef<string | null>(null)
  const deletingFolderId = shallowRef<string | null>(null)
  const deletingFileId = shallowRef<string | null>(null)
  const downloadingFileId = shallowRef<string | null>(null)
  const updatingFileId = shallowRef<string | null>(null)
  const copyingFileId = shallowRef<string | null>(null)
  const versionFileId = shallowRef<string | null>(null)
  const restoringVersionId = shallowRef<string | null>(null)
  const fileFilters = shallowRef<WorkspaceFileFilters>({ ...emptyFileFilters })
  const fileListLoading = shallowRef(false)
  const uploadingFile = shallowRef(false)
  const teamOperationLoading = shallowRef(false)
  const errorMessage = shallowRef('')
  const apiState = shallowRef<WorkspaceApiState>('demo')

  const files = computed(() => snapshot.value.files)
  const indexedFiles = computed(() => snapshot.value.files.filter((file) => file.parse_status === 'indexed'))
  const tools = computed(() => snapshot.value.tools)
  const workflows = computed(() => snapshot.value.workflows)
  const teams = computed(() => snapshot.value.teams)
  const auditLogs = computed(() => snapshot.value.audit_logs)
  const summary = computed(() => snapshot.value.summary)
  const folderOptions = computed(() => flattenFolderOptions(folders.value))
  const activeBreadcrumbs = computed(() => buildFolderBreadcrumbs(folders.value, activeFolderId.value))

  async function loadWorkspace(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      apiState.value = 'demo'
      fileFilters.value = { ...emptyFileFilters }
      resetFoldersToDemo()
      resetVersionsToDemo()
      snapshot.value = demoWorkspaceSnapshot
      narrative.value = demoWorkspaceNarrative
      activeTeamDetail.value = demoWorkspaceTeamDetail
      return
    }

    loading.value = true
    try {
      const [nextSnapshot, folderTree] = await Promise.all([
        fetchWorkspaceSnapshot(accessToken),
        listWorkspaceFolders(accessToken),
      ])
      snapshot.value = nextSnapshot
      folders.value = cloneFolderTree(folderTree.items)
      fileVersionsById.value = {}
      activeTeamDetail.value = null
      ensureActiveFolderSelection()
      narrative.value = demoWorkspaceNarrative
      fileFilters.value = { ...emptyFileFilters }
      apiState.value = 'live'
    } catch {
      snapshot.value = demoWorkspaceSnapshot
      narrative.value = demoWorkspaceNarrative
      resetFoldersToDemo()
      resetVersionsToDemo()
      activeTeamDetail.value = demoWorkspaceTeamDetail
      apiState.value = 'fallback'
    } finally {
      loading.value = false
    }
  }

  async function loadFolders(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      resetFoldersToDemo()
      return { items: folders.value }
    }

    folderTreeLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspaceFolders(accessToken)
      folders.value = cloneFolderTree(response.items)
      ensureActiveFolderSelection()
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '目录树加载失败，请稍后重试'
      throw error
    } finally {
      folderTreeLoading.value = false
    }
  }

  async function searchFiles(nextFilters: Partial<WorkspaceFileFilters> = {}) {
    const accessToken = requireAccessToken()
    const filters = normalizeFileFilters({ ...fileFilters.value, ...nextFilters })

    fileFilters.value = filters
    fileListLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspaceFiles(accessToken, filters)
      snapshot.value = {
        ...snapshot.value,
        files: response.items,
        summary: {
          ...snapshot.value.summary,
          file_count: response.total,
          indexed_count: response.items.filter((file) => file.parse_status === 'indexed').length,
        },
      }
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '文件检索失败，请稍后重试'
      throw error
    } finally {
      fileListLoading.value = false
    }
  }

  async function resetFileFilters() {
    return searchFiles(emptyFileFilters)
  }

  async function uploadFile(payload: WorkspaceFileUploadInput) {
    const accessToken = requireAccessToken()

    uploadingFile.value = true
    errorMessage.value = ''
    try {
      const uploaded = await uploadWorkspaceFile(accessToken, payload)
      fileFilters.value = { ...emptyFileFilters }
      insertFileIntoSnapshot(uploaded)
      apiState.value = 'live'
      return uploaded
    } catch (error) {
      errorMessage.value = '文件上传失败，请检查文件和权限后重试'
      throw error
    } finally {
      uploadingFile.value = false
    }
  }

  async function updateFile(fileId: string, payload: WorkspaceFileUpdateInput) {
    const accessToken = requireAccessToken()
    const nextPayload = normalizeFileUpdatePayload(payload)

    updatingFileId.value = fileId
    errorMessage.value = ''
    try {
      const updated = await updateWorkspaceFile(accessToken, fileId, nextPayload)
      replaceFileInSnapshot(updated)
      apiState.value = 'live'
      return updated
    } catch (error) {
      errorMessage.value = '文件属性更新失败，请检查目录和权限后重试'
      throw error
    } finally {
      updatingFileId.value = null
    }
  }

  async function copyFile(fileId: string, payload: WorkspaceFileCopyInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceFileCopyInput = {
      targetFolderId: payload.targetFolderId,
    }
    if ('name' in payload) {
      nextPayload.name = payload.name?.trim() || null
    }
    if ('tags' in payload) {
      nextPayload.tags = payload.tags ? normalizeTags(payload.tags) : null
    }

    copyingFileId.value = fileId
    errorMessage.value = ''
    try {
      const copied = await copyWorkspaceFile(accessToken, fileId, nextPayload)
      insertFileIntoSnapshot(copied)
      fileVersionsById.value = {
        ...fileVersionsById.value,
        [copied.id]: [],
      }
      apiState.value = 'live'
      return copied
    } catch (error) {
      errorMessage.value = '文件复制失败，请检查目标目录和权限后重试'
      throw error
    } finally {
      copyingFileId.value = null
    }
  }

  async function downloadFile(fileId: string) {
    const accessToken = requireAccessToken()

    downloadingFileId.value = fileId
    errorMessage.value = ''
    try {
      return await downloadWorkspaceFile(accessToken, fileId)
    } catch (error) {
      errorMessage.value = '文件下载失败，请稍后重试'
      throw error
    } finally {
      downloadingFileId.value = null
    }
  }

  async function deleteFile(fileId: string) {
    const accessToken = requireAccessToken()

    deletingFileId.value = fileId
    errorMessage.value = ''
    try {
      await deleteWorkspaceFile(accessToken, fileId)
      removeFileFromSnapshot(fileId)
      removeFileVersions(fileId)
    } catch (error) {
      errorMessage.value = '文件删除失败，请检查权限后重试'
      throw error
    } finally {
      deletingFileId.value = null
    }
  }

  async function loadFileVersions(fileId: string) {
    const accessToken = requireAccessToken()

    versionFileId.value = fileId
    errorMessage.value = ''
    try {
      const response = await listWorkspaceFileVersions(accessToken, fileId)
      fileVersionsById.value = {
        ...fileVersionsById.value,
        [fileId]: response.items,
      }
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '文件版本加载失败，请稍后重试'
      throw error
    } finally {
      versionFileId.value = null
    }
  }

  async function loadTeams(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      snapshot.value = {
        ...snapshot.value,
        teams: demoWorkspaceSnapshot.teams,
      }
      activeTeamDetail.value = demoWorkspaceTeamDetail
      return { items: snapshot.value.teams }
    }

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspaceTeams(accessToken)
      snapshot.value = {
        ...snapshot.value,
        teams: response.items,
        summary: {
          ...snapshot.value.summary,
          unread_notifications: response.items.reduce((sum, team) => sum + team.unread_count, 0),
        },
      }
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '团队列表加载失败，请稍后重试'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function createTeam(payload: WorkspaceTeamCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceTeamCreateInput = {
      description: payload.description?.trim() || null,
      name: payload.name.trim(),
    }

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      const detail = await createWorkspaceTeam(accessToken, nextPayload)
      activeTeamDetail.value = detail
      upsertTeamSummary(teamDetailToSummary(detail), true)
      folders.value = addFolderToTree(removeFolderFromTree(folders.value, detail.root_folder.id).items, detail.root_folder)
      activeFolderId.value = detail.root_folder.id
      apiState.value = 'live'
      return detail
    } catch (error) {
      errorMessage.value = '团队创建失败，请检查名称后重试'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function loadTeamDetail(teamId: string) {
    const accessToken = requireAccessToken()

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      const detail = await loadWorkspaceTeamDetail(accessToken, teamId)
      activeTeamDetail.value = detail
      upsertTeamSummary(teamDetailToSummary(detail))
      apiState.value = 'live'
      return detail
    } catch (error) {
      errorMessage.value = '团队详情加载失败，请检查权限后重试'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function inviteTeamMember(teamId: string, payload: WorkspaceTeamInviteInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceTeamInviteInput = {
      email: payload.email.trim(),
      role: payload.role,
    }

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      const invite = await createWorkspaceTeamInvite(accessToken, teamId, nextPayload)
      if (activeTeamDetail.value?.id === teamId) {
        activeTeamDetail.value = {
          ...activeTeamDetail.value,
          invites: [invite, ...activeTeamDetail.value.invites.filter((item) => item.id !== invite.id)],
        }
      }
      apiState.value = 'live'
      return invite
    } catch (error) {
      errorMessage.value = '邀请创建失败，请检查邮箱和权限后重试'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function joinTeam(teamId: string, inviteToken: string) {
    const accessToken = requireAccessToken()

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      const member = await joinWorkspaceTeam(accessToken, teamId, inviteToken.trim())
      mergeTeamMember(teamId, member)
      apiState.value = 'live'
      return member
    } catch (error) {
      errorMessage.value = '加入团队失败，请检查邀请是否有效'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function updateTeamMemberRole(teamId: string, memberId: string, role: WorkspaceTeamRole) {
    const accessToken = requireAccessToken()

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      const member = await updateWorkspaceTeamMember(accessToken, teamId, memberId, role)
      mergeTeamMember(teamId, member)
      apiState.value = 'live'
      return member
    } catch (error) {
      errorMessage.value = '成员角色更新失败，请检查管理权限'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function removeTeamMember(teamId: string, memberId: string) {
    const accessToken = requireAccessToken()

    teamOperationLoading.value = true
    errorMessage.value = ''
    try {
      await removeWorkspaceTeamMember(accessToken, teamId, memberId)
      if (activeTeamDetail.value?.id === teamId) {
        activeTeamDetail.value = {
          ...activeTeamDetail.value,
          member_count: Math.max(0, activeTeamDetail.value.member_count - 1),
          members: activeTeamDetail.value.members.filter((member) => member.id !== memberId),
        }
        upsertTeamSummary(teamDetailToSummary(activeTeamDetail.value))
      }
      apiState.value = 'live'
    } catch (error) {
      errorMessage.value = '成员移除失败，请检查管理权限'
      throw error
    } finally {
      teamOperationLoading.value = false
    }
  }

  async function restoreFileVersion(fileId: string, versionId: string) {
    const accessToken = requireAccessToken()

    restoringVersionId.value = versionId
    errorMessage.value = ''
    try {
      const restored = await restoreWorkspaceFileVersion(accessToken, fileId, versionId)
      replaceFileInSnapshot(restored, true)
      apiState.value = 'live'
      return restored
    } catch (error) {
      errorMessage.value = '文件版本回滚失败，请稍后重试'
      throw error
    } finally {
      restoringVersionId.value = null
    }
  }

  async function createFolder(payload: WorkspaceFolderCreateInput) {
    const accessToken = requireAccessToken()
    const parent = findFolderById(folders.value, payload.parentId ?? activeFolderId.value)
    const nextPayload: WorkspaceFolderCreateInput = {
      name: payload.name.trim(),
      parentId: payload.parentId ?? parent?.id ?? activeFolderId.value,
      scope: payload.scope ?? parent?.scope ?? 'personal',
    }

    creatingFolder.value = true
    errorMessage.value = ''
    try {
      const created = await createWorkspaceFolder(accessToken, nextPayload)
      folders.value = addFolderToTree(removeFolderFromTree(folders.value, created.id).items, created)
      activeFolderId.value = created.id
      apiState.value = 'live'
      return created
    } catch (error) {
      errorMessage.value = '文件夹创建失败，请检查名称和权限后重试'
      throw error
    } finally {
      creatingFolder.value = false
    }
  }

  async function updateFolder(folderId: string, payload: WorkspaceFolderUpdateInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceFolderUpdateInput = {}
    if ('name' in payload) {
      nextPayload.name = payload.name?.trim() || null
    }
    if ('parentId' in payload) {
      nextPayload.parentId = payload.parentId ?? null
    }

    updatingFolderId.value = folderId
    errorMessage.value = ''
    try {
      const updated = await updateWorkspaceFolder(accessToken, folderId, nextPayload)
      folders.value = upsertFolderInTree(folders.value, updated)
      activeFolderId.value = updated.id
      apiState.value = 'live'
      return updated
    } catch (error) {
      errorMessage.value = '文件夹更新失败，请检查移动目标和权限后重试'
      throw error
    } finally {
      updatingFolderId.value = null
    }
  }

  async function deleteFolder(folderId: string) {
    const accessToken = requireAccessToken()
    const target = findFolderById(folders.value, folderId)
    const fallbackFolderId = target?.parent_id ?? findFirstFolderId(folders.value)

    deletingFolderId.value = folderId
    errorMessage.value = ''
    try {
      await deleteWorkspaceFolder(accessToken, folderId)
      const removal = removeFolderFromTree(folders.value, folderId)
      folders.value = removal.items
      if (!findFolderById(folders.value, activeFolderId.value)) {
        activeFolderId.value = findFolderById(folders.value, fallbackFolderId)?.id ?? findFirstFolderId(folders.value)
      }
      apiState.value = 'live'
    } catch (error) {
      errorMessage.value = '文件夹删除失败，请先清空目录内容后重试'
      throw error
    } finally {
      deletingFolderId.value = null
    }
  }

  function selectFolder(folderId: string) {
    if (findFolderById(folders.value, folderId)) {
      activeFolderId.value = folderId
    }
  }

  function resolveOptionalAccessToken(token?: string) {
    const auth = useAuthStore()
    return token ?? auth.session?.accessToken ?? resolveWorkspaceToken()
  }

  function requireAccessToken(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)
    if (!accessToken) {
      errorMessage.value = '请先登录后再执行文件操作'
      throw new Error(errorMessage.value)
    }
    return accessToken
  }

  function removeFileFromSnapshot(fileId: string) {
    const removedFile = snapshot.value.files.find((file) => file.id === fileId)
    if (!removedFile) {
      return
    }

    snapshot.value = {
      ...snapshot.value,
      files: snapshot.value.files.filter((file) => file.id !== fileId),
      summary: {
        ...snapshot.value.summary,
        file_count: Math.max(0, snapshot.value.summary.file_count - 1),
        indexed_count:
          removedFile.parse_status === 'indexed'
            ? Math.max(0, snapshot.value.summary.indexed_count - 1)
            : snapshot.value.summary.indexed_count,
      },
    }
  }

  function removeFileVersions(fileId: string) {
    const { [fileId]: _removed, ...remaining } = fileVersionsById.value
    fileVersionsById.value = remaining
  }

  function replaceFileInSnapshot(updated: WorkspaceFile, moveToFront = false) {
    const existed = snapshot.value.files.some((file) => file.id === updated.id)
    const nextFiles = moveToFront
      ? [updated, ...snapshot.value.files.filter((file) => file.id !== updated.id)]
      : snapshot.value.files.map((file) => (file.id === updated.id ? updated : file))

    snapshot.value = {
      ...snapshot.value,
      files: existed ? nextFiles : [updated, ...snapshot.value.files],
      summary: {
        ...snapshot.value.summary,
        file_count: existed ? snapshot.value.summary.file_count : snapshot.value.summary.file_count + 1,
        indexed_count: nextFiles.filter((file) => file.parse_status === 'indexed').length,
      },
    }
  }

  function insertFileIntoSnapshot(uploaded: WorkspaceFile) {
    const existed = snapshot.value.files.some((file) => file.id === uploaded.id)
    const nextFiles = [uploaded, ...snapshot.value.files.filter((file) => file.id !== uploaded.id)]

    snapshot.value = {
      ...snapshot.value,
      files: nextFiles,
      summary: {
        ...snapshot.value.summary,
        file_count: existed ? snapshot.value.summary.file_count : snapshot.value.summary.file_count + 1,
        indexed_count: nextFiles.filter((file) => file.parse_status === 'indexed').length,
      },
    }
  }

  function normalizeFileFilters(filters: Partial<WorkspaceFileFilters>): WorkspaceFileFilters {
    return {
      fileType: filters.fileType?.trim() ?? '',
      query: filters.query?.trim() ?? '',
      tag: filters.tag?.trim() ?? '',
    }
  }

  function normalizeFileUpdatePayload(payload: WorkspaceFileUpdateInput): WorkspaceFileUpdateInput {
    const nextPayload: WorkspaceFileUpdateInput = {}
    if ('name' in payload) {
      nextPayload.name = payload.name?.trim() || null
    }
    if ('folderId' in payload) {
      nextPayload.folderId = payload.folderId ?? null
    }
    if ('tags' in payload) {
      nextPayload.tags = payload.tags ? normalizeTags(payload.tags) : null
    }
    return nextPayload
  }

  function normalizeTags(tags: string[]): string[] {
    return tags.map((tag) => tag.trim()).filter(Boolean)
  }

  function resetFoldersToDemo() {
    folders.value = cloneFolderTree(demoWorkspaceFolders.items)
    ensureActiveFolderSelection()
  }

  function resetVersionsToDemo() {
    fileVersionsById.value = cloneVersionMap(demoWorkspaceFileVersions)
  }

  function ensureActiveFolderSelection() {
    if (!findFolderById(folders.value, activeFolderId.value)) {
      activeFolderId.value = findFirstFolderId(folders.value)
    }
  }

  function upsertTeamSummary(teamSummary: TeamSummary, moveToFront = false) {
    const existing = snapshot.value.teams.some((team) => team.id === teamSummary.id)
    const nextTeams = moveToFront
      ? [teamSummary, ...snapshot.value.teams.filter((team) => team.id !== teamSummary.id)]
      : existing
        ? snapshot.value.teams.map((team) => (team.id === teamSummary.id ? teamSummary : team))
        : [teamSummary, ...snapshot.value.teams]

    snapshot.value = {
      ...snapshot.value,
      teams: nextTeams,
      summary: {
        ...snapshot.value.summary,
        unread_notifications: nextTeams.reduce((sum, team) => sum + team.unread_count, 0),
      },
    }
  }

  function mergeTeamMember(teamId: string, member: WorkspaceTeamMember) {
    if (activeTeamDetail.value?.id !== teamId) {
      return
    }

    const existed = activeTeamDetail.value.members.some((item) => item.id === member.id)
    const nextMembers = existed
      ? activeTeamDetail.value.members.map((item) => (item.id === member.id ? member : item))
      : [member, ...activeTeamDetail.value.members]
    const nextDetail = {
      ...activeTeamDetail.value,
      member_count: nextMembers.length,
      members: nextMembers,
    }

    activeTeamDetail.value = nextDetail
    upsertTeamSummary(teamDetailToSummary(nextDetail))
  }

  return {
    activeTeamDetail,
    activeBreadcrumbs,
    activeFolderId,
    apiState,
    auditLogs,
    copyFile,
    copyingFileId,
    createFolder,
    creatingFolder,
    deleteFolder,
    deleteFile,
    deletingFolderId,
    deletingFileId,
    downloadFile,
    downloadingFileId,
    errorMessage,
    fileFilters,
    fileListLoading,
    fileVersionsById,
    files,
    folderOptions,
    folders,
    folderTreeLoading,
    indexedFiles,
    loadFolders,
    loadFileVersions,
    loadTeamDetail,
    loadTeams,
    loadWorkspace,
    loading,
    narrative,
    resetFileFilters,
    restoreFileVersion,
    restoringVersionId,
    searchFiles,
    selectFolder,
    summary,
    teams,
    createTeam,
    inviteTeamMember,
    joinTeam,
    removeTeamMember,
    teamOperationLoading,
    tools,
    updateTeamMemberRole,
    updateFile,
    updateFolder,
    updatingFileId,
    updatingFolderId,
    uploadFile,
    uploadingFile,
    versionFileId,
    workflows,
  }
})

function cloneFolderTree(folders: WorkspaceFolder[]): WorkspaceFolder[] {
  return folders.map(cloneFolder)
}

function cloneFolder(folder: WorkspaceFolder): WorkspaceFolder {
  return {
    ...folder,
    children: cloneFolderTree(folder.children ?? []),
  }
}

function cloneVersionMap(versions: Record<string, WorkspaceFileVersion[]>): Record<string, WorkspaceFileVersion[]> {
  return Object.fromEntries(
    Object.entries(versions).map(([fileId, items]) => [
      fileId,
      items.map((item) => ({ ...item })),
    ]),
  )
}

function flattenFolderOptions(folders: WorkspaceFolder[]): WorkspaceFolderOption[] {
  const options: WorkspaceFolderOption[] = []
  collectFolderOptions(folders, [], options)
  return options
}

function collectFolderOptions(folders: WorkspaceFolder[], parents: string[], options: WorkspaceFolderOption[]) {
  for (const folder of folders) {
    const path = [...parents, folder.name]
    options.push({ label: path.join(' / '), value: folder.id })
    collectFolderOptions(folder.children ?? [], path, options)
  }
}

function buildFolderBreadcrumbs(folders: WorkspaceFolder[], folderId: string | null): WorkspaceFolder[] {
  if (!folderId) {
    return []
  }

  for (const folder of folders) {
    if (folder.id === folderId) {
      return [folder]
    }
    const childPath = buildFolderBreadcrumbs(folder.children ?? [], folderId)
    if (childPath.length) {
      return [folder, ...childPath]
    }
  }
  return []
}

function findFolderById(folders: WorkspaceFolder[], folderId: string | null | undefined): WorkspaceFolder | null {
  if (!folderId) {
    return null
  }

  for (const folder of folders) {
    if (folder.id === folderId) {
      return folder
    }
    const child = findFolderById(folder.children ?? [], folderId)
    if (child) {
      return child
    }
  }
  return null
}

function findFirstFolderId(folders: WorkspaceFolder[]): string | null {
  return folders[0]?.id ?? null
}

function addFolderToTree(folders: WorkspaceFolder[], folder: WorkspaceFolder): WorkspaceFolder[] {
  const normalizedFolder = cloneFolder(folder)
  if (!normalizedFolder.parent_id) {
    return [...cloneFolderTree(folders), normalizedFolder]
  }

  const result = addFolderToTreeWithStatus(folders, normalizedFolder)
  return result.inserted ? result.items : [...result.items, normalizedFolder]
}

function addFolderToTreeWithStatus(
  folders: WorkspaceFolder[],
  folder: WorkspaceFolder,
): { items: WorkspaceFolder[]; inserted: boolean } {
  let insertedInTree = false
  const items = folders.map((candidate) => {
    let nextChildren = cloneFolderTree(candidate.children ?? [])
    if (candidate.id === folder.parent_id) {
      insertedInTree = true
      nextChildren = [...nextChildren, folder]
    } else {
      const childResult = addFolderToTreeWithStatus(candidate.children ?? [], folder)
      if (childResult.inserted) {
        insertedInTree = true
        nextChildren = childResult.items
      }
    }
    return {
      ...candidate,
      children: nextChildren,
    }
  })

  return { items, inserted: insertedInTree }
}

function upsertFolderInTree(folders: WorkspaceFolder[], folder: WorkspaceFolder): WorkspaceFolder[] {
  const existingFolder = findFolderById(folders, folder.id)
  const nextFolder = {
    ...folder,
    children: folder.children?.length ? folder.children : existingFolder?.children ?? [],
  }
  return addFolderToTree(removeFolderFromTree(folders, folder.id).items, nextFolder)
}

function removeFolderFromTree(
  folders: WorkspaceFolder[],
  folderId: string,
): { items: WorkspaceFolder[]; removed: WorkspaceFolder | null } {
  let removed: WorkspaceFolder | null = null
  const items = folders.flatMap((folder) => {
    if (folder.id === folderId) {
      removed = cloneFolder(folder)
      return []
    }

    const childRemoval = removeFolderFromTree(folder.children ?? [], folderId)
    if (childRemoval.removed) {
      removed = childRemoval.removed
    }
    return [
      {
        ...folder,
        children: childRemoval.items,
      },
    ]
  })

  return { items, removed }
}

function teamDetailToSummary(detail: WorkspaceTeamDetail): TeamSummary {
  return {
    description: detail.description,
    id: detail.id,
    member_count: detail.member_count,
    name: detail.name,
    role: detail.role,
    root_folder_id: detail.root_folder.id,
    unread_count: detail.unread_count,
  }
}
