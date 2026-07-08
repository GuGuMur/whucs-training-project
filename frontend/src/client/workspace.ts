import { createAuthorizationHeader } from '@/auth/workspaceAccess'
import {
  copyFileApiV1FilesFileIdCopyPost,
  createFolderApiV1FoldersPost,
  createTeamApiV1TeamsPost,
  createTeamInviteApiV1TeamsTeamIdInvitesPost,
  deleteFileApiV1FilesFileIdDelete,
  deleteFolderApiV1FoldersFolderIdDelete,
  downloadFileApiV1FilesFileIdDownloadGet,
  filesApiV1FilesGet,
  fileVersionsApiV1FilesFileIdVersionsGet,
  foldersApiV1FoldersTreeGet,
  joinTeamApiV1TeamsTeamIdMembersPost,
  removeTeamMemberApiV1TeamsTeamIdMembersMemberIdDelete,
  restoreFileVersionApiV1FilesFileIdVersionsVersionIdRestorePost,
  teamDetailApiV1TeamsTeamIdGet,
  teamsApiV1TeamsGet,
  updateFileApiV1FilesFileIdPatch,
  updateFolderApiV1FoldersFolderIdPatch,
  updateTeamMemberApiV1TeamsTeamIdMembersMemberIdPatch,
  uploadFileApiV1FilesUploadPost,
  workspaceSnapshotApiV1WorkspaceSnapshotGet,
} from '@/client/generated'
import type {
  AgentStep as GeneratedAgentStep,
  AuditLogEntry,
  Citation,
  FileCopyRequest,
  DashboardSummary,
  FileItem,
  FileListResponse,
  FileUpdate,
  FileVersionItem,
  FileVersionListResponse,
  FolderItem,
  FolderTreeResponse,
  FolderUpdate,
  TeamDetail,
  TeamInvitePublic,
  TeamListResponse,
  TeamMemberPublic,
  TeamMemberUpdate,
  TeamSummary,
  ToolDefinition,
  WorkflowDefinition,
  WorkspaceSnapshot,
} from '@/client/generated'

export type AgentStep = GeneratedAgentStep & { status: NonNullable<GeneratedAgentStep['status']> }
export type WorkspaceFile = FileItem
export type WorkspaceFileVersion = FileVersionItem
export type WorkspaceFileVersionListResponse = FileVersionListResponse
export type WorkspaceFolder = FolderItem
export type WorkspaceFolderScope = WorkspaceFolder['scope']
export type WorkspaceFolderTreeResponse = FolderTreeResponse
export type WorkspaceTeamDetail = TeamDetail
export type WorkspaceTeamInvite = TeamInvitePublic
export type WorkspaceTeamMember = TeamMemberPublic
export type WorkspaceTeamRole = TeamMemberUpdate['role']

