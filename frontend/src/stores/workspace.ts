import { computed, shallowRef } from 'vue'
import { defineStore } from 'pinia'

import { resolveWorkspaceToken } from '@/auth'
import {
  addKnowledgeDocument,
  askWorkspaceQuestion,
  copyWorkspaceFile,
  createWorkspaceFileAnnotation,
  createKnowledgeBase,
  createWorkspaceFileShareLink,
  createWorkspacePermissionRule,
  createWorkspaceWorkflow,
  createWorkspaceTeam,
  createWorkspaceFolder,
  demoWorkspaceFileVersions,
  demoWorkspaceKnowledgeBases,
  demoWorkspaceKnowledgeDocuments,
  demoWorkspaceNarrative,
  demoWorkspacePermissionRules,
  demoWorkspaceTeamMessages,
  demoWorkspaceFolders,
  demoWorkspaceSnapshot,
  demoWorkspaceTeamDetail,
  deleteWorkspacePermissionRule,
  deleteWorkspaceFile,
  deleteWorkspaceFileAnnotation,
  deleteWorkspaceFolder,
  downloadWorkspaceFile,
  executeWorkspaceWorkflow,
  fetchWorkspaceSnapshot,
  createWorkspaceTeamInvite,
  joinWorkspaceTeam,
  listKnowledgeBases,
  listKnowledgeDocuments,
  listWorkspaceTeamMessages,
  listWorkspaceTeams,
  listWorkspaceFileVersions,
  listWorkspaceFileAnnotations,
  listWorkspaceNotifications,
  listWorkspacePermissionRules,
  listWorkspaceRecycleBin,
  listWorkspaceFolders,
  listWorkspaceFiles,
  loadWorkspaceTeamDetail,
  markWorkspaceNotificationRead,
  publishWorkspaceWorkflow,
  removeWorkspaceTeamMember,
  replyWorkspaceFileAnnotation,
  restoreWorkspaceDeletedFile,
  restoreWorkspaceFileVersion,
  sendWorkspaceTeamMessage,
  updateWorkspaceTeamMember,
  updateWorkspaceFile,
  updateWorkspaceFolder,
  updateWorkspaceWorkflow,
  uploadWorkspaceMultipartFile,
  uploadWorkspaceFile,
  validateWorkspaceWorkflow,
  type AgentStep,
  type WorkspaceFile,
  type WorkspaceFileAnnotation,
  type WorkspaceFileAnnotationCreateInput,
  type WorkspaceFileAnnotationReplyInput,
  type WorkspaceFileCopyInput,
  type WorkspaceFileFilters,
  type WorkspaceFileUpdateInput,
  type WorkspaceFileUploadInput,
  type WorkspaceShareLink,
  type WorkspaceShareLinkCreateInput,
  type WorkspaceMultipartUploadInput,
  type WorkspaceFileVersion,
  type WorkspaceFolder,
  type WorkspaceFolderCreateInput,
  type WorkspaceFolderOption,
  type WorkspaceFolderUpdateInput,
  type WorkspaceKnowledgeBase,
  type WorkspaceKnowledgeBaseCreateInput,
  type WorkspaceKnowledgeDocument,
  type WorkspaceNarrative,
  type WorkspaceNotification,
  type WorkspacePermissionRule,
  type WorkspacePermissionRuleCreateInput,
  type WorkspaceQuestionInput,
  type WorkspaceRecycleBinItem,
  type WorkspaceSnapshot,
  type TeamSummary,
  type WorkspaceTeamCreateInput,
  type WorkspaceTeamDetail,
  type WorkspaceTeamInviteInput,
  type WorkspaceTeamMember,
  type WorkspaceTeamMessage,
  type WorkspaceTeamMessageCreateInput,
  type WorkspaceTeamRole,
  type WorkspaceWorkflow,
  type WorkspaceWorkflowCreateInput,
  type WorkspaceWorkflowExecuteInput,
  type WorkspaceWorkflowExecution,
  type WorkspaceWorkflowUpdateInput,
  type WorkspaceWorkflowValidation,
} from '@/client/workspace'
import { useAuthStore } from '@/stores/auth'

export type WorkspaceApiState = 'demo' | 'live' | 'fallback'

