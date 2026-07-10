import { createAuthorizationHeader } from '@/auth/workspaceAccess'
import {
  addKnowledgeDocumentApiV2KnowledgeBasesKbIdDocumentsPost,
  completeMultipartUploadApiV2FilesMultipartUploadsSessionIdCompletePost,
  copyFileApiV2FilesFileIdCopyPost,
  createFileAnnotationApiV2FilesFileIdAnnotationsPost,
  createFileShareLinkApiV2FilesFileIdShareLinksPost,
  createFolderApiV2FoldersPost,
  createKnowledgeBaseApiV2KnowledgeBasesPost,
  createPermissionRuleApiV2PermissionsRulesPost,
  createTeamApiV2TeamsPost,
  createTeamInviteApiV2TeamsTeamIdInvitesPost,
  createTeamMessageApiV2TeamsTeamIdMessagesPost,
  createWorkflowApiV2WorkflowsPost,
  deleteFileAnnotationApiV2FilesFileIdAnnotationsAnnotationIdDelete,
  deleteFileApiV2FilesFileIdDelete,
  deleteFolderApiV2FoldersFolderIdDelete,
  deletePermissionRuleApiV2PermissionsRulesRuleIdDelete,
  downloadFileApiV2FilesFileIdDownloadGet,
  executeWorkflowApiV2WorkflowsWorkflowIdExecutionsPost,
  fileAnnotationsApiV2FilesFileIdAnnotationsGet,
  listFilesApiV2FilesGet,
  fileVersionsApiV2FilesFileIdVersionsGet,
  folderTreeApiV2FoldersTreeGet,
  joinTeamApiV2TeamsTeamIdMembersPost,
  listKnowledgeBasesApiV2KnowledgeBasesGet,
  knowledgeDocumentsApiV2KnowledgeBasesKbIdDocumentsGet,
  markNotificationReadApiV2NotificationsNotificationIdReadPatch,
  multipartUploadStatusApiV2FilesMultipartUploadsSessionIdGet,
  notificationsApiV2NotificationsGet,
  permissionRulesApiV2PermissionsRulesGet,
  publishWorkflowApiV2WorkflowsWorkflowIdPublishPost,
  removeTeamMemberApiV2TeamsTeamIdMembersMemberIdDelete,
  replyFileAnnotationApiV2AnnotationsAnnotationIdRepliesPost,
  restoreFileVersionApiV2FilesFileIdVersionsVersionIdRestorePost,
  teamDetailApiV2TeamsTeamIdGet,
  teamMessagesApiV2TeamsTeamIdMessagesGet,
  listTeamsApiV2TeamsGet,
  updateFileApiV2FilesFileIdPatch,
  updateFolderApiV2FoldersFolderIdPatch,
  updateKnowledgeBaseApiV2KnowledgeBasesKbIdPatch,
  updateTeamMemberApiV2TeamsTeamIdMembersMemberIdPatch,
  updateWorkflowApiV2WorkflowsWorkflowIdPatch,
  initMultipartUploadApiV2FilesMultipartUploadsPost,
  uploadFileApiV2FilesUploadPost,
  uploadMultipartChunkApiV2FilesMultipartUploadsSessionIdChunksChunkIndexPut,
  qaQueryApiV2QaQueryPost,
  recycleBinApiV2FilesRecycleBinGet,
  validateWorkflowApiV2WorkflowsWorkflowIdValidatePost,
  restoreDeletedFileApiV2FilesFileIdRestorePost,
  listWorkflowsApiV2WorkflowsGet,
  workspaceSnapshotApiV2WorkspaceSnapshotGet,
} from '@/client/generated'
import type {
  AgentStep as GeneratedAgentStep,
  AuditLogEntry,
  Citation,
  FileCopyRequest,
  FileAnnotationCreate,
  FileAnnotationItem,
  FileAnnotationListResponse,
  FileAnnotationReplyCreate,
  FileAnnotationReplyItem,
  DashboardSummary,
  FileItem,
  FileListResponse,
  FileUpdate,
  FileVersionItem,
  FileVersionListResponse,
  FolderItem,
  FolderTreeResponse,
  FolderUpdate,
  KnowledgeBaseListResponse,
  KnowledgeBasePublic,
  KnowledgeBaseUpdate,
  KnowledgeDocumentListResponse,
  KnowledgeDocumentPublic,
  MultipartChunkResponse,
  MultipartUploadSession,
  NotificationItem,
  NotificationListResponse,
  PermissionRuleCreate,
  PermissionRuleListResponse,
  PermissionRulePublic,
  QaResponse,
  RecycleBinItem,
  RecycleBinResponse,
  ShareLinkPublic,
  TeamDetail,
  TeamInvitePublic,
  TeamListResponse,
  TeamMemberPublic,
  TeamMemberUpdate,
  TeamMessageCreate,
  TeamMessageItem,
  TeamMessageListResponse,
  TeamSummary,
  ToolDefinition,
  WorkflowCreate,
  WorkflowDefinition,
  WorkflowEdgeDefinition,
  WorkflowExecutionResponse,
  WorkflowListResponse,
  WorkflowNodeDefinition,
  WorkflowUpdate,
  WorkflowValidationResponse,
  WorkspaceSnapshot,
} from '@/client/generated'