export interface WorkspaceFileFilters {
  fileType: string
  query: string
  tag: string
}
export interface WorkspaceFileUploadInput {
  file: File
  folderId: string
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
export interface WorkspaceTeamCreateInput {
  description?: string | null
  name: string
}
export interface WorkspaceTeamInviteInput {
  email: string
  role: WorkspaceTeamRole
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

export const demoWorkspaceFolders: FolderTreeResponse = {
  items: [
    {
      id: 'personal-root',
      name: '个人文件',
      parent_id: null,
      scope: 'personal',
      permission: '个人',
      children: [
        {
          id: 'folder-biology',
          name: '生物学实验',
          parent_id: 'personal-root',
          scope: 'personal',
          permission: '个人',
          children: [],
        },
        {
          id: 'folder-course',
          name: '软件工程课程',
          parent_id: 'personal-root',
          scope: 'personal',
          permission: '个人',
          children: [],
        },
      ],
    },
    {
      id: 'team-root',
      name: '团队文件',
      parent_id: null,
      scope: 'team',
      permission: '团队',
      children: [],
    },
  ],
}

export const demoWorkspaceSnapshot: WorkspaceSnapshot = {
  summary: {
    file_count: 3,
    indexed_count: 2,
    knowledge_base_count: 2,
    running_workflows: 0,
    unread_notifications: 4,
    tools_enabled: 4,
  },
  files: [
    {
      id: 'file-microscope',
      name: '显微镜实验报告.pdf',
      folder_id: 'folder-biology',
      type: 'pdf',
      size: 2430112,
      sha256: '8b73c9d2d4c02b4b4f0e1c7a8dbf1023f44e8d9e7a10f24b15a02d983ff42d91',
      parse_status: 'indexed',
      tags: ['实验', '显微镜'],
      updated_at: '2026-07-08T06:21:00+08:00',
      permission_scope: '个人',
      knowledge_base_ids: ['kb-biology'],
    },
    {
      id: 'file-requirements',
      name: '需求规格说明书.md',
      folder_id: 'folder-course',
      type: 'markdown',
      size: 96418,
      sha256: 'fb8bd33418f0d6a73f83341f1f3bbef710c66f6a73e4c4afece8e7dfcb71b884',
      parse_status: 'indexed',
      tags: ['课程', '需求'],
      updated_at: '2026-07-07T18:10:00+08:00',
      permission_scope: '团队',
      knowledge_base_ids: ['kb-course'],
    },
    {
      id: 'file-weekly',
      name: '小组周报.docx',
      folder_id: 'team-root',
      type: 'docx',
      size: 384200,
      sha256: 'd654611a21f65bbdcad7f0c96da59e267674b0d806f65220b46fbf35d94a826b',
      parse_status: 'parsing',
      tags: ['周报', '团队'],
      updated_at: '2026-07-08T07:43:00+08:00',
      permission_scope: '团队',
      knowledge_base_ids: [],
    },
  ],
  tools: [
    {
      id: 'tool-file-search',
      name: 'file_search',
      version: '1.0.0',
      category: '文件操作',
      description: '按文件名、标签和解析状态搜索用户可访问文件。',
      input_schema: { type: 'object', properties: { query: { type: 'string' } } },
      output_schema: { type: 'object', properties: { files: { type: 'array' } } },
      enabled: true,
    },
    {
      id: 'tool-knowledge-qa',
      name: 'knowledge_qa',
      version: '1.0.0',
      category: 'AI处理',
      description: '基于知识库检索片段生成带引用的回答。',
      input_schema: { type: 'object', properties: { question: { type: 'string' }, kb_id: { type: 'string' } } },
      output_schema: { type: 'object', properties: { answer: { type: 'string' }, citations: { type: 'array' } } },
      enabled: true,
    },
    {
      id: 'tool-report-generate',
      name: 'report_generate',
      version: '1.0.0',
      category: 'AI处理',
      description: '将检索结果和活动动态整理为 Markdown 报告。',
      input_schema: { type: 'object', properties: { file_ids: { type: 'array' } } },
      output_schema: { type: 'object', properties: { markdown: { type: 'string' } } },
      enabled: true,
    },
    {
      id: 'tool-image-ocr',
      name: 'image_ocr',
      version: '1.0.0',
      category: '文档解析',
      description: '提取图片或扫描件中的文字。',
      input_schema: { type: 'object', properties: { image_file_id: { type: 'string' } } },
      output_schema: { type: 'object', properties: { text: { type: 'string' } } },
      enabled: true,
    },
  ],
  workflows: [
    {
      id: 'new-file-auto-summary',
      name: '新文件自动摘要',
      description: '文件上传后自动解析、知识库问答并生成摘要。',
      trigger: 'file.uploaded',
      version: '1.0.0',
      node_count: 3,
      status: 'published',
    },
  ],
  teams: [
    {
      description: '实验报告与观察数据协作',
      id: 'team-biology',
      member_count: 6,
      name: '生物学实验',
      role: 'admin',
      root_folder_id: 'team-root',
      unread_count: 3,
    },
    {
      description: '需求文档、周报和课程资料',
      id: 'team-course',
      member_count: 5,
      name: '软件工程课程组',
      role: 'member',
      root_folder_id: 'team-root',
      unread_count: 1,
    },
  ],
  audit_logs: [
    {
      id: 'audit-1',
      actor: 'xiaoming',
      action: 'workflow.execute',
      resource_type: 'workflow',
      resource_name: 'new-file-auto-summary',
      created_at: '2026-07-08T08:10:00+08:00',
    },
    {
      id: 'audit-2',
      actor: 'system',
      action: 'tool.publish',
      resource_type: 'tool',
      resource_name: 'knowledge_qa',
      created_at: '2026-07-08T04:20:00+08:00',
    },
  ],
}

export const demoWorkspaceTeamDetail: WorkspaceTeamDetail = {
  description: '实验报告与观察数据协作',
  id: 'team-biology',
  invites: [],
  member_count: 3,
  members: [
    {
      display_name: '小明',
      email: 'xiaoming@example.com',
      id: 'team-biology-member-1',
      joined_at: '2026-07-08T08:00:00+08:00',
      role: 'owner',
      status: 'active',
      team_id: 'team-biology',
      user_id: 1,
      username: 'xiaoming',
    },
    {
      display_name: '小红',
      email: 'xiaohong@example.com',
      id: 'team-biology-member-2',
      joined_at: '2026-07-08T08:10:00+08:00',
      role: 'member',
      status: 'active',
      team_id: 'team-biology',
      user_id: 2,
      username: 'xiaohong',
    },
    {
      display_name: '访客',
      email: 'guest@example.com',
      id: 'team-biology-member-3',
      joined_at: '2026-07-08T08:20:00+08:00',
      role: 'guest',
      status: 'active',
      team_id: 'team-biology',
      user_id: 3,
      username: 'guest',
    },
  ],
  name: '生物学实验',
  role: 'admin',
  root_folder: {
    children: [],
    id: 'team-root',
    name: '团队文件',
    parent_id: null,
    permission: '读写',
    scope: 'team',
    team_id: 'team-biology',
  },
  unread_count: 3,
}

export const demoWorkspaceFileVersions: Record<string, WorkspaceFileVersion[]> = {
  'file-microscope': [
    {
      id: 'file-microscope-v1',
      file_id: 'file-microscope',
      version_no: 1,
      name: '显微镜实验报告.pdf',
      size: 2430112,
      sha256: '8b73c9d2d4c02b4b4f0e1c7a8dbf1023f44e8d9e7a10f24b15a02d983ff42d91',
      created_at: '2026-07-08T06:21:00+08:00',
      created_by: 'system',
      is_current: true,
    },
  ],
  'file-requirements': [
    {
      id: 'file-requirements-v1',
      file_id: 'file-requirements',
      version_no: 1,
      name: '需求规格说明书.md',
      size: 96418,
      sha256: 'fb8bd33418f0d6a73f83341f1f3bbef710c66f6a73e4c4afece8e7dfcb71b884',
      created_at: '2026-07-07T18:10:00+08:00',
      created_by: 'system',
      is_current: true,
    },
  ],
  'file-weekly': [
    {
      id: 'file-weekly-v1',
      file_id: 'file-weekly',
      version_no: 1,
      name: '小组周报.docx',
      size: 384200,
      sha256: 'd654611a21f65bbdcad7f0c96da59e267674b0d806f65220b46fbf35d94a826b',
      created_at: '2026-07-08T07:43:00+08:00',
      created_by: 'system',
      is_current: true,
    },
  ],
}

export const demoWorkspaceNarrative: WorkspaceNarrative = {
  answer:
    '显微镜相关实验步骤包括：准备载玻片与样本，低倍镜定位目标区域，切换高倍镜观察细胞结构，记录视野特征，并在实验报告中附上观察结论。',
  citations: [
    {
      file_id: 'file-microscope',
      document_id: 'doc-microscope',
      chunk_id: 'chunk-micro-003',
      title: '显微镜实验报告.pdf',
      page_no: 3,
      paragraph_no: 5,
      snippet: '显微镜实验包含取样、制片、低倍镜定位、高倍镜观察和结果记录。',
    },
  ],
  agentSteps: [
    { type: 'thought', title: '任务理解', content: '需要先定位相关文件，再生成结构化报告。', status: 'success' },
    {
      type: 'action',
      title: '搜索文件',
      content: '按生物实验和显微镜关键词检索文件。',
      tool_name: 'file_search',
      status: 'success',
    },
    { type: 'observation', title: '文件结果', content: '找到 显微镜实验报告.pdf，已入库。', status: 'success' },
    {
      type: 'action',
      title: '生成报告',
      content: '根据检索结果生成团队周报草稿。',
      tool_name: 'report_generate',
      status: 'success',
    },
    { type: 'answer', title: '最终结果', content: '报告草稿已生成，包含实验目的、步骤、观察结果和待确认事项。', status: 'success' },
  ],
}

export async function fetchWorkspaceSnapshot(token: string): Promise<WorkspaceSnapshot> {
  const response = await workspaceSnapshotApiV1WorkspaceSnapshotGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceTeams(token: string): Promise<TeamListResponse> {
  const response = await teamsApiV1TeamsGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function createWorkspaceTeam(
  token: string,
  payload: WorkspaceTeamCreateInput,
): Promise<WorkspaceTeamDetail> {
  const response = await createTeamApiV1TeamsPost({
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
  const response = await teamDetailApiV1TeamsTeamIdGet({
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
  const response = await createTeamInviteApiV1TeamsTeamIdInvitesPost({
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
  const response = await joinTeamApiV1TeamsTeamIdMembersPost({
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
  const response = await updateTeamMemberApiV1TeamsTeamIdMembersMemberIdPatch({
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
  const response = await removeTeamMemberApiV1TeamsTeamIdMembersMemberIdDelete({
    headers: createAuthorizationHeader(token),
    path: { member_id: memberId, team_id: teamId },
  })

  if (response.error) {
    throw response.error
  }
}

export async function listWorkspaceFolders(token: string): Promise<FolderTreeResponse> {
  const response = await foldersApiV1FoldersTreeGet({
    headers: createAuthorizationHeader(token),
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function listWorkspaceFiles(token: string, filters: WorkspaceFileFilters): Promise<FileListResponse> {
  const response = await filesApiV1FilesGet({
    headers: createAuthorizationHeader(token),
    query: {
      file_type: filters.fileType || null,
      query: filters.query || null,
      tag: filters.tag || null,
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
  const response = await createFolderApiV1FoldersPost({
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

  const response = await updateFolderApiV1FoldersFolderIdPatch({
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
  const response = await deleteFolderApiV1FoldersFolderIdDelete({
    headers: createAuthorizationHeader(token),
    path: { folder_id: folderId },
  })

  if (response.error) {
    throw response.error
  }
}

export async function uploadWorkspaceFile(token: string, payload: WorkspaceFileUploadInput): Promise<WorkspaceFile> {
  const response = await uploadFileApiV1FilesUploadPost({
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

  const response = await updateFileApiV1FilesFileIdPatch({
    body,
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
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

  const response = await copyFileApiV1FilesFileIdCopyPost({
    body,
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function downloadWorkspaceFile(token: string, fileId: string): Promise<Blob> {
  const response = await downloadFileApiV1FilesFileIdDownloadGet({
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
  const response = await fileVersionsApiV1FilesFileIdVersionsGet({
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
  const response = await restoreFileVersionApiV1FilesFileIdVersionsVersionIdRestorePost({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId, version_id: versionId },
  })

  if (response.error) {
    throw response.error
  }

  return response.data
}

export async function deleteWorkspaceFile(token: string, fileId: string): Promise<void> {
  const response = await deleteFileApiV1FilesFileIdDelete({
    headers: createAuthorizationHeader(token),
    path: { file_id: fileId },
  })

  if (response.error) {
    throw response.error
  }
}