const emptyFileFilters: WorkspaceFileFilters = {
  fileType: '',
  query: '',
  tag: '',
  updatedFrom: '',
  updatedTo: '',
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const snapshot = shallowRef<WorkspaceSnapshot>(demoWorkspaceSnapshot)
  const folders = shallowRef<WorkspaceFolder[]>(cloneFolderTree(demoWorkspaceFolders.items))
  const fileVersionsById = shallowRef<Record<string, WorkspaceFileVersion[]>>(cloneVersionMap(demoWorkspaceFileVersions))
  const fileAnnotationsById = shallowRef<Record<string, WorkspaceFileAnnotation[]>>({})
  const notifications = shallowRef<WorkspaceNotification[]>([])
  const teamMessagesById = shallowRef<Record<string, WorkspaceTeamMessage[]>>(cloneTeamMessageMap(demoWorkspaceTeamMessages))
  const knowledgeBases = shallowRef<WorkspaceKnowledgeBase[]>(cloneKnowledgeBases(demoWorkspaceKnowledgeBases))
  const activeKnowledgeBaseId = shallowRef<string | null>(demoWorkspaceKnowledgeBases[0]?.id ?? null)
  const knowledgeDocumentsByKbId = shallowRef<Record<string, WorkspaceKnowledgeDocument[]>>(
    cloneKnowledgeDocumentMap(demoWorkspaceKnowledgeDocuments),
  )
  const narrative = shallowRef<WorkspaceNarrative>(demoWorkspaceNarrative)
  const activeTeamDetail = shallowRef<WorkspaceTeamDetail | null>(demoWorkspaceTeamDetail)
  const permissionRules = shallowRef<WorkspacePermissionRule[]>(clonePermissionRules(demoWorkspacePermissionRules))
  const recycleBinItems = shallowRef<WorkspaceRecycleBinItem[]>([])
  const activeWorkflowId = shallowRef<string | null>(demoWorkspaceSnapshot.workflows[0]?.id ?? null)
  const activeWorkflowValidation = shallowRef<WorkspaceWorkflowValidation | null>(null)
  const activeWorkflowExecution = shallowRef<WorkspaceWorkflowExecution | null>(null)
  const loading = shallowRef(false)
  const folderTreeLoading = shallowRef(false)
  const activeFolderId = shallowRef<string | null>('personal-root')
  const creatingFolder = shallowRef(false)
  const updatingFolderId = shallowRef<string | null>(null)
  const deletingFolderId = shallowRef<string | null>(null)
  const deletingFileId = shallowRef<string | null>(null)
  const downloadingFileId = shallowRef<string | null>(null)
  const sharingFileId = shallowRef<string | null>(null)
  const updatingFileId = shallowRef<string | null>(null)
  const copyingFileId = shallowRef<string | null>(null)
  const versionFileId = shallowRef<string | null>(null)
  const restoringVersionId = shallowRef<string | null>(null)
  const annotationFileIdLoading = shallowRef<string | null>(null)
  const annotationSaving = shallowRef(false)
  const deletingAnnotationId = shallowRef<string | null>(null)
  const notificationsLoading = shallowRef(false)
  const markingNotificationId = shallowRef<string | null>(null)
  const teamMessageTeamIdLoading = shallowRef<string | null>(null)
  const teamMessageSending = shallowRef(false)
  const recycleBinLoading = shallowRef(false)
  const restoringDeletedFileId = shallowRef<string | null>(null)
  const fileFilters = shallowRef<WorkspaceFileFilters>({ ...emptyFileFilters })
  const fileListLoading = shallowRef(false)
  const uploadingFile = shallowRef(false)
  const knowledgeOperationLoading = shallowRef(false)
  const addingKnowledgeDocument = shallowRef(false)
  const askingQuestion = shallowRef(false)
  const teamOperationLoading = shallowRef(false)
  const permissionRulesLoading = shallowRef(false)
  const permissionRuleSaving = shallowRef(false)
  const deletingPermissionRuleId = shallowRef<string | null>(null)
  const workflowOperationLoading = shallowRef(false)
  const errorMessage = shallowRef('')
  const apiState = shallowRef<WorkspaceApiState>('demo')

  const files = computed(() => snapshot.value.files)
  const indexedFiles = computed(() => snapshot.value.files.filter((file) => file.parse_status === 'indexed'))
  const tools = computed(() => snapshot.value.tools)
  const workflows = computed(() => snapshot.value.workflows)
  const teams = computed(() => snapshot.value.teams)
  const auditLogs = computed(() => snapshot.value.audit_logs)
  const summary = computed(() => snapshot.value.summary)
  const activeWorkflow = computed(
    () => snapshot.value.workflows.find((workflow) => workflow.id === activeWorkflowId.value) ?? null,
  )
  const folderOptions = computed(() => flattenFolderOptions(folders.value))
  const activeBreadcrumbs = computed(() => buildFolderBreadcrumbs(folders.value, activeFolderId.value))
  const activeKnowledgeBase = computed(
    () => knowledgeBases.value.find((knowledgeBase) => knowledgeBase.id === activeKnowledgeBaseId.value) ?? null,
  )
  const activeKnowledgeDocuments = computed(() =>
    activeKnowledgeBaseId.value ? knowledgeDocumentsByKbId.value[activeKnowledgeBaseId.value] ?? [] : [],
  )

  async function loadWorkspace(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      apiState.value = 'demo'
      fileFilters.value = { ...emptyFileFilters }
      resetFoldersToDemo()
      resetVersionsToDemo()
      resetAnnotations()
      resetNotifications()
      resetTeamMessagesToDemo()
      resetKnowledgeToDemo()
      resetPermissionRulesToDemo()
      resetRecycleBinToDemo()
      snapshot.value = demoWorkspaceSnapshot
      narrative.value = demoWorkspaceNarrative
      activeTeamDetail.value = demoWorkspaceTeamDetail
      activeWorkflowValidation.value = null
      activeWorkflowExecution.value = null
      ensureActiveWorkflowSelection()
      return
    }

    loading.value = true
    try {
      const [nextSnapshot, folderTree, ruleList, recycleBin, notificationList] = await Promise.all([
        fetchWorkspaceSnapshot(accessToken),
        listWorkspaceFolders(accessToken),
        listWorkspacePermissionRules(accessToken),
        listWorkspaceRecycleBin(accessToken),
        listWorkspaceNotifications(accessToken),
      ])
      snapshot.value = nextSnapshot
      folders.value = cloneFolderTree(folderTree.items)
      permissionRules.value = clonePermissionRules(ruleList.items)
      recycleBinItems.value = cloneRecycleBinItems(recycleBin.items)
      notifications.value = [...notificationList.items]
      syncUnreadNotificationSummary(notificationList.unread_count)
      fileVersionsById.value = {}
      resetAnnotations()
      teamMessagesById.value = {}
      await loadKnowledgeBases(accessToken)
      activeTeamDetail.value = null
      ensureActiveFolderSelection()
      ensureActiveWorkflowSelection()
      narrative.value = demoWorkspaceNarrative
      activeWorkflowValidation.value = null
      activeWorkflowExecution.value = null
      fileFilters.value = { ...emptyFileFilters }
      apiState.value = 'live'
    } catch {
      snapshot.value = demoWorkspaceSnapshot
      narrative.value = demoWorkspaceNarrative
      resetFoldersToDemo()
      resetVersionsToDemo()
      resetAnnotations()
      resetNotifications()
      resetTeamMessagesToDemo()
      resetKnowledgeToDemo()
      resetPermissionRulesToDemo()
      resetRecycleBinToDemo()
      activeTeamDetail.value = demoWorkspaceTeamDetail
      activeWorkflowValidation.value = null
      activeWorkflowExecution.value = null
      ensureActiveWorkflowSelection()
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

  async function loadKnowledgeBases(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      resetKnowledgeToDemo()
      return { items: knowledgeBases.value }
    }

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listKnowledgeBases(accessToken)
      knowledgeBases.value = cloneKnowledgeBases(response.items)
      ensureActiveKnowledgeBaseSelection()
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '知识库列表加载失败，请稍后重试'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function createKnowledgeBaseAction(payload: WorkspaceKnowledgeBaseCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceKnowledgeBaseCreateInput = {
      description: payload.description?.trim() || null,
      name: payload.name.trim(),
    }

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const created = await createKnowledgeBase(accessToken, nextPayload)
      upsertKnowledgeBase(created, true)
      activeKnowledgeBaseId.value = created.id
      knowledgeDocumentsByKbId.value = {
        ...knowledgeDocumentsByKbId.value,
        [created.id]: knowledgeDocumentsByKbId.value[created.id] ?? [],
      }
      apiState.value = 'live'
      return created
    } catch (error) {
      errorMessage.value = '知识库创建失败，请检查名称后重试'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function loadKnowledgeDocuments(kbId: string, token?: string) {
    const accessToken = requireAccessToken(token)

    knowledgeOperationLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listKnowledgeDocuments(accessToken, kbId)
      knowledgeDocumentsByKbId.value = {
        ...knowledgeDocumentsByKbId.value,
        [kbId]: response.items,
      }
      activeKnowledgeBaseId.value = kbId
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '知识库文档加载失败，请稍后重试'
      throw error
    } finally {
      knowledgeOperationLoading.value = false
    }
  }

  async function addKnowledgeDocumentAction(kbId: string, fileId: string) {
    const accessToken = requireAccessToken()

    addingKnowledgeDocument.value = true
    errorMessage.value = ''
    try {
      const document = await addKnowledgeDocument(accessToken, kbId, fileId)
      upsertKnowledgeDocument(kbId, document)
      markFileIndexedInKnowledgeBase(fileId, kbId)
      activeKnowledgeBaseId.value = kbId
      apiState.value = 'live'
      return document
    } catch (error) {
      errorMessage.value = '文档入库失败，请检查文件解析状态和权限'
      throw error
    } finally {
      addingKnowledgeDocument.value = false
    }
  }

  async function askKnowledgeQuestion(payload: WorkspaceQuestionInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceQuestionInput = {
      conversationId: payload.conversationId ?? null,
      kbId: payload.kbId,
      question: payload.question.trim(),
      topK: payload.topK ?? 5,
    }

    askingQuestion.value = true
    errorMessage.value = ''
    try {
      const response = await askWorkspaceQuestion(accessToken, nextPayload)
      narrative.value = {
        ...narrative.value,
        answer: response.answer,
        citations: response.citations,
      }
      activeKnowledgeBaseId.value = payload.kbId
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '知识库问答失败，请稍后重试'
      throw error
    } finally {
      askingQuestion.value = false
    }
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

  async function uploadLargeFile(payload: WorkspaceMultipartUploadInput) {
    const accessToken = requireAccessToken()

    uploadingFile.value = true
    errorMessage.value = ''
    try {
      const uploaded = await uploadWorkspaceMultipartFile(accessToken, payload)
      fileFilters.value = { ...emptyFileFilters }
      insertFileIntoSnapshot(uploaded)
      apiState.value = 'live'
      return uploaded
    } catch (error) {
      errorMessage.value = '分片上传失败，请检查文件完整性和目录权限后重试'
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

  async function createFileShareLink(
    fileId: string,
    payload: WorkspaceShareLinkCreateInput,
  ): Promise<WorkspaceShareLink> {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceShareLinkCreateInput = {
      downloadLimit: payload.downloadLimit ?? null,
      expiresInSeconds: payload.expiresInSeconds ?? 3600,
      password: payload.password?.trim() || null,
    }

    sharingFileId.value = fileId
    errorMessage.value = ''
    try {
      const shareLink = await createWorkspaceFileShareLink(accessToken, fileId, nextPayload)
      apiState.value = 'live'
      return shareLink
    } catch (error) {
      errorMessage.value = '分享链接创建失败，请检查权限和有效期'
      throw error
    } finally {
      sharingFileId.value = null
    }
  }

  async function loadFileAnnotations(fileId: string) {
    const accessToken = requireAccessToken()

    annotationFileIdLoading.value = fileId
    errorMessage.value = ''
    try {
      const response = await listWorkspaceFileAnnotations(accessToken, fileId)
      fileAnnotationsById.value = {
        ...fileAnnotationsById.value,
        [fileId]: response.items,
      }
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '文件批注加载失败，请稍后重试'
      throw error
    } finally {
      annotationFileIdLoading.value = null
    }
  }

  async function createFileAnnotation(fileId: string, payload: WorkspaceFileAnnotationCreateInput) {
    const accessToken = requireAccessToken()
    const content = payload.content.trim()

    annotationSaving.value = true
    errorMessage.value = ''
    try {
      const annotation = await createWorkspaceFileAnnotation(accessToken, fileId, {
        content,
        position: payload.position ?? null,
      })
      upsertFileAnnotation(fileId, annotation, true)
      apiState.value = 'live'
      return annotation
    } catch (error) {
      errorMessage.value = '文件批注创建失败，请检查权限后重试'
      throw error
    } finally {
      annotationSaving.value = false
    }
  }

  async function replyFileAnnotation(annotationId: string, payload: WorkspaceFileAnnotationReplyInput) {
    const accessToken = requireAccessToken()
    const content = payload.content.trim()

    annotationSaving.value = true
    errorMessage.value = ''
    try {
      const reply = await replyWorkspaceFileAnnotation(accessToken, annotationId, { content })
      insertFileAnnotationReply(reply.file_id, annotationId, reply)
      apiState.value = 'live'
      return reply
    } catch (error) {
      errorMessage.value = '批注回复失败，请检查权限后重试'
      throw error
    } finally {
      annotationSaving.value = false
    }
  }

  async function deleteFileAnnotation(fileId: string, annotationId: string) {
    const accessToken = requireAccessToken()

    deletingAnnotationId.value = annotationId
    errorMessage.value = ''
    try {
      await deleteWorkspaceFileAnnotation(accessToken, fileId, annotationId)
      removeFileAnnotation(fileId, annotationId)
      apiState.value = 'live'
    } catch (error) {
      errorMessage.value = '批注删除失败，请检查权限后重试'
      throw error
    } finally {
      deletingAnnotationId.value = null
    }
  }

  async function loadNotifications(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      resetNotifications()
      return { items: notifications.value, total: 0, unread_count: 0 }
    }

    notificationsLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspaceNotifications(accessToken)
      notifications.value = [...response.items]
      syncUnreadNotificationSummary(response.unread_count)
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '通知列表加载失败，请稍后重试'
      throw error
    } finally {
      notificationsLoading.value = false
    }
  }

  async function markNotificationRead(notificationId: string, token?: string) {
    const accessToken = requireAccessToken(token)
    markingNotificationId.value = notificationId
    errorMessage.value = ''
    try {
      const notification = await markWorkspaceNotificationRead(accessToken, notificationId)
      upsertNotification(notification)
      syncUnreadNotificationSummary(notifications.value.filter((item) => !item.is_read).length)
      apiState.value = 'live'
      return notification
    } catch (error) {
      errorMessage.value = '通知状态更新失败，请稍后重试'
      throw error
    } finally {
      markingNotificationId.value = null
    }
  }

  async function loadTeamMessages(teamId: string, token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      const messages = demoWorkspaceTeamMessages[teamId] ?? teamMessagesById.value[teamId] ?? []
      teamMessagesById.value = {
        ...teamMessagesById.value,
        [teamId]: messages.map((message) => ({ ...message })),
      }
      return { items: teamMessagesById.value[teamId] ?? [], total: teamMessagesById.value[teamId]?.length ?? 0 }
    }

    teamMessageTeamIdLoading.value = teamId
    errorMessage.value = ''
    try {
      const response = await listWorkspaceTeamMessages(accessToken, teamId)
      teamMessagesById.value = {
        ...teamMessagesById.value,
        [teamId]: [...response.items],
      }
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '团队聊天记录加载失败，请检查权限后重试'
      throw error
    } finally {
      teamMessageTeamIdLoading.value = null
    }
  }

  async function sendTeamMessage(teamId: string, payload: WorkspaceTeamMessageCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceTeamMessageCreateInput = {
      content: payload.content.trim(),
      message_type: payload.message_type ?? 'text',
      receiver_id: payload.receiver_id ?? null,
    }
    if (!nextPayload.content) {
      return null
    }

    teamMessageSending.value = true
    errorMessage.value = ''
    try {
      const message = await sendWorkspaceTeamMessage(accessToken, teamId, nextPayload)
      upsertTeamMessage(teamId, message)
      apiState.value = 'live'
      return message
    } catch (error) {
      errorMessage.value = '团队消息发送失败，请检查频道权限后重试'
      throw error
    } finally {
      teamMessageSending.value = false
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

  async function loadRecycleBin(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      resetRecycleBinToDemo()
      return { items: recycleBinItems.value, total: recycleBinItems.value.length }
    }

    recycleBinLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspaceRecycleBin(accessToken)
      recycleBinItems.value = cloneRecycleBinItems(response.items)
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '回收站加载失败，请稍后重试'
      throw error
    } finally {
      recycleBinLoading.value = false
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

  async function loadPermissionRules(token?: string) {
    const accessToken = resolveOptionalAccessToken(token)

    if (!accessToken) {
      resetPermissionRulesToDemo()
      return { items: permissionRules.value }
    }

    permissionRulesLoading.value = true
    errorMessage.value = ''
    try {
      const response = await listWorkspacePermissionRules(accessToken)
      permissionRules.value = clonePermissionRules(response.items)
      apiState.value = 'live'
      return response
    } catch (error) {
      errorMessage.value = '权限规则加载失败，请稍后重试'
      throw error
    } finally {
      permissionRulesLoading.value = false
    }
  }

  async function createPermissionRule(payload: WorkspacePermissionRuleCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload = normalizePermissionRulePayload(payload)

    permissionRuleSaving.value = true
    errorMessage.value = ''
    try {
      const created = await createWorkspacePermissionRule(accessToken, nextPayload)
      upsertPermissionRule(created, true)
      apiState.value = 'live'
      return created
    } catch (error) {
      errorMessage.value = '权限规则保存失败，请检查主体、资源和管理权限'
      throw error
    } finally {
      permissionRuleSaving.value = false
    }
  }

  async function deletePermissionRule(ruleId: string) {
    const accessToken = requireAccessToken()

    deletingPermissionRuleId.value = ruleId
    errorMessage.value = ''
    try {
      await deleteWorkspacePermissionRule(accessToken, ruleId)
      permissionRules.value = permissionRules.value.filter((rule) => rule.id !== ruleId)
      apiState.value = 'live'
    } catch (error) {
      errorMessage.value = '权限规则删除失败，请检查管理权限'
      throw error
    } finally {
      deletingPermissionRuleId.value = null
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

  async function restoreDeletedFile(fileId: string) {
    const accessToken = requireAccessToken()

    restoringDeletedFileId.value = fileId
    errorMessage.value = ''
    try {
      const restored = await restoreWorkspaceDeletedFile(accessToken, fileId)
      replaceFileInSnapshot(restored, true)
      recycleBinItems.value = recycleBinItems.value.filter((item) => item.file.id !== fileId)
      apiState.value = 'live'
      return restored
    } catch (error) {
      errorMessage.value = '文件恢复失败，请检查权限后重试'
      throw error
    } finally {
      restoringDeletedFileId.value = null
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

  async function selectKnowledgeBase(kbId: string) {
    if (!knowledgeBases.value.some((knowledgeBase) => knowledgeBase.id === kbId)) {
      return
    }
    activeKnowledgeBaseId.value = kbId
    if (resolveOptionalAccessToken()) {
      await loadKnowledgeDocuments(kbId)
    }
  }

  function selectWorkflow(workflowId: string) {
    if (snapshot.value.workflows.some((workflow) => workflow.id === workflowId)) {
      activeWorkflowId.value = workflowId
    }
  }

  async function createWorkflow(payload: WorkspaceWorkflowCreateInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceWorkflowCreateInput = {
      description: payload.description?.trim() || null,
      edges: payload.edges ?? [],
      name: payload.name.trim(),
      nodes: payload.nodes ?? [],
      trigger: payload.trigger?.trim() || 'manual',
    }

    workflowOperationLoading.value = true
    errorMessage.value = ''
    try {
      const created = await createWorkspaceWorkflow(accessToken, nextPayload)
      upsertWorkflow(created, true)
      activeWorkflowId.value = created.id
      activeWorkflowValidation.value = null
      activeWorkflowExecution.value = null
      apiState.value = 'live'
      return created
    } catch (error) {
      errorMessage.value = '流程创建失败，请检查节点配置后重试'
      throw error
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function updateWorkflow(workflowId: string, payload: WorkspaceWorkflowUpdateInput) {
    const accessToken = requireAccessToken()
    const nextPayload: WorkspaceWorkflowUpdateInput = normalizeWorkflowUpdatePayload(payload)

    workflowOperationLoading.value = true
    errorMessage.value = ''
    try {
      const updated = await updateWorkspaceWorkflow(accessToken, workflowId, nextPayload)
      upsertWorkflow(updated)
      activeWorkflowId.value = updated.id
      activeWorkflowValidation.value = null
      apiState.value = 'live'
      return updated
    } catch (error) {
      errorMessage.value = '流程保存失败，请检查节点配置后重试'
      throw error
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function validateWorkflow(workflowId: string) {
    const accessToken = requireAccessToken()

    workflowOperationLoading.value = true
    errorMessage.value = ''
    try {
      const validation = await validateWorkspaceWorkflow(accessToken, workflowId)
      activeWorkflowId.value = workflowId
      activeWorkflowValidation.value = validation
      apiState.value = 'live'
      return validation
    } catch (error) {
      errorMessage.value = '流程校验失败，请稍后重试'
      throw error
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function publishWorkflow(workflowId: string) {
    const accessToken = requireAccessToken()

    workflowOperationLoading.value = true
    errorMessage.value = ''
    try {
      const published = await publishWorkspaceWorkflow(accessToken, workflowId)
      upsertWorkflow(published)
      activeWorkflowId.value = published.id
      apiState.value = 'live'
      return published
    } catch (error) {
      errorMessage.value = '流程发布失败，请先完成校验'
      throw error
    } finally {
      workflowOperationLoading.value = false
    }
  }

  async function executeWorkflow(workflowId: string, payload: WorkspaceWorkflowExecuteInput) {
    const accessToken = requireAccessToken()

    workflowOperationLoading.value = true
    errorMessage.value = ''
    try {
      const execution = await executeWorkspaceWorkflow(accessToken, workflowId, payload)
      activeWorkflowId.value = workflowId
      activeWorkflowExecution.value = execution
      narrative.value = {
        ...narrative.value,
        answer: extractWorkflowExecutionAnswer(execution) ?? narrative.value.answer,
        agentSteps: workflowExecutionToAgentSteps(execution),
      }
      apiState.value = 'live'
      return execution
    } catch (error) {
      errorMessage.value = '流程执行失败，请检查文件和知识库权限'
      throw error
    } finally {
      workflowOperationLoading.value = false
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
      updatedFrom: filters.updatedFrom?.trim() ?? '',
      updatedTo: filters.updatedTo?.trim() ?? '',
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

  function normalizeWorkflowUpdatePayload(payload: WorkspaceWorkflowUpdateInput): WorkspaceWorkflowUpdateInput {
    const nextPayload: WorkspaceWorkflowUpdateInput = {}
    if ('description' in payload) {
      nextPayload.description = payload.description?.trim() || null
    }
    if ('edges' in payload) {
      nextPayload.edges = payload.edges ?? null
    }
    if ('name' in payload) {
      nextPayload.name = payload.name?.trim() || null
    }
    if ('nodes' in payload) {
      nextPayload.nodes = payload.nodes ?? null
    }
    if ('trigger' in payload) {
      nextPayload.trigger = payload.trigger?.trim() || null
    }
    return nextPayload
  }

  function normalizePermissionRulePayload(payload: WorkspacePermissionRuleCreateInput): WorkspacePermissionRuleCreateInput {
    return {
      action: payload.action,
      effect: payload.effect,
      inherit: payload.inherit ?? false,
      resourceId: payload.resourceId.trim(),
      resourceType: payload.resourceType,
      subjectId: payload.subjectId.trim(),
      subjectType: payload.subjectType,
    }
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

  function resetAnnotations() {
    fileAnnotationsById.value = {}
  }

  function resetNotifications() {
    notifications.value = []
    syncUnreadNotificationSummary(0)
  }

  function resetTeamMessagesToDemo() {
    teamMessagesById.value = cloneTeamMessageMap(demoWorkspaceTeamMessages)
  }

  function resetKnowledgeToDemo() {
    knowledgeBases.value = cloneKnowledgeBases(demoWorkspaceKnowledgeBases)
    knowledgeDocumentsByKbId.value = cloneKnowledgeDocumentMap(demoWorkspaceKnowledgeDocuments)
    ensureActiveKnowledgeBaseSelection()
  }

  function resetPermissionRulesToDemo() {
    permissionRules.value = clonePermissionRules(demoWorkspacePermissionRules)
  }

  function resetRecycleBinToDemo() {
    recycleBinItems.value = []
  }

  function ensureActiveFolderSelection() {
    if (!findFolderById(folders.value, activeFolderId.value)) {
      activeFolderId.value = findFirstFolderId(folders.value)
    }
  }

  function ensureActiveKnowledgeBaseSelection() {
    if (!knowledgeBases.value.some((knowledgeBase) => knowledgeBase.id === activeKnowledgeBaseId.value)) {
      activeKnowledgeBaseId.value = knowledgeBases.value[0]?.id ?? null
    }
  }

  function ensureActiveWorkflowSelection() {
    if (!snapshot.value.workflows.some((workflow) => workflow.id === activeWorkflowId.value)) {
      activeWorkflowId.value = snapshot.value.workflows[0]?.id ?? null
    }
  }

  function upsertWorkflow(workflow: WorkspaceWorkflow, moveToFront = false) {
    const existing = snapshot.value.workflows.some((item) => item.id === workflow.id)
    const nextWorkflows = moveToFront
      ? [workflow, ...snapshot.value.workflows.filter((item) => item.id !== workflow.id)]
      : existing
        ? snapshot.value.workflows.map((item) => (item.id === workflow.id ? workflow : item))
        : [workflow, ...snapshot.value.workflows]

    snapshot.value = {
      ...snapshot.value,
      workflows: nextWorkflows,
    }
  }

  function upsertFileAnnotation(fileId: string, annotation: WorkspaceFileAnnotation, moveToFront = false) {
    const current = fileAnnotationsById.value[fileId] ?? []
    const exists = current.some((item) => item.id === annotation.id)
    fileAnnotationsById.value = {
      ...fileAnnotationsById.value,
      [fileId]: moveToFront
        ? [annotation, ...current.filter((item) => item.id !== annotation.id)]
        : exists
          ? current.map((item) => (item.id === annotation.id ? annotation : item))
          : [...current, annotation],
    }
  }

  function upsertNotification(notification: WorkspaceNotification) {
    const exists = notifications.value.some((item) => item.id === notification.id)
    notifications.value = exists
      ? notifications.value.map((item) => (item.id === notification.id ? notification : item))
      : [notification, ...notifications.value]
  }

  function upsertTeamMessage(teamId: string, message: WorkspaceTeamMessage) {
    const current = teamMessagesById.value[teamId] ?? []
    const exists = current.some((item) => item.id === message.id)
    teamMessagesById.value = {
      ...teamMessagesById.value,
      [teamId]: exists
        ? current.map((item) => (item.id === message.id ? message : item))
        : [...current, message],
    }
  }

  function syncUnreadNotificationSummary(unreadCount: number) {
    snapshot.value = {
      ...snapshot.value,
      summary: {
        ...snapshot.value.summary,
        unread_notifications: unreadCount,
      },
    }
  }

  function insertFileAnnotationReply(
    fileId: string,
    annotationId: string,
    reply: NonNullable<WorkspaceFileAnnotation['replies']>[number],
  ) {
    const current = fileAnnotationsById.value[fileId] ?? []
    fileAnnotationsById.value = {
      ...fileAnnotationsById.value,
      [fileId]: current.map((annotation) =>
        annotation.id === annotationId
          ? {
              ...annotation,
              replies: [
                ...(annotation.replies ?? []).filter((item) => item.id !== reply.id),
                reply,
              ],
            }
          : annotation,
      ),
    }
  }

  function removeFileAnnotation(fileId: string, annotationId: string) {
    const current = fileAnnotationsById.value[fileId] ?? []
    fileAnnotationsById.value = {
      ...fileAnnotationsById.value,
      [fileId]: current
        .filter((annotation) => annotation.id !== annotationId)
        .map((annotation) => ({
          ...annotation,
          replies: (annotation.replies ?? []).filter((reply) => reply.id !== annotationId),
        })),
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

  function upsertKnowledgeBase(knowledgeBase: WorkspaceKnowledgeBase, moveToFront = false) {
    const existing = knowledgeBases.value.some((item) => item.id === knowledgeBase.id)
    knowledgeBases.value = moveToFront
      ? [knowledgeBase, ...knowledgeBases.value.filter((item) => item.id !== knowledgeBase.id)]
      : existing
        ? knowledgeBases.value.map((item) => (item.id === knowledgeBase.id ? knowledgeBase : item))
        : [knowledgeBase, ...knowledgeBases.value]
    snapshot.value = {
      ...snapshot.value,
      summary: {
        ...snapshot.value.summary,
        knowledge_base_count: knowledgeBases.value.length,
      },
    }
  }

  function upsertKnowledgeDocument(kbId: string, document: WorkspaceKnowledgeDocument) {
    const currentDocuments = knowledgeDocumentsByKbId.value[kbId] ?? []
    const nextDocuments = [
      document,
      ...currentDocuments.filter((item) => item.id !== document.id),
    ]
    knowledgeDocumentsByKbId.value = {
      ...knowledgeDocumentsByKbId.value,
      [kbId]: nextDocuments,
    }
    const knowledgeBase = knowledgeBases.value.find((item) => item.id === kbId)
    if (knowledgeBase) {
      upsertKnowledgeBase({
        ...knowledgeBase,
        chunk_count: nextDocuments.reduce((sum, item) => sum + item.chunk_count, 0),
        document_count: nextDocuments.length,
        updated_at: document.updated_at,
      })
    }
  }

  function upsertPermissionRule(rule: WorkspacePermissionRule, moveToFront = false) {
    const existing = permissionRules.value.some((item) => item.id === rule.id)
    permissionRules.value = moveToFront
      ? [rule, ...permissionRules.value.filter((item) => item.id !== rule.id)]
      : existing
        ? permissionRules.value.map((item) => (item.id === rule.id ? rule : item))
        : [rule, ...permissionRules.value]
  }

  function markFileIndexedInKnowledgeBase(fileId: string, kbId: string) {
    const nextFiles = snapshot.value.files.map((file) => {
      if (file.id !== fileId) {
        return file
      }
      const knowledgeBaseIds = file.knowledge_base_ids.includes(kbId)
        ? file.knowledge_base_ids
        : [...file.knowledge_base_ids, kbId]
      return {
        ...file,
        knowledge_base_ids: knowledgeBaseIds,
        parse_status: 'indexed' as const,
      }
    })
    snapshot.value = {
      ...snapshot.value,
      files: nextFiles,
      summary: {
        ...snapshot.value.summary,
        indexed_count: nextFiles.filter((file) => file.parse_status === 'indexed').length,
      },
    }
  }

  return {
    activeWorkflow,
    activeWorkflowExecution,
    activeWorkflowId,
    activeWorkflowValidation,
    activeKnowledgeBase,
    activeKnowledgeBaseId,
    activeKnowledgeDocuments,
    activeTeamDetail,
    activeBreadcrumbs,
    activeFolderId,
    annotationFileIdLoading,
    annotationSaving,
    apiState,
    addKnowledgeDocument: addKnowledgeDocumentAction,
    addingKnowledgeDocument,
    auditLogs,
    askKnowledgeQuestion,
    askingQuestion,
    copyFile,
    copyingFileId,
    createFileAnnotation,
    createFolder,
    createKnowledgeBase: createKnowledgeBaseAction,
    createPermissionRule,
    createWorkflow,
    creatingFolder,
    deletePermissionRule,
    deleteFolder,
    deleteFile,
    deleteFileAnnotation,
    deletingAnnotationId,
    deletingPermissionRuleId,
    deletingFolderId,
    deletingFileId,
    downloadFile,
    downloadingFileId,
    errorMessage,
    executeWorkflow,
    fileAnnotationsById,
    fileFilters,
    fileListLoading,
    fileVersionsById,
    files,
    folderOptions,
    folders,
    folderTreeLoading,
    indexedFiles,
    knowledgeBases,
    knowledgeDocumentsByKbId,
    knowledgeOperationLoading,
    loadKnowledgeBases,
    loadKnowledgeDocuments,
    loadFolders,
    loadFileAnnotations,
    loadFileVersions,
    loadNotifications,
    loadPermissionRules,
    loadRecycleBin,
    loadTeamDetail,
    loadTeamMessages,
    loadTeams,
    loadWorkspace,
    loading,
    markNotificationRead,
    markingNotificationId,
    narrative,
    notifications,
    notificationsLoading,
    permissionRuleSaving,
    permissionRules,
    permissionRulesLoading,
    recycleBinItems,
    recycleBinLoading,
    replyFileAnnotation,
    resetFileFilters,
    restoreDeletedFile,
    restoreFileVersion,
    restoringDeletedFileId,
    restoringVersionId,
    searchFiles,
    selectFolder,
    selectKnowledgeBase,
    selectWorkflow,
    sharingFileId,
    summary,
    teams,
    createTeam,
    inviteTeamMember,
    joinTeam,
    removeTeamMember,
    sendTeamMessage,
    teamOperationLoading,
    teamMessagesById,
    teamMessageSending,
    teamMessageTeamIdLoading,
    tools,
    updateTeamMemberRole,
    updateFile,
    createFileShareLink,
    updateFolder,
    updateWorkflow,
    updatingFileId,
    updatingFolderId,
    uploadLargeFile,
    uploadFile,
    uploadingFile,
    validateWorkflow,
    versionFileId,
    workflowOperationLoading,
    workflows,
    publishWorkflow,
  }
})

function extractWorkflowExecutionAnswer(execution: WorkspaceWorkflowExecution): string | null {
  const summary = execution.output.summary
  return typeof summary === 'string' ? summary : null
}

function workflowExecutionToAgentSteps(execution: WorkspaceWorkflowExecution): AgentStep[] {
  return execution.node_executions.map((node) => ({
    content: formatWorkflowNodeOutput(node.output),
    metadata: {
      input: node.input ?? {},
      node_id: node.node_id,
    },
    status: node.status,
    title: node.name,
    tool_name: node.tool_name === 'trigger' ? null : node.tool_name,
    type: node.tool_name === 'trigger' ? 'thought' : 'action',
  }))
}

function formatWorkflowNodeOutput(output: Record<string, unknown> | undefined): string {
  if (!output || Object.keys(output).length === 0) {
    return '节点已执行，等待下游节点消费结果。'
  }

  const summary = output.summary
  if (typeof summary === 'string') {
    return summary
  }

  const markdown = output.markdown
  if (typeof markdown === 'string') {
    return markdown
  }

  return JSON.stringify(output)
}

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

function cloneKnowledgeBases(knowledgeBases: WorkspaceKnowledgeBase[]): WorkspaceKnowledgeBase[] {
  return knowledgeBases.map((knowledgeBase) => ({ ...knowledgeBase }))
}

function cloneKnowledgeDocumentMap(
  documents: Record<string, WorkspaceKnowledgeDocument[]>,
): Record<string, WorkspaceKnowledgeDocument[]> {
  return Object.fromEntries(
    Object.entries(documents).map(([kbId, items]) => [
      kbId,
      items.map((item) => ({ ...item })),
    ]),
  )
}

function clonePermissionRules(rules: WorkspacePermissionRule[]): WorkspacePermissionRule[] {
  return rules.map((rule) => ({ ...rule }))
}

function cloneTeamMessageMap(messagesById: Record<string, WorkspaceTeamMessage[]>): Record<string, WorkspaceTeamMessage[]> {
  return Object.fromEntries(
    Object.entries(messagesById).map(([teamId, messages]) => [
      teamId,
      messages.map((message) => ({ ...message })),
    ]),
  )
}

function cloneRecycleBinItems(items: WorkspaceRecycleBinItem[]): WorkspaceRecycleBinItem[] {
  return items.map((item) => ({ ...item, file: { ...item.file } }))
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