export type AgentStep = GeneratedAgentStep & { status: NonNullable<GeneratedAgentStep['status']> }
export type WorkspaceFile = FileItem
export type WorkspaceFileAnnotation = FileAnnotationItem
export type WorkspaceFileAnnotationReply = FileAnnotationReplyItem
export type WorkspaceFileAnnotationListResponse = FileAnnotationListResponse
export type WorkspaceFileVersion = FileVersionItem
export type WorkspaceFileVersionListResponse = FileVersionListResponse
export type WorkspaceShareLink = ShareLinkPublic
export type WorkspaceRecycleBinItem = RecycleBinItem
export type WorkspaceRecycleBinResponse = RecycleBinResponse
export type WorkspaceMultipartUploadSession = MultipartUploadSession
export type WorkspaceMultipartChunkResponse = MultipartChunkResponse
export type WorkspaceNotification = NotificationItem
export type WorkspaceNotificationListResponse = NotificationListResponse
export type WorkspaceFolder = FolderItem
export type WorkspaceFolderScope = WorkspaceFolder['scope']
export type WorkspaceFolderTreeResponse = FolderTreeResponse
export type WorkspaceKnowledgeBase = KnowledgeBasePublic
export type WorkspaceKnowledgeDocument = KnowledgeDocumentPublic
export type WorkspaceKnowledgeBaseListResponse = KnowledgeBaseListResponse
export type WorkspaceKnowledgeDocumentListResponse = KnowledgeDocumentListResponse
export type WorkspacePermissionRule = PermissionRulePublic
export type WorkspacePermissionRuleListResponse = PermissionRuleListResponse
export type WorkspaceQuestionResponse = QaResponse
export type WorkspaceTeamDetail = TeamDetail
export type WorkspaceTeamInvite = TeamInvitePublic
export type WorkspaceTeamMember = TeamMemberPublic
export type WorkspaceTeamRole = TeamMemberUpdate['role']
export type WorkspaceTeamMessage = TeamMessageItem
export type WorkspaceTeamMessageListResponse = TeamMessageListResponse
export type WorkspaceWorkflow = WorkflowDefinition
export type WorkspaceWorkflowNode = WorkflowNodeDefinition
export type WorkspaceWorkflowEdge = WorkflowEdgeDefinition
export type WorkspaceWorkflowValidation = WorkflowValidationResponse
export type WorkspaceWorkflowExecution = WorkflowExecutionResponse

export interface WorkspaceFileFilters {
  fileType: string
  query: string
  tag: string
  updatedFrom: string
  updatedTo: string
}
export interface WorkspaceFileUploadInput {
  file: File
  folderId: string
  tags: string[]
}
export interface WorkspaceMultipartUploadInput extends WorkspaceFileUploadInput {
  chunkSize?: number
}
export interface WorkspaceMultipartUploadInitInput {
  chunkSize: number
  filename: string
  folderId: string
  sha256: string
  size: number
  tags: string[]
}
export interface WorkspaceFileUpdateInput {
  folderId?: string | null
  name?: string | null
  tags?: string[] | null
}
export interface WorkspaceFileCopyInput {
  name?: string | null
  tags?: string[] | null
  targetFolderId: string
}
export interface WorkspaceShareLinkCreateInput {
  downloadLimit?: number | null
  expiresInSeconds?: number
  password?: string | null
}
export interface WorkspaceFileAnnotationCreateInput {
  content: string
  position?: FileAnnotationCreate['position']
}
export interface WorkspaceFileAnnotationReplyInput {
  content: string
}
export interface WorkspaceFolderCreateInput {
  name: string
  parentId?: string | null
  scope?: WorkspaceFolderScope
}
export interface WorkspaceFolderUpdateInput {
  name?: string | null
  parentId?: string | null
}
export interface WorkspaceFolderOption {
  label: string
  value: string
}
export interface WorkspaceKnowledgeBaseCreateInput {
  description?: string | null
  name: string
}
export interface WorkspaceKnowledgeBaseUpdateInput {
  description?: string | null
  name?: string | null
  status?: NonNullable<KnowledgeBaseUpdate['status']>
}
export interface WorkspaceQuestionInput {
  conversationId?: string | null
  kbId: string
  question: string
  topK?: number
}
export interface WorkspaceTeamCreateInput {
  description?: string | null
  name: string
}
export interface WorkspaceTeamInviteInput {
  email: string
  role: WorkspaceTeamRole
}
export interface WorkspaceTeamMessageCreateInput {
  content: string
  message_type?: TeamMessageCreate['message_type']
  receiver_id?: number | null
}
export interface WorkspacePermissionRuleCreateInput {
  action: PermissionRuleCreate['action']
  effect: PermissionRuleCreate['effect']
  inherit?: boolean
  resourceId: string
  resourceType: PermissionRuleCreate['resource_type']
  subjectId: string
  subjectType: PermissionRuleCreate['subject_type']
}
export interface WorkspaceWorkflowCreateInput {
  description?: string | null
  edges?: WorkspaceWorkflowEdge[]
  name: string
  nodes?: WorkspaceWorkflowNode[]
  trigger?: string
}
export interface WorkspaceWorkflowUpdateInput {
  description?: string | null
  edges?: WorkspaceWorkflowEdge[] | null
  name?: string | null
  nodes?: WorkspaceWorkflowNode[] | null
  trigger?: string | null
}
export interface WorkspaceWorkflowExecuteInput {
  fileId: string
  targetKbId?: string | null
}
export type {
  AuditLogEntry,
  Citation,
  DashboardSummary,
  FileListResponse,
  TeamSummary,
  ToolDefinition,
  WorkflowDefinition,
  WorkspaceSnapshot,
}

export interface WorkspaceNarrative {
  answer: string
  citations: Citation[]
  agentSteps: AgentStep[]
}


export async function fetchWorkspaceSnapshot(token: string): Promise<WorkspaceSnapshot> {
  const response = await workspaceSnapshotApiV2WorkspaceSnapshotGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceWorkflows(token: string): Promise<WorkflowListResponse> {
  const response = await listWorkflowsApiV2WorkflowsGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspaceWorkflow(
  token: string,
  payload: WorkspaceWorkflowCreateInput,
): Promise<WorkspaceWorkflow> {
  const body: WorkflowCreate = {
    description: payload.description ?? null,
    edges: payload.edges ?? [],
    name: payload.name,
    nodes: payload.nodes ?? [],
    trigger: payload.trigger ?? 'manual',
  }
  const response = await createWorkflowApiV2WorkflowsPost({
    body,
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function updateWorkspaceWorkflow(
  token: string,
  workflowId: string,
  payload: WorkspaceWorkflowUpdateInput,
): Promise<WorkspaceWorkflow> {
  const body: WorkflowUpdate = {}
  if ('description' in payload) {
    body.description = payload.description ?? null
  }
  if ('edges' in payload) {
    body.edges = payload.edges ?? null
  }
  if ('name' in payload) {
    body.name = payload.name ?? null
  }
  if ('nodes' in payload) {
    body.nodes = payload.nodes ?? null
  }
  if ('trigger' in payload) {
    body.trigger = payload.trigger ?? null
  }

  const response = await updateWorkflowApiV2WorkflowsWorkflowIdPatch({
    body,
    headers: createAuthorizationHeader(token),
    path: { workflow_id: workflowId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function validateWorkspaceWorkflow(
  token: string,
  workflowId: string,
): Promise<WorkspaceWorkflowValidation> {
  const response = await validateWorkflowApiV2WorkflowsWorkflowIdValidatePost({
    headers: createAuthorizationHeader(token),
    path: { workflow_id: workflowId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function publishWorkspaceWorkflow(token: string, workflowId: string): Promise<WorkspaceWorkflow> {
  const response = await publishWorkflowApiV2WorkflowsWorkflowIdPublishPost({
    headers: createAuthorizationHeader(token),
    path: { workflow_id: workflowId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function executeWorkspaceWorkflow(
  token: string,
  workflowId: string,
  payload: WorkspaceWorkflowExecuteInput,
): Promise<WorkspaceWorkflowExecution> {
  const response = await executeWorkflowApiV2WorkflowsWorkflowIdExecutionsPost({
    body: {
      file_id: payload.fileId,
      target_kb_id: payload.targetKbId ?? null,
    },
    headers: createAuthorizationHeader(token),
    path: { workflow_id: workflowId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listKnowledgeBases(token: string): Promise<WorkspaceKnowledgeBaseListResponse> {
  const response = await listKnowledgeBasesApiV2KnowledgeBasesGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createKnowledgeBase(
  token: string,
  payload: WorkspaceKnowledgeBaseCreateInput,
): Promise<WorkspaceKnowledgeBase> {
  const response = await createKnowledgeBaseApiV2KnowledgeBasesPost({
    body: {
      description: payload.description ?? null,
      name: payload.name,
    },
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function updateKnowledgeBase(
  token: string,
  kbId: string,
  payload: WorkspaceKnowledgeBaseUpdateInput,
): Promise<WorkspaceKnowledgeBase> {
  const body: KnowledgeBaseUpdate = {}
  if ('description' in payload) {
    body.description = payload.description ?? null
  }
  if ('name' in payload) {
    body.name = payload.name ?? null
  }
  if ('status' in payload) {
    body.status = payload.status ?? null
  }

  const response = await updateKnowledgeBaseApiV2KnowledgeBasesKbIdPatch({
    body,
    headers: createAuthorizationHeader(token),
    path: { kb_id: kbId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listKnowledgeDocuments(
  token: string,
  kbId: string,
): Promise<WorkspaceKnowledgeDocumentListResponse> {
  const response = await knowledgeDocumentsApiV2KnowledgeBasesKbIdDocumentsGet({
    headers: createAuthorizationHeader(token),
    path: { kb_id: kbId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function addKnowledgeDocument(
  token: string,
  kbId: string,
  fileId: string,
): Promise<WorkspaceKnowledgeDocument> {
  const response = await addKnowledgeDocumentApiV2KnowledgeBasesKbIdDocumentsPost({
    body: { file_id: fileId },
    headers: createAuthorizationHeader(token),
    path: { kb_id: kbId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function askWorkspaceQuestion(
  token: string,
  payload: WorkspaceQuestionInput,
): Promise<WorkspaceQuestionResponse> {
  const response = await qaQueryApiV2QaQueryPost({
    body: {
      conversation_id: payload.conversationId ?? null,
      kb_id: payload.kbId,
      question: payload.question,
      stream: false,
      top_k: payload.topK ?? 5,
    },
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceTeams(token: string): Promise<TeamListResponse> {
  const response = await listTeamsApiV2TeamsGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspacePermissionRules(token: string): Promise<WorkspacePermissionRuleListResponse> {
  const response = await permissionRulesApiV2PermissionsRulesGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspacePermissionRule(
  token: string,
  payload: WorkspacePermissionRuleCreateInput,
): Promise<WorkspacePermissionRule> {
  const body: PermissionRuleCreate = {
    action: payload.action,
    effect: payload.effect,
    inherit: payload.inherit ?? false,
    resource_id: payload.resourceId,
    resource_type: payload.resourceType,
    subject_id: payload.subjectId,
    subject_type: payload.subjectType,
  }
  const response = await createPermissionRuleApiV2PermissionsRulesPost({
    body,
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function deleteWorkspacePermissionRule(token: string, ruleId: string): Promise<void> {
  const response = await deletePermissionRuleApiV2PermissionsRulesRuleIdDelete({
    headers: createAuthorizationHeader(token),
    path: { rule_id: ruleId },
  })

  if (response.error) {
    throw response.error
  }
}

export async function createWorkspaceTeam(
  token: string,
  payload: WorkspaceTeamCreateInput,
): Promise<WorkspaceTeamDetail> {
  const response = await createTeamApiV2TeamsPost({
    body: {
      description: payload.description ?? null,
      name: payload.name,
    },
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function loadWorkspaceTeamDetail(token: string, teamId: string): Promise<WorkspaceTeamDetail> {
  const response = await teamDetailApiV2TeamsTeamIdGet({
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceTeamMessages(
  token: string,
  teamId: string,
): Promise<WorkspaceTeamMessageListResponse> {
  const response = await teamMessagesApiV2TeamsTeamIdMessagesGet({
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function sendWorkspaceTeamMessage(
  token: string,
  teamId: string,
  payload: WorkspaceTeamMessageCreateInput,
): Promise<WorkspaceTeamMessage> {
  const response = await createTeamMessageApiV2TeamsTeamIdMessagesPost({
    body: {
      content: payload.content,
      message_type: payload.message_type ?? 'text',
      receiver_id: payload.receiver_id ?? null,
    },
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspaceTeamInvite(
  token: string,
  teamId: string,
  payload: WorkspaceTeamInviteInput,
): Promise<WorkspaceTeamInvite> {
  const response = await createTeamInviteApiV2TeamsTeamIdInvitesPost({
    body: {
      email: payload.email,
      role: payload.role,
    },
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function joinWorkspaceTeam(
  token: string,
  teamId: string,
  inviteToken: string,
): Promise<WorkspaceTeamMember> {
  const response = await joinTeamApiV2TeamsTeamIdMembersPost({
    body: { invite_token: inviteToken },
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function updateWorkspaceTeamMember(
  token: string,
  teamId: string,
  memberId: string,
  role: WorkspaceTeamRole,
): Promise<WorkspaceTeamMember> {
  const response = await updateTeamMemberApiV2TeamsTeamIdMembersMemberIdPatch({
    body: { role },
    headers: createAuthorizationHeader(token),
    path: { member_id: memberId, team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function removeWorkspaceTeamMember(token: string, teamId: string, memberId: string): Promise<void> {
  const response = await removeTeamMemberApiV2TeamsTeamIdMembersMemberIdDelete({
    headers: createAuthorizationHeader(token),
    path: { member_id: memberId, team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }
}

export async function listWorkspaceFolders(token: string): Promise<FolderTreeResponse> {
  const response = await folderTreeApiV2FoldersTreeGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceFiles(token: string, filters: WorkspaceFileFilters): Promise<FileListResponse> {
  const response = await listFilesApiV2FilesGet({
    headers: createAuthorizationHeader(token),
    query: {
      file_type: filters.fileType || null,
      query: filters.query || null,
      tag: filters.tag || null,
      updated_from: filters.updatedFrom || null,
      updated_to: filters.updatedTo || null,
    },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspaceFolder(
  token: string,
  payload: WorkspaceFolderCreateInput,
): Promise<WorkspaceFolder> {
  const response = await createFolderApiV2FoldersPost({
    body: {
      name: payload.name,
      parent_id: payload.parentId ?? null,
      scope: payload.scope ?? 'personal',
    },
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function updateWorkspaceFolder(
  token: string,
  folderId: string,
  payload: WorkspaceFolderUpdateInput,
): Promise<WorkspaceFolder> {
  const body: FolderUpdate = {}
  if ('name' in payload) {
    body.name = payload.name ?? null
  }
  if ('parentId' in payload) {
    body.parent_id = payload.parentId ?? null
  }

  const response = await updateFolderApiV2FoldersFolderIdPatch({
    body,
    headers: createAuthorizationHeader(token),
    path: { folder_id: folderId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function deleteWorkspaceFolder(token: string, folderId: string): Promise<void> {
  const response = await deleteFolderApiV2FoldersFolderIdDelete({
    headers: createAuthorizationHeader(token),
    path: { folder_id: folderId },
  })

  if (response.error) {
    throw response.error
  }
}

export async function uploadWorkspaceFile(token: string, payload: WorkspaceFileUploadInput): Promise<WorkspaceFile> {
  const response = await uploadFileApiV2FilesUploadPost({
    body: {
      file: payload.file,
      folder_id: payload.folderId,
      tags: payload.tags.join(',') || null,
    },
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function initWorkspaceMultipartUpload(
  token: string,
  payload: WorkspaceMultipartUploadInitInput,
): Promise<WorkspaceMultipartUploadSession> {
  const response = await initMultipartUploadApiV2FilesMultipartUploadsPost({
    body: {
      chunk_size: payload.chunkSize,
      filename: payload.filename,
      folder_id: payload.folderId,
      sha256: payload.sha256,
      size: payload.size,
      tags: payload.tags,
    },
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function uploadWorkspaceMultipartChunk(
  token: string,
  sessionId: string,
  chunkIndex: number,
  chunk: Blob,
): Promise<WorkspaceMultipartChunkResponse> {
  const response = await uploadMultipartChunkApiV2FilesMultipartUploadsSessionIdChunksChunkIndexPut({
    body: {
      chunk,
      sha256: await sha256Blob(chunk),
    },
    headers: createAuthorizationHeader(token),
    path: { chunk_index: chunkIndex, session_id: sessionId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function getWorkspaceMultipartUpload(
  token: string,
  sessionId: string,
): Promise<WorkspaceMultipartUploadSession> {
  const response = await multipartUploadStatusApiV2FilesMultipartUploadsSessionIdGet({
    headers: createAuthorizationHeader(token),
    path: { session_id: sessionId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function completeWorkspaceMultipartUpload(token: string, sessionId: string): Promise<WorkspaceFile> {
  const response = await completeMultipartUploadApiV2FilesMultipartUploadsSessionIdCompletePost({
    headers: createAuthorizationHeader(token),
    path: { session_id: sessionId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function uploadWorkspaceMultipartFile(
  token: string,
  payload: WorkspaceMultipartUploadInput,
): Promise<WorkspaceFile> {
  const chunkSize = payload.chunkSize ?? 5 * 1024 * 1024
  const session = await initWorkspaceMultipartUpload(token, {
    chunkSize,
    filename: payload.file.name,
    folderId: payload.folderId,
    sha256: await sha256Blob(payload.file),
    size: payload.file.size,
    tags: payload.tags,
  })

  for (let offset = 0, chunkIndex = 0; offset < payload.file.size; offset += chunkSize, chunkIndex += 1) {
    const chunk = payload.file.slice(offset, Math.min(offset + chunkSize, payload.file.size))
    await uploadWorkspaceMultipartChunk(token, session.id, chunkIndex, chunk)
  }

  return completeWorkspaceMultipartUpload(token, session.id)
}

export async function updateWorkspaceFile(
  token: string,
  fileId: string,
  payload: WorkspaceFileUpdateInput,
): Promise<WorkspaceFile> {
  const body: FileUpdate = {}
  if ('name' in payload) {
    body.name = payload.name ?? null
  }
  if ('folderId' in payload) {
    body.folder_id = payload.folderId ?? null
  }
  if ('tags' in payload) {
    body.tags = payload.tags ?? null
  }

  const response = await updateFileApiV2FilesFileIdPatch({
    body,
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

async function sha256Blob(blob: Blob): Promise<string> {
  const digest = await crypto.subtle.digest('SHA-256', await blob.arrayBuffer())
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, '0'))
    .join('')
}

export async function copyWorkspaceFile(
  token: string,
  fileId: string,
  payload: WorkspaceFileCopyInput,
): Promise<WorkspaceFile> {
  const body: FileCopyRequest = {
    target_folder_id: payload.targetFolderId,
  }
  if ('name' in payload) {
    body.name = payload.name ?? null
  }
  if ('tags' in payload) {
    body.tags = payload.tags ?? null
  }

  const response = await copyFileApiV2FilesFileIdCopyPost({
    body,
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspaceFileShareLink(
  token: string,
  fileId: string,
  payload: WorkspaceShareLinkCreateInput,
): Promise<WorkspaceShareLink> {
  const response = await createFileShareLinkApiV2FilesFileIdShareLinksPost({
    body: {
      download_limit: payload.downloadLimit ?? null,
      expires_in_seconds: payload.expiresInSeconds ?? 3600,
      password: payload.password ?? null,
    },
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceFileAnnotations(
  token: string,
  fileId: string,
): Promise<WorkspaceFileAnnotationListResponse> {
  const response = await fileAnnotationsApiV2FilesFileIdAnnotationsGet({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspaceFileAnnotation(
  token: string,
  fileId: string,
  payload: WorkspaceFileAnnotationCreateInput,
): Promise<WorkspaceFileAnnotation> {
  const response = await createFileAnnotationApiV2FilesFileIdAnnotationsPost({
    body: {
      content: payload.content,
      position: payload.position ?? null,
    },
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function replyWorkspaceFileAnnotation(
  token: string,
  annotationId: string,
  payload: WorkspaceFileAnnotationReplyInput,
): Promise<WorkspaceFileAnnotationReply> {
  const response = await replyFileAnnotationApiV2AnnotationsAnnotationIdRepliesPost({
    body: {
      content: payload.content,
    },
    headers: createAuthorizationHeader(token),
    path: { annotation_id: annotationId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function deleteWorkspaceFileAnnotation(
  token: string,
  fileId: string,
  annotationId: string,
): Promise<void> {
  const response = await deleteFileAnnotationApiV2FilesFileIdAnnotationsAnnotationIdDelete({
    headers: createAuthorizationHeader(token),
    path: { annotation_id: annotationId, file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }
}

export async function listWorkspaceNotifications(token: string): Promise<WorkspaceNotificationListResponse> {
  const response = await notificationsApiV2NotificationsGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function markWorkspaceNotificationRead(
  token: string,
  notificationId: string,
): Promise<WorkspaceNotification> {
  const response = await markNotificationReadApiV2NotificationsNotificationIdReadPatch({
    headers: createAuthorizationHeader(token),
    path: { notification_id: notificationId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function downloadWorkspaceFile(token: string, fileId: string): Promise<Blob> {
  const response = await downloadFileApiV2FilesFileIdDownloadGet({
    headers: createAuthorizationHeader(token),
    parseAs: 'blob',
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  if (response.data instanceof Blob) {
    return response.data
  }

  throw new Error('文件下载响应格式不正确')
}

export async function listWorkspaceFileVersions(
  token: string,
  fileId: string,
): Promise<WorkspaceFileVersionListResponse> {
  const response = await fileVersionsApiV2FilesFileIdVersionsGet({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function restoreWorkspaceFileVersion(
  token: string,
  fileId: string,
  versionId: string,
): Promise<WorkspaceFile> {
  const response = await restoreFileVersionApiV2FilesFileIdVersionsVersionIdRestorePost({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId, version_id: versionId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceRecycleBin(token: string): Promise<WorkspaceRecycleBinResponse> {
  const response = await recycleBinApiV2FilesRecycleBinGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function restoreWorkspaceDeletedFile(token: string, fileId: string): Promise<WorkspaceFile> {
  const response = await restoreDeletedFileApiV2FilesFileIdRestorePost({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function deleteWorkspaceFile(token: string, fileId: string): Promise<void> {
  const response = await deleteFileApiV2FilesFileIdDelete({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }
}

// ── Team management (V2) ──
import {
  deleteTeamApiV2TeamsTeamIdDelete,
  updateTeamApiV2TeamsTeamIdPatch,
  leaveTeamApiV2TeamsTeamIdMembersMeDelete,
} from '@/client/generated'

export async function deleteWorkspaceTeam(token: string, teamId: string): Promise<void> {
  const response = await deleteTeamApiV2TeamsTeamIdDelete({
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })
  if (response.error) throw response.error
}

export async function updateWorkspaceTeam(
  token: string,
  teamId: string,
  payload: { name?: string | null; description?: string | null },
): Promise<any> {
  const response = await updateTeamApiV2TeamsTeamIdPatch({
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
    body: payload as any,
  })
  if (response.error) throw response.error
  return response.data
}

export async function leaveWorkspaceTeam(token: string, teamId: string): Promise<void> {
  const response = await leaveTeamApiV2TeamsTeamIdMembersMeDelete({
    headers: createAuthorizationHeader(token),
    path: { team_id: teamId },
  })
  if (response.error) throw response.error
}

export function buildTeamInviteUrl(teamId: string, token: string): string {
  return `${window.location.origin}/team-chat?join=${teamId}&token=${encodeURIComponent(token)}`
}
